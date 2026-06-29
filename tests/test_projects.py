import shutil
from pathlib import Path

import pytest
import yaml

from jdgf_framework.projects import (
    RegistryError,
    load_project_registry,
    validate_project_manifest,
    validate_projects_platform,
)

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def _project_document(
    project_id: str = "sample-project",
    lifecycle: str = "active",
    approval: bool = True,
) -> dict:
    return {
        "api_version": "jdgf.io/v1alpha1",
        "contract_version": "1.0",
        "kind": "Project",
        "metadata": {
            "id": project_id,
            "name": "Sample",
            "version": "1.0.0",
            "description": "Sample project contract.",
            "license": "MIT",
        },
        "spec": {
            "lifecycle": lifecycle,
            "owner": "Test",
            "governance": {
                "human_approval_required": approval,
                "roles": {},
            },
            "architecture": {
                "modules": [],
                "services": [],
                "dependencies": [],
                "datasets": [],
                "knowledge": [],
                "agents": [],
            },
            "capabilities": [],
            "timeline": {
                "created": "2026-06-27",
                "updated": "2026-06-27",
                "release": "1.0.0",
            },
            "documentation": {"readme": "docs/sample.md"},
        },
    }


def _registry_document(entries: list[dict]) -> dict:
    return {
        "api_version": "jdgf.io/v1alpha1",
        "contract_version": "1.0",
        "kind": "ProjectRegistry",
        "metadata": {"version": "0.3.0", "lifecycle": "active"},
        "projects": entries,
    }


def _entry(
    project_id: str = "sample-project",
    manifest: str = "projects/sample/project.yaml",
    lifecycle: str = "active",
) -> dict:
    return {
        "id": project_id,
        "version": "1.0.0",
        "lifecycle": lifecycle,
        "manifest": manifest,
    }


def _initialize_contract_root(root: Path) -> None:
    (root / "registry").mkdir()
    (root / "projects").mkdir()
    for relative_path in (
        Path("registry/project-registry.schema.yaml"),
        Path("projects/project.schema.yaml"),
    ):
        target = root / relative_path
        target.write_text(
            (ROOT / relative_path).read_text(encoding="utf-8"), encoding="utf-8"
        )


def _initialize_platform_root(root: Path) -> None:
    shutil.copytree(ROOT / "projects", root / "projects")
    shutil.copytree(ROOT / "registry", root / "registry")
    shutil.copytree(ROOT / "manifests", root / "manifests")
    for filename in ("ARCHITECTURE.md", "CHANGELOG.md", "ROADMAP.md"):
        shutil.copy2(ROOT / filename, root / filename)


def test_repository_registry_is_valid() -> None:
    projects = load_project_registry(ROOT)

    assert [project.project_id for project in projects] == ["jdgf-framework"]
    assert projects[0].lifecycle == "active"
    assert projects[0].version == "0.10.1"


def test_projects_platform_is_active_and_validated() -> None:
    summary = validate_projects_platform(ROOT)

    assert summary.version == "0.3.0"
    assert summary.lifecycle == "active"
    assert summary.installable is True
    assert summary.project_ids == ("jdgf-framework",)


def test_registry_rejects_manifest_path_escape(tmp_path: Path) -> None:
    _initialize_contract_root(tmp_path)
    _write(
        tmp_path / "registry" / "projects.yaml",
        _registry_document([_entry(manifest="../outside.yaml")]),
    )

    with pytest.raises(RegistryError, match="project-registry.schema.yaml"):
        load_project_registry(tmp_path)


def test_registry_rejects_identifier_mismatch(tmp_path: Path) -> None:
    _initialize_contract_root(tmp_path)
    project_dir = tmp_path / "projects" / "sample"
    project_dir.mkdir()
    _write(
        tmp_path / "registry" / "projects.yaml",
        _registry_document([_entry(project_id="wrong-project")]),
    )
    _write(project_dir / "project.yaml", _project_document())

    with pytest.raises(RegistryError, match="does not match"):
        load_project_registry(tmp_path)


def test_registry_schema_rejects_wrong_kind(tmp_path: Path) -> None:
    _initialize_contract_root(tmp_path)
    registry = _registry_document([])
    registry["kind"] = "NotAProjectRegistry"
    _write(tmp_path / "registry" / "projects.yaml", registry)

    with pytest.raises(RegistryError, match="project-registry.schema.yaml"):
        load_project_registry(tmp_path)


def test_project_schema_rejects_undeclared_fields(tmp_path: Path) -> None:
    _initialize_contract_root(tmp_path)
    project_dir = tmp_path / "projects" / "sample"
    project_dir.mkdir()
    _write(
        tmp_path / "registry" / "projects.yaml",
        _registry_document([_entry()]),
    )
    project = _project_document()
    project["spec"]["unexpected"] = True
    _write(project_dir / "project.yaml", project)

    with pytest.raises(RegistryError, match="project.schema.yaml"):
        load_project_registry(tmp_path)


def test_project_schema_rejects_non_boolean_approval(tmp_path: Path) -> None:
    manifest = tmp_path / "project.yaml"
    project = _project_document()
    project["spec"]["governance"]["human_approval_required"] = "yes"
    _write(manifest, project)

    with pytest.raises(RegistryError, match="human_approval_required"):
        validate_project_manifest(manifest, ROOT / "projects/project.schema.yaml")


def test_registry_rejects_version_mismatch(tmp_path: Path) -> None:
    _initialize_contract_root(tmp_path)
    project_dir = tmp_path / "projects" / "sample"
    project_dir.mkdir()
    entry = _entry()
    entry["version"] = "2.0.0"
    _write(
        tmp_path / "registry" / "projects.yaml",
        _registry_document([entry]),
    )
    _write(project_dir / "project.yaml", _project_document())

    with pytest.raises(RegistryError, match="version.*does not match"):
        load_project_registry(tmp_path)


def test_active_project_requires_human_approval(tmp_path: Path) -> None:
    _initialize_platform_root(tmp_path)
    manifest_path = tmp_path / "projects" / "JDGF" / "project.yaml"
    project = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    project["spec"]["governance"]["human_approval_required"] = False
    _write(manifest_path, project)

    with pytest.raises(RegistryError, match="requires human approval"):
        validate_projects_platform(tmp_path)


def test_project_documentation_must_exist(tmp_path: Path) -> None:
    _initialize_platform_root(tmp_path)
    manifest_path = tmp_path / "projects" / "JDGF" / "project.yaml"
    project = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    project["spec"]["documentation"]["readme"] = "docs/missing.md"
    _write(manifest_path, project)

    with pytest.raises(RegistryError, match="documentation is missing"):
        validate_projects_platform(tmp_path)


def test_project_capability_must_exist(tmp_path: Path) -> None:
    _initialize_platform_root(tmp_path)
    manifest_path = tmp_path / "projects" / "JDGF" / "project.yaml"
    project = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    project["spec"]["capabilities"].append("unknown-capability")
    _write(manifest_path, project)

    with pytest.raises(RegistryError, match="unknown capabilities"):
        validate_projects_platform(tmp_path)
