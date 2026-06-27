from pathlib import Path
import shutil

import pytest
import yaml

from jdgf_framework.data_platform import DataPlatformError, validate_data_platform


ROOT = Path(__file__).resolve().parents[1]


def _copy_contracts(tmp_path: Path) -> Path:
    for relative in (
        "manifests/database-platform.yaml",
        "manifests/database-platform.schema.yaml",
        "registry/database-services.yaml",
        "registry/database-services.schema.yaml",
        "registry/services.yaml",
        "infrastructure/postgres/config/postgresql.conf",
        "infrastructure/redis/compose.yaml",
        "infrastructure/qdrant/compose.yaml",
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


def test_data_platform_contracts_are_valid() -> None:
    summary = validate_data_platform(ROOT)

    assert summary.version == "0.2.0"
    assert summary.lifecycle == "specified"
    assert summary.installable is False
    assert set(summary.service_ids) == {"postgres", "redis", "neo4j", "qdrant"}


def test_non_active_database_service_cannot_be_enabled(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    registry_path = root / "registry" / "database-services.yaml"
    registry = _load(registry_path)
    registry["services"][0]["enabled"] = True
    _write(registry_path, registry)

    with pytest.raises(DataPlatformError, match="Non-active"):
        validate_data_platform(root)


def test_default_connection_must_reference_matching_type(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    registry_path = root / "registry" / "database-services.yaml"
    registry = _load(registry_path)
    registry["connections"]["default_sql"] = "redis"
    _write(registry_path, registry)

    with pytest.raises(DataPlatformError, match="requires type relational"):
        validate_data_platform(root)


def test_unknown_default_connection_is_rejected(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    registry_path = root / "registry" / "database-services.yaml"
    registry = _load(registry_path)
    registry["connections"]["default_vector"] = "missing-store"
    _write(registry_path, registry)

    with pytest.raises(DataPlatformError, match="references unknown service"):
        validate_data_platform(root)


def test_installable_requires_runtime_and_restore_evidence(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    manifest_path = root / "manifests" / "database-platform.yaml"
    manifest = _load(manifest_path)
    manifest["spec"]["installable"] = True
    _write(manifest_path, manifest)

    with pytest.raises(DataPlatformError, match="runtime, restore and activation"):
        validate_data_platform(root)


def test_schema_rejects_additional_fields(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    manifest_path = root / "manifests" / "database-platform.yaml"
    manifest = _load(manifest_path)
    manifest["spec"]["claim"] = "production-ready"
    _write(manifest_path, manifest)

    with pytest.raises(DataPlatformError, match="Additional properties"):
        validate_data_platform(root)
