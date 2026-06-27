from pathlib import Path

import pytest
import yaml

from jdgf_framework.projects import (
    RegistryError,
    load_project_registry,
    validate_project_manifest,
)


ROOT = Path(__file__).resolve().parents[1]


def initialize_contract_root(root: Path) -> None:
    """Create the contract directories used by isolated registry tests."""

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


def test_repository_registry_is_valid() -> None:
    projects = load_project_registry(ROOT)

    assert [project.project_id for project in projects] == ["jdgf-framework"]
    assert projects[0].lifecycle == "active"


def test_registry_rejects_manifest_path_escape(tmp_path: Path) -> None:
    initialize_contract_root(tmp_path)
    registry_dir = tmp_path / "registry"
    registry = {
        "api_version": "jdgf.io/v1alpha1",
        "kind": "ProjectRegistry",
        "projects": [{"id": "bad-project", "manifest": "../outside.yaml"}],
    }
    (registry_dir / "projects.yaml").write_text(yaml.safe_dump(registry), encoding="utf-8")

    with pytest.raises(RegistryError, match="escapes repository"):
        load_project_registry(tmp_path)


def test_registry_rejects_identifier_mismatch(tmp_path: Path) -> None:
    initialize_contract_root(tmp_path)
    registry_dir = tmp_path / "registry"
    project_dir = tmp_path / "projects" / "sample"
    project_dir.mkdir()
    (registry_dir / "projects.yaml").write_text(
        yaml.safe_dump(
            {
                "api_version": "jdgf.io/v1alpha1",
                "kind": "ProjectRegistry",
                "projects": [
                    {"id": "wrong-project", "manifest": "projects/sample/project.yaml"}
                ],
            }
        ),
        encoding="utf-8",
    )
    (project_dir / "project.yaml").write_text(
        yaml.safe_dump(
            {
                "api_version": "jdgf.io/v1alpha1",
                "kind": "Project",
                "metadata": {"id": "sample-project", "name": "Sample"},
                "spec": {
                    "lifecycle": "active",
                    "owner": "Test",
                    "governance": {"human_approval_required": True},
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RegistryError, match="does not match"):
        load_project_registry(tmp_path)


def test_registry_schema_rejects_wrong_kind(tmp_path: Path) -> None:
    initialize_contract_root(tmp_path)
    (tmp_path / "registry" / "projects.yaml").write_text(
        yaml.safe_dump(
            {
                "api_version": "jdgf.io/v1alpha1",
                "kind": "NotAProjectRegistry",
                "projects": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RegistryError, match="project-registry.schema.yaml"):
        load_project_registry(tmp_path)


def test_project_schema_rejects_undeclared_fields(tmp_path: Path) -> None:
    initialize_contract_root(tmp_path)
    project_dir = tmp_path / "projects" / "sample"
    project_dir.mkdir()
    (tmp_path / "registry" / "projects.yaml").write_text(
        yaml.safe_dump(
            {
                "api_version": "jdgf.io/v1alpha1",
                "kind": "ProjectRegistry",
                "projects": [
                    {
                        "id": "sample-project",
                        "manifest": "projects/sample/project.yaml",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (project_dir / "project.yaml").write_text(
        yaml.safe_dump(
            {
                "api_version": "jdgf.io/v1alpha1",
                "kind": "Project",
                "metadata": {"id": "sample-project", "name": "Sample"},
                "spec": {
                    "lifecycle": "active",
                    "owner": "Test",
                    "governance": {"human_approval_required": "yes"},
                    "unexpected": True,
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RegistryError, match="project.schema.yaml"):
        load_project_registry(tmp_path)


def test_project_schema_rejects_non_boolean_approval(tmp_path: Path) -> None:
    manifest = tmp_path / "project.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "api_version": "jdgf.io/v1alpha1",
                "kind": "Project",
                "metadata": {"id": "sample-project", "name": "Sample"},
                "spec": {
                    "lifecycle": "active",
                    "owner": "Test",
                    "governance": {"human_approval_required": "yes"},
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RegistryError, match="human_approval_required"):
        validate_project_manifest(manifest, ROOT / "projects/project.schema.yaml")


def test_registry_rejects_manifest_outside_projects(tmp_path: Path) -> None:
    initialize_contract_root(tmp_path)
    manifest = tmp_path / "standalone.yaml"
    manifest.write_text("{}\n", encoding="utf-8")
    (tmp_path / "registry" / "projects.yaml").write_text(
        yaml.safe_dump(
            {
                "api_version": "jdgf.io/v1alpha1",
                "kind": "ProjectRegistry",
                "projects": [
                    {"id": "bad-project", "manifest": str(manifest)}
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RegistryError, match="under projects"):
        load_project_registry(tmp_path)
