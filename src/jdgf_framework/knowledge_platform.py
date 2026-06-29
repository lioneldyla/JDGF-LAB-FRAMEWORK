"""Knowledge Platform schema and cross-artifact validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

ARTIFACT_KEYS = {
    "config": "knowledge/knowledge.yaml",
    "ontology": "knowledge/ontology.yaml",
    "metadata_schema": "knowledge/metadata.schema.yaml",
    "indexing": "knowledge/indexing.yaml",
    "collections": "knowledge/collections.yaml",
    "vector_profiles": "knowledge/vector_profiles.yaml",
    "graph_schema": "knowledge/graph_schema.yaml",
    "ingestion_pipeline": "knowledge/pipelines/document-ingestion.yaml",
    "rag_pipeline": "knowledge/pipelines/rag.yaml",
}


@dataclass(frozen=True)
class KnowledgePlatformSummary:
    version: str
    lifecycle: str
    installable: bool
    collection_ids: tuple[str, ...]
    source_count: int


class KnowledgePlatformError(ValueError):
    """Raised when Knowledge Platform contracts are invalid or inconsistent."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise KnowledgePlatformError(f"Missing knowledge artifact: {path}") from exc
    except yaml.YAMLError as exc:
        raise KnowledgePlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise KnowledgePlatformError(f"Expected a YAML mapping in {path}")
    return document


def _checked_schema(path: Path) -> dict[str, Any]:
    schema = _load_mapping(path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise KnowledgePlatformError(
            f"Invalid schema in {path}: {exc.message}"
        ) from exc
    return schema


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _checked_schema(schema_path)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
            document
        ),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise KnowledgePlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def _resolve_repository_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise KnowledgePlatformError(
            f"Knowledge artifact escapes repository root: {relative}"
        ) from exc
    if not path.is_file():
        raise KnowledgePlatformError(f"Knowledge artifact does not exist: {relative}")
    return path


def validate_document_metadata(root: Path, path: Path) -> dict[str, Any]:
    """Validate one source metadata document against the public metadata schema."""

    root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise KnowledgePlatformError(
            "Metadata document escapes repository root"
        ) from exc
    document = _load_mapping(resolved)
    _validate(document, root / "knowledge" / "metadata.schema.yaml", resolved)
    return document


def validate_knowledge_platform(root: Path) -> KnowledgePlatformSummary:
    """Validate the Knowledge Platform foundation without activating runtimes."""

    root = root.resolve()
    manifest_path = root / "manifests" / "knowledge-platform.yaml"
    registry_path = root / "registry" / "knowledge.yaml"
    manifest = _load_mapping(manifest_path)
    registry = _load_mapping(registry_path)
    _validate(
        manifest,
        root / "manifests" / "knowledge-platform.schema.yaml",
        manifest_path,
    )
    _validate(
        registry,
        root / "registry" / "knowledge.schema.yaml",
        registry_path,
    )

    if registry["metadata"]["version"] != manifest["metadata"]["version"]:
        raise KnowledgePlatformError("Knowledge manifest and registry versions differ")
    expected_components = {
        "ontology",
        "metadata",
        "collections",
        "indexing",
        "ingestion",
        "rag",
        "graph",
        "vectors",
    }
    if set(manifest["spec"]["components"]) != expected_components:
        raise KnowledgePlatformError("Knowledge manifest component set is incomplete")

    if registry["artifacts"] != ARTIFACT_KEYS:
        raise KnowledgePlatformError("Knowledge registry artifact map is not canonical")
    paths = {
        key: _resolve_repository_path(root, relative)
        for key, relative in registry["artifacts"].items()
    }

    artifact_schema = root / "knowledge" / "artifacts.schema.yaml"
    artifacts = {
        key: _load_mapping(path)
        for key, path in paths.items()
        if key not in {"metadata_schema", "ingestion_pipeline", "rag_pipeline"}
    }
    for key, document in artifacts.items():
        _validate(document, artifact_schema, paths[key])
    _checked_schema(paths["metadata_schema"])

    pipeline_schema = root / "knowledge" / "pipelines" / "pipeline.schema.yaml"
    ingestion = _load_mapping(paths["ingestion_pipeline"])
    rag = _load_mapping(paths["rag_pipeline"])
    _validate(ingestion, pipeline_schema, paths["ingestion_pipeline"])
    _validate(rag, pipeline_schema, paths["rag_pipeline"])

    registry_collections = [entry["id"] for entry in registry["collections"]]
    catalog_collections = [
        entry["id"] for entry in artifacts["collections"]["collections"]
    ]
    if len(registry_collections) != len(set(registry_collections)):
        raise KnowledgePlatformError("Duplicate knowledge collection id")
    if registry_collections != catalog_collections:
        raise KnowledgePlatformError(
            "Knowledge registry collections do not match the collection catalog"
        )
    for collection in registry["collections"]:
        if collection["lifecycle"] != "active" and collection["enabled"]:
            raise KnowledgePlatformError(
                f"Non-active knowledge collection cannot be enabled: {collection['id']}"
            )

    config = artifacts["config"]
    for provider in config["spec"]["providers"]:
        if provider["lifecycle"] != "active" and provider["enabled"]:
            raise KnowledgePlatformError(
                f"Non-active knowledge provider cannot be enabled: {provider['id']}"
            )

    ontology_types = {entry["id"] for entry in artifacts["ontology"]["types"]}
    ontology_relations = {
        entry["id"] for entry in artifacts["ontology"]["relationships"]
    }
    graph = artifacts["graph_schema"]
    if set(graph["nodes"]) != ontology_types:
        raise KnowledgePlatformError("Graph nodes do not match ontology types")
    if set(graph["edges"]) != ontology_relations:
        raise KnowledgePlatformError("Graph edges do not match ontology relationships")
    if graph["adapter"]["enabled"]:
        raise KnowledgePlatformError("Knowledge graph adapter must remain disabled")

    indexing = artifacts["indexing"]
    stage_ids = [stage["id"] for stage in indexing["stages"]]
    if len(stage_ids) != len(set(stage_ids)):
        raise KnowledgePlatformError("Duplicate knowledge indexing stage")
    seen: set[str] = set()
    for stage in indexing["stages"]:
        unknown = set(stage["dependencies"]) - seen
        if unknown:
            raise KnowledgePlatformError(
                f"Indexing stage {stage['id']} has unavailable dependencies: "
                + ", ".join(sorted(unknown))
            )
        if stage["enabled"]:
            raise KnowledgePlatformError(
                f"Knowledge indexing runtime must remain disabled: {stage['id']}"
            )
        seen.add(stage["id"])
    if ingestion["spec"]["stages"] != stage_ids:
        raise KnowledgePlatformError("Ingestion pipeline does not match indexing plan")
    if ingestion["spec"]["enabled"]:
        raise KnowledgePlatformError("Knowledge ingestion runtime must remain disabled")

    engine_manifest = _resolve_repository_path(root, rag["spec"]["engine_manifest"])
    if engine_manifest != (root / "manifests" / "rag-engine.yaml").resolve():
        raise KnowledgePlatformError("Knowledge RAG pipeline uses an unknown engine")
    if rag["spec"]["enabled"]:
        raise KnowledgePlatformError("Knowledge RAG runtime must remain disabled")

    for profile in artifacts["vector_profiles"]["profiles"]:
        if profile["enabled"] and (
            profile["lifecycle"] != "active"
            or profile["model_ref"] is None
            or profile["dimensions"] is None
        ):
            raise KnowledgePlatformError(
                f"Vector profile lacks an active model contract: {profile['id']}"
            )

    known_collections = set(registry_collections)
    for source in registry["sources"]:
        if source["collection"] not in known_collections:
            raise KnowledgePlatformError(
                f"Knowledge source references unknown collection: {source['id']}"
            )
        metadata_path = _resolve_repository_path(root, source["metadata"])
        validate_document_metadata(root, metadata_path)
        if source["lifecycle"] != "active" and source["enabled"]:
            raise KnowledgePlatformError(
                f"Non-active knowledge source cannot be enabled: {source['id']}"
            )

    spec = manifest["spec"]
    adapters_enabled = (
        any(provider["enabled"] for provider in config["spec"]["providers"])
        or graph["adapter"]["enabled"]
    )
    if spec["adapters_enabled"] != adapters_enabled:
        raise KnowledgePlatformError(
            "Knowledge adapter activation claim is inconsistent"
        )
    if spec["installable"] and not (
        spec["runtime_tested"]
        and spec["lifecycle"] == "active"
        and spec["adapters_enabled"]
    ):
        raise KnowledgePlatformError(
            "Knowledge platform cannot be installable before runtime tests and activation"
        )

    return KnowledgePlatformSummary(
        version=manifest["metadata"]["version"],
        lifecycle=spec["lifecycle"],
        installable=spec["installable"],
        collection_ids=tuple(registry_collections),
        source_count=len(registry["sources"]),
    )
