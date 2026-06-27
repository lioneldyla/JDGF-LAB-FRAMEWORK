from pathlib import Path
import shutil

import pytest
import yaml

from jdgf_framework.rag import RagContractError, validate_rag_contracts


ROOT = Path(__file__).resolve().parents[1]


def copy_rag_contracts(target: Path) -> None:
    for directory in ("manifests", "platform", "registry"):
        shutil.copytree(ROOT / directory, target / directory)


def test_repository_rag_contracts_are_valid() -> None:
    contracts = validate_rag_contracts(ROOT)

    assert contracts.manifest_version == "0.9.2"
    assert contracts.engine_version == "1.0.0"
    assert contracts.contract_version == "1.0"
    assert contracts.lifecycle == "specified"
    assert contracts.maturity == "experimental"
    assert contracts.installable is False
    assert len(contracts.component_ids) == 9
    assert len(contracts.dependency_ids) == 6
    assert contracts.runtime_capabilities == (
        "citation-preservation",
        "lexical-retrieval",
    )


def test_runtime_capability_partition_must_be_complete(tmp_path: Path) -> None:
    copy_rag_contracts(tmp_path)
    path = tmp_path / "platform" / "rag" / "local-runtime.yaml"
    runtime = yaml.safe_load(path.read_text(encoding="utf-8"))
    runtime["spec"]["deferred_capabilities"].remove("confidence-scoring")
    path.write_text(yaml.safe_dump(runtime), encoding="utf-8")

    with pytest.raises(RagContractError, match="partition is incomplete"):
        validate_rag_contracts(tmp_path)


def test_component_schema_rejects_unknown_fields(tmp_path: Path) -> None:
    copy_rag_contracts(tmp_path)
    reranker_path = tmp_path / "platform" / "rag" / "reranker.yaml"
    reranker = yaml.safe_load(reranker_path.read_text(encoding="utf-8"))
    reranker["spec"]["unsupported"] = True
    reranker_path.write_text(yaml.safe_dump(reranker), encoding="utf-8")

    with pytest.raises(RagContractError, match="component.schema.yaml"):
        validate_rag_contracts(tmp_path)


def test_confidence_thresholds_must_descend(tmp_path: Path) -> None:
    copy_rag_contracts(tmp_path)
    confidence_path = tmp_path / "platform" / "rag" / "confidence-scoring.yaml"
    confidence = yaml.safe_load(confidence_path.read_text(encoding="utf-8"))
    confidence["spec"]["thresholds"] = {"high": 0.6, "medium": 0.8, "low": 0.4}
    confidence_path.write_text(yaml.safe_dump(confidence), encoding="utf-8")

    with pytest.raises(RagContractError, match="strictly descending"):
        validate_rag_contracts(tmp_path)


def test_registry_schema_rejects_incorrect_types(tmp_path: Path) -> None:
    copy_rag_contracts(tmp_path)
    registry_path = tmp_path / "registry" / "rag.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["metadata"]["version"] = 1
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")

    with pytest.raises(RagContractError, match="rag.schema.yaml"):
        validate_rag_contracts(tmp_path)


def test_missing_dependency_definition_is_rejected(tmp_path: Path) -> None:
    copy_rag_contracts(tmp_path)
    registry_path = tmp_path / "registry" / "rag.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["dependencies"] = [
        dependency
        for dependency in registry["dependencies"]
        if dependency["id"] != "model-gateway"
    ]
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")

    with pytest.raises(RagContractError, match="missing dependencies"):
        validate_rag_contracts(tmp_path)


def test_incompatible_contract_version_is_rejected(tmp_path: Path) -> None:
    copy_rag_contracts(tmp_path)
    manifest_path = tmp_path / "manifests" / "rag-engine.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["contract_version"] = "2.0"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

    with pytest.raises(RagContractError, match="Incompatible RAG contract_version"):
        validate_rag_contracts(tmp_path)


def test_unsupported_api_version_is_rejected(tmp_path: Path) -> None:
    copy_rag_contracts(tmp_path)
    manifest_path = tmp_path / "manifests" / "rag-engine.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["api_version"] = "jdgf.io/v2"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

    with pytest.raises(RagContractError, match="Unsupported RAG api_version"):
        validate_rag_contracts(tmp_path)


def test_missing_component_configuration_is_rejected(tmp_path: Path) -> None:
    copy_rag_contracts(tmp_path)
    (tmp_path / "platform" / "rag" / "reranker.yaml").unlink()

    with pytest.raises(RagContractError, match="Missing RAG contract"):
        validate_rag_contracts(tmp_path)


def test_incompatible_registry_version_is_rejected(tmp_path: Path) -> None:
    copy_rag_contracts(tmp_path)
    registry_path = tmp_path / "registry" / "rag.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["metadata"]["version"] = "2.0.0"
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")

    with pytest.raises(RagContractError, match="major version"):
        validate_rag_contracts(tmp_path)
