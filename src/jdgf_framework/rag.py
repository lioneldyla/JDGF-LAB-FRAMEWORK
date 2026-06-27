"""Advanced RAG capability contract loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
import yaml


@dataclass(frozen=True)
class RagContractSet:
    manifest_version: str
    engine_version: str
    contract_version: str
    lifecycle: str
    maturity: str
    installable: bool
    component_ids: tuple[str, ...]
    dependency_ids: tuple[str, ...]


class RagContractError(ValueError):
    """Raised when an Advanced RAG contract is invalid."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RagContractError(f"Missing RAG contract: {path}") from exc
    except yaml.YAMLError as exc:
        raise RagContractError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(content, dict):
        raise RagContractError(f"Expected a YAML mapping in {path}")
    return content


def _validate_document(
    document: dict[str, Any], schema_path: Path, document_path: Path
) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise RagContractError(
            f"Invalid RAG schema in {schema_path}: {exc.message}"
        ) from exc

    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise RagContractError(
            f"{document_path} violates {schema_path.name} at "
            f"{location}: {error.message}"
        )


def _resolve_contract(root: Path, value: str, allowed_directory: Path) -> Path:
    relative_path = Path(value)
    if relative_path.is_absolute():
        raise RagContractError("RAG contract paths must be repository-relative")
    resolved = (root / relative_path).resolve()
    allowed = allowed_directory.resolve()
    if not resolved.is_relative_to(allowed):
        raise RagContractError(f"RAG contract path escapes {allowed_directory}")
    return resolved


def _require_compatible(
    document: dict[str, Any], document_path: Path, policy: dict[str, Any]
) -> None:
    supported_api_versions = policy["spec"]["supported_api_versions"]
    if document["api_version"] not in supported_api_versions:
        raise RagContractError(
            f"Unsupported RAG api_version in {document_path}: "
            f"{document['api_version']}"
        )
    current_contract_version = policy["spec"]["current_contract_version"]
    if document["contract_version"] != current_contract_version:
        raise RagContractError(
            f"Incompatible RAG contract_version in {document_path}: "
            f"{document['contract_version']} != {current_contract_version}"
        )


def validate_rag_contracts(root: Path) -> RagContractSet:
    """Validate the RAG manifest, registry, engine and component contracts."""

    root = root.resolve()
    manifest_path = root / "manifests" / "rag-engine.yaml"
    manifest = _load_mapping(manifest_path)
    _validate_document(
        manifest, root / "manifests" / "rag-engine.schema.yaml", manifest_path
    )

    spec = manifest["spec"]
    compatibility_path = _resolve_contract(
        root, spec["compatibility"], root / "platform" / "rag"
    )
    compatibility = _load_mapping(compatibility_path)
    _validate_document(
        compatibility,
        root / "platform" / "rag" / "compatibility.schema.yaml",
        compatibility_path,
    )
    _require_compatible(manifest, manifest_path, compatibility)

    engine_path = _resolve_contract(root, spec["engine"], root / "platform" / "rag")
    registry_path = _resolve_contract(root, spec["registry"], root / "registry")

    engine = _load_mapping(engine_path)
    _validate_document(
        engine, root / "platform" / "rag" / "rag-engine.schema.yaml", engine_path
    )
    _require_compatible(engine, engine_path, compatibility)
    registry = _load_mapping(registry_path)
    _validate_document(
        registry, root / "registry" / "rag.schema.yaml", registry_path
    )
    _require_compatible(registry, registry_path, compatibility)

    lifecycle = spec["lifecycle"]
    if engine["spec"]["lifecycle"] != lifecycle:
        raise RagContractError("RAG engine lifecycle does not match its manifest")
    if registry["metadata"]["lifecycle"] != lifecycle:
        raise RagContractError("RAG registry lifecycle does not match its manifest")
    if lifecycle != "active" and spec["installable"]:
        raise RagContractError("A non-active RAG capability cannot be installable")

    maturity = registry["metadata"]["maturity"]
    if lifecycle == "specified" and maturity not in {"experimental", "preview"}:
        raise RagContractError(
            "A specified RAG capability must have experimental or preview maturity"
        )
    engine_major = engine["metadata"]["version"].split(".", 1)[0]
    registry_major = registry["metadata"]["version"].split(".", 1)[0]
    if registry_major != engine_major:
        raise RagContractError("RAG registry major version does not match the engine")
    engine_capabilities = set(engine["spec"]["capabilities"])
    if set(registry["capabilities"]) != engine_capabilities:
        raise RagContractError("RAG registry capabilities do not match the engine")

    dependency_ids = [dependency["id"] for dependency in registry["dependencies"]]
    if len(dependency_ids) != len(set(dependency_ids)):
        raise RagContractError("Duplicate RAG dependency id")
    if spec["installable"]:
        unavailable_required = [
            dependency["id"]
            for dependency in registry["dependencies"]
            if dependency["required_for_runtime"]
            and dependency["status"] != "available"
        ]
        if unavailable_required:
            raise RagContractError(
                "Installable RAG capability has unavailable dependencies: "
                + ", ".join(unavailable_required)
            )

    component_ids: list[str] = []
    config_paths: set[Path] = set()
    for entry in registry["components"]:
        component_id = entry["id"]
        if component_id in component_ids:
            raise RagContractError(f"Duplicate RAG component id: {component_id}")
        config_path = _resolve_contract(
            root, entry["config"], root / "platform" / "rag"
        )
        if config_path in config_paths:
            raise RagContractError(f"Duplicate RAG component config: {config_path}")

        component = _load_mapping(config_path)
        _validate_document(
            component,
            root / "platform" / "rag" / "component.schema.yaml",
            config_path,
        )
        _require_compatible(component, config_path, compatibility)
        if component["kind"] != entry["kind"]:
            raise RagContractError(
                f"RAG component kind mismatch for {component_id}: "
                f"{entry['kind']} != {component['kind']}"
            )
        if component["metadata"]["name"] != component_id:
            raise RagContractError(
                f"RAG component name does not match registry id: {component_id}"
            )
        if component["metadata"]["lifecycle"] != lifecycle:
            raise RagContractError(
                f"RAG component lifecycle mismatch for {component_id}"
            )
        unknown_capabilities = set(entry["capabilities"]) - engine_capabilities
        if unknown_capabilities:
            raise RagContractError(
                f"RAG component {component_id} declares unknown capabilities: "
                + ", ".join(sorted(unknown_capabilities))
            )
        missing_dependencies = set(entry["dependencies"]) - set(dependency_ids)
        if missing_dependencies:
            raise RagContractError(
                f"RAG component {component_id} references missing dependencies: "
                + ", ".join(sorted(missing_dependencies))
            )
        if entry["version"].split(".", 1)[0] != engine_major:
            raise RagContractError(
                f"RAG component major version mismatch for {component_id}"
            )
        if entry["maturity"] != maturity:
            raise RagContractError(
                f"RAG component maturity mismatch for {component_id}"
            )
        component_ids.append(component_id)
        config_paths.add(config_path)

    confidence = _load_mapping(root / "platform" / "rag" / "confidence-scoring.yaml")
    thresholds = confidence["spec"]["thresholds"]
    if not thresholds["high"] > thresholds["medium"] > thresholds["low"]:
        raise RagContractError("RAG confidence thresholds must be strictly descending")

    return RagContractSet(
        manifest_version=manifest["metadata"]["version"],
        engine_version=engine["metadata"]["version"],
        contract_version=manifest["contract_version"],
        lifecycle=lifecycle,
        maturity=maturity,
        installable=spec["installable"],
        component_ids=tuple(component_ids),
        dependency_ids=tuple(dependency_ids),
    )
