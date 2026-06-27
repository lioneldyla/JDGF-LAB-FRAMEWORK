from pathlib import Path
import shutil

import pytest
import yaml

from jdgf_framework.projects import validate_project_manifest
from jdgf_framework.sdk_platform import (
    SdkPlatformError,
    scaffold_project,
    validate_sdk_platform,
)


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def _copy_contracts(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "sdk", tmp_path / "sdk")
    shutil.copytree(ROOT / "projects", tmp_path / "projects")
    for relative in (
        "manifests/sdk-platform.yaml",
        "manifests/sdk-platform.schema.yaml",
        "registry/sdk.yaml",
        "registry/sdk.schema.yaml",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def test_sdk_platform_contracts_are_valid() -> None:
    summary = validate_sdk_platform(ROOT)

    assert summary.version == "0.7.0"
    assert summary.lifecycle == "active"
    assert summary.active_generators == ("project",)


def test_project_scaffold_is_valid_and_unregistered(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)

    destination = scaffold_project(root, "new-project", "New Project", "Owner")
    record = validate_project_manifest(
        destination / "project.yaml", root / "projects" / "project.schema.yaml"
    )

    assert record.project_id == "new-project"
    assert record.lifecycle == "proposed"
    assert (destination / "README.md").is_file()


@pytest.mark.parametrize("project_id", ["../escape", "Bad_Name", "x"])
def test_project_scaffold_rejects_unsafe_identifiers(
    tmp_path: Path, project_id: str
) -> None:
    root = _copy_contracts(tmp_path)

    with pytest.raises(SdkPlatformError, match="Project id"):
        scaffold_project(root, project_id, "Unsafe", "Owner")


def test_project_scaffold_never_overwrites(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    scaffold_project(root, "new-project", "New Project", "Owner")

    with pytest.raises(SdkPlatformError, match="already exists"):
        scaffold_project(root, "new-project", "Replacement", "Owner")


def test_deferred_generator_cannot_claim_command(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "registry" / "sdk.yaml"
    registry = _load(path)
    registry["capabilities"][1]["command"] = "jdgf scaffold-agent"
    _write(path, registry)

    with pytest.raises(SdkPlatformError, match="cannot claim implementation"):
        validate_sdk_platform(root)


def test_sdk_versions_must_match(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "registry" / "sdk.yaml"
    registry = _load(path)
    registry["metadata"]["version"] = "0.7.1"
    _write(path, registry)

    with pytest.raises(SdkPlatformError, match="versions do not match"):
        validate_sdk_platform(root)
