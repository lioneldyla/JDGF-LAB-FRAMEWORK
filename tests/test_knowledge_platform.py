from pathlib import Path
import shutil

import pytest
import yaml

from jdgf_framework.knowledge_platform import (
    KnowledgePlatformError,
    validate_document_metadata,
    validate_knowledge_platform,
)


ROOT = Path(__file__).resolve().parents[1]


def _copy_contracts(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    for relative in (
        "manifests/knowledge-platform.yaml",
        "manifests/knowledge-platform.schema.yaml",
        "manifests/rag-engine.yaml",
        "registry/knowledge.yaml",
        "registry/knowledge.schema.yaml",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def _valid_metadata() -> dict:
    return {
        "id": "source-001",
        "title": "Portable knowledge source",
        "authors": ["JDGF contributors"],
        "language": "en",
        "publication_date": "2026-06-27",
        "document_type": "documentation",
        "source": {"kind": "file", "locator": "docs/example.md"},
        "checksum": "sha256:" + ("a" * 64),
    }


def test_knowledge_platform_contracts_are_valid() -> None:
    summary = validate_knowledge_platform(ROOT)

    assert summary.version == "0.3.0"
    assert summary.lifecycle == "specified"
    assert summary.installable is False
    assert len(summary.collection_ids) == 6
    assert summary.source_count == 0


def test_document_metadata_schema_accepts_governed_metadata(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    metadata_path = root / "knowledge" / "source-metadata.yaml"
    _write(metadata_path, _valid_metadata())

    document = validate_document_metadata(root, metadata_path)

    assert document["id"] == "source-001"


def test_document_metadata_rejects_unknown_fields(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    metadata_path = root / "knowledge" / "source-metadata.yaml"
    metadata = _valid_metadata()
    metadata["unverified_claim"] = True
    _write(metadata_path, metadata)

    with pytest.raises(KnowledgePlatformError, match="Additional properties"):
        validate_document_metadata(root, metadata_path)


def test_document_metadata_rejects_invalid_date(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    metadata_path = root / "knowledge" / "source-metadata.yaml"
    metadata = _valid_metadata()
    metadata["publication_date"] = "2026-99-99"
    _write(metadata_path, metadata)

    with pytest.raises(KnowledgePlatformError, match="not a 'date'"):
        validate_document_metadata(root, metadata_path)


def test_graph_schema_must_match_ontology(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    graph_path = root / "knowledge" / "graph_schema.yaml"
    graph = _load(graph_path)
    graph["nodes"].remove("concept")
    _write(graph_path, graph)

    with pytest.raises(KnowledgePlatformError, match="Graph nodes"):
        validate_knowledge_platform(root)


def test_indexing_dependency_must_precede_stage(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    indexing_path = root / "knowledge" / "indexing.yaml"
    indexing = _load(indexing_path)
    indexing["stages"][0]["dependencies"] = ["register"]
    _write(indexing_path, indexing)

    with pytest.raises(KnowledgePlatformError, match="unavailable dependencies"):
        validate_knowledge_platform(root)


def test_provider_cannot_be_enabled_before_activation(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    config_path = root / "knowledge" / "knowledge.yaml"
    config = _load(config_path)
    config["spec"]["providers"][0]["enabled"] = True
    _write(config_path, config)

    with pytest.raises(KnowledgePlatformError, match="Non-active knowledge provider"):
        validate_knowledge_platform(root)


def test_installable_requires_runtime_evidence(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    manifest_path = root / "manifests" / "knowledge-platform.yaml"
    manifest = _load(manifest_path)
    manifest["spec"]["installable"] = True
    _write(manifest_path, manifest)

    with pytest.raises(KnowledgePlatformError, match="runtime tests"):
        validate_knowledge_platform(root)


def test_registry_artifact_cannot_escape_repository(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    registry_path = root / "registry" / "knowledge.yaml"
    registry = _load(registry_path)
    registry["artifacts"]["ontology"] = "../outside.yaml"
    _write(registry_path, registry)

    with pytest.raises(KnowledgePlatformError):
        validate_knowledge_platform(root)


def test_manifest_and_registry_versions_must_match(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    registry_path = root / "registry" / "knowledge.yaml"
    registry = _load(registry_path)
    registry["metadata"]["version"] = "0.4.0"
    _write(registry_path, registry)

    with pytest.raises(KnowledgePlatformError, match="versions differ"):
        validate_knowledge_platform(root)
