from pathlib import Path
import shutil

import pytest
import yaml

from jdgf_framework.core_platform import (
    CorePlatformError,
    run_doctor,
    validate_core_platform,
)


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def _copy_contracts(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "core", tmp_path / "core")
    for relative in (
        "manifests/framework-core-platform.yaml",
        "manifests/framework-core-platform.schema.yaml",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for relative in (
        "bootstrap.sh",
        "verify.sh",
        "src/jdgf_framework/core_platform.py",
        "scripts/devsecops/build-release.sh",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
    return tmp_path


def test_core_platform_contracts_are_valid() -> None:
    summary = validate_core_platform(ROOT)

    assert summary.version == "0.8.0"
    assert summary.lifecycle == "active"
    assert summary.active_operations == ("bootstrap", "doctor", "package", "validate")


def test_doctor_checks_authoritative_local_state() -> None:
    report = run_doctor(ROOT)

    assert report.version == "0.10.0"
    assert "version-consistency" in report.checks


def test_active_operation_requires_implementation(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    (root / "verify.sh").unlink()

    with pytest.raises(CorePlatformError, match="lacks implementation"):
        validate_core_platform(root)


def test_deferred_operation_cannot_claim_implementation(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "core" / "framework.yaml"
    definition = _load(path)
    definition["spec"]["operations"][4]["implementation"] = "update.sh"
    _write(path, definition)

    with pytest.raises(CorePlatformError, match="cannot claim implementation"):
        validate_core_platform(root)


def test_consequential_operation_requires_approval(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "core" / "framework.yaml"
    definition = _load(path)
    definition["spec"]["operations"][3]["approval_required"] = False
    _write(path, definition)

    with pytest.raises(CorePlatformError, match="requires approval"):
        validate_core_platform(root)


def test_active_operation_sets_must_match(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "manifests" / "framework-core-platform.yaml"
    manifest = _load(path)
    manifest["spec"]["active_operations"].remove("doctor")
    _write(path, manifest)

    with pytest.raises(CorePlatformError, match="declarations differ"):
        validate_core_platform(root)
