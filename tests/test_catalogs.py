from pathlib import Path
import shutil

import pytest
import yaml

from jdgf_framework.catalogs import CatalogError, validate_bootstrap_catalogs


ROOT = Path(__file__).resolve().parents[1]


def copy_catalogs(target: Path) -> None:
    shutil.copytree(ROOT / "manifests", target / "manifests")
    shutil.copytree(ROOT / "registry", target / "registry")


def test_repository_bootstrap_catalogs_are_valid() -> None:
    summary = validate_bootstrap_catalogs(ROOT)

    assert summary.manifest_count == 3
    assert summary.registry_count == 6
    assert summary.service_count == 14


def test_module_manifest_and_registry_must_match(tmp_path: Path) -> None:
    copy_catalogs(tmp_path)
    registry_path = tmp_path / "registry" / "modules.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["modules"][0]["lifecycle"] = "deferred"
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")

    with pytest.raises(CatalogError, match="do not match"):
        validate_bootstrap_catalogs(tmp_path)


def test_duplicate_port_reservation_is_rejected(tmp_path: Path) -> None:
    copy_catalogs(tmp_path)
    registry_path = tmp_path / "registry" / "ports.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["ports"][1]["port"] = registry["ports"][0]["port"]
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")

    with pytest.raises(CatalogError, match="Duplicate port"):
        validate_bootstrap_catalogs(tmp_path)


def test_deferred_service_cannot_be_enabled(tmp_path: Path) -> None:
    copy_catalogs(tmp_path)
    registry_path = tmp_path / "registry" / "services.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["services"][0]["enabled"] = True
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")

    with pytest.raises(CatalogError, match="cannot be enabled"):
        validate_bootstrap_catalogs(tmp_path)
