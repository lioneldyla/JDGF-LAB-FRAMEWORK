from pathlib import Path
import shutil

import pytest
import yaml

from jdgf_framework.judicial_intelligence import (
    JudicialIntelligenceError,
    validate_judicial_intelligence,
)


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def _copy_contracts(tmp_path: Path) -> Path:
    for relative in (
        "platform/judicial-intelligence/profile.yaml",
        "platform/judicial-intelligence/profile.schema.yaml",
        "manifests/judicial-intelligence-platform.yaml",
        "manifests/judicial-intelligence-platform.schema.yaml",
        "registry/judicial-intelligence.yaml",
        "registry/judicial-intelligence.schema.yaml",
        "knowledge/metadata.schema.yaml",
        "registry/knowledge.yaml",
        "platform/rag/rag-engine.yaml",
        "platform/rag/citation-engine.yaml",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def test_judicial_intelligence_contracts_are_valid() -> None:
    summary = validate_judicial_intelligence(ROOT)

    assert summary.version == "0.9.0"
    assert summary.lifecycle == "specified"
    assert summary.enabled is False
    assert len(summary.outputs) == 2


def test_extension_rejects_unknown_fields(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "platform" / "judicial-intelligence" / "profile.yaml"
    profile = _load(path)
    profile["spec"]["legal_reasoning"] = True
    _write(path, profile)

    with pytest.raises(JudicialIntelligenceError, match="Additional properties"):
        validate_judicial_intelligence(root)


def test_extension_must_use_authoritative_composition(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "platform" / "judicial-intelligence" / "profile.yaml"
    profile = _load(path)
    profile["spec"]["composition"]["rag_engine"] = "platform/custom-rag.yaml"
    _write(path, profile)

    with pytest.raises(JudicialIntelligenceError, match="authoritative"):
        validate_judicial_intelligence(root)


def test_extension_requires_existing_composition_files(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    (root / "platform" / "rag" / "citation-engine.yaml").unlink()

    with pytest.raises(JudicialIntelligenceError, match="is missing"):
        validate_judicial_intelligence(root)


def test_extension_cannot_enable_runtime(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "platform" / "judicial-intelligence" / "profile.schema.yaml"
    schema = _load(path)
    schema["properties"]["spec"]["properties"]["runtime_implemented"] = {
        "type": "boolean"
    }
    _write(path, schema)
    profile_path = root / "platform" / "judicial-intelligence" / "profile.yaml"
    profile = _load(profile_path)
    profile["spec"]["runtime_implemented"] = True
    _write(profile_path, profile)

    with pytest.raises(JudicialIntelligenceError, match="runtime must remain disabled"):
        validate_judicial_intelligence(root)


def test_extension_versions_must_match(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "registry" / "judicial-intelligence.yaml"
    registry = _load(path)
    registry["metadata"]["version"] = "0.9.1"
    _write(path, registry)

    with pytest.raises(JudicialIntelligenceError, match="versions do not match"):
        validate_judicial_intelligence(root)
