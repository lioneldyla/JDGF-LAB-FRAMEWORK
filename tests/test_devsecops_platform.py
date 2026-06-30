from pathlib import Path
import shutil

import pytest
import yaml

from jdgf_framework.devsecops_platform import (
    DevSecOpsPlatformError,
    validate_devsecops_platform,
)


ROOT = Path(__file__).resolve().parents[1]


def _copy_contracts(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / ".github", tmp_path / ".github")
    shutil.copytree(ROOT / "devsecops", tmp_path / "devsecops")
    shutil.copytree(ROOT / "scripts" / "devsecops", tmp_path / "scripts" / "devsecops")
    for relative in (
        "pyproject.toml",
        "manifests/devsecops-platform.yaml",
        "manifests/devsecops-platform.schema.yaml",
        "registry/devsecops.yaml",
        "registry/devsecops.schema.yaml",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def _load_base(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def test_devsecops_platform_contracts_are_valid() -> None:
    summary = validate_devsecops_platform(ROOT)

    assert summary.version == "0.6.0"
    assert summary.lifecycle == "specified"
    assert summary.installable is False
    assert len(summary.workflow_ids) == 3
    assert set(summary.tool_ids) == {"uv", "pytest", "ruff", "pip-audit", "bash"}


def test_action_must_be_pinned_by_full_sha(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / ".github" / "workflows" / "ci.yml"
    workflow = _load_base(path)
    workflow["jobs"]["validate"]["steps"][0]["uses"] = "actions/checkout@v7"
    _write(path, workflow)

    with pytest.raises(DevSecOpsPlatformError, match="not pinned"):
        validate_devsecops_platform(root)


def test_workflow_permissions_must_be_read_only(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / ".github" / "workflows" / "ci.yml"
    workflow = _load_base(path)
    workflow["permissions"]["contents"] = "write"
    _write(path, workflow)

    with pytest.raises(DevSecOpsPlatformError, match="forbidden authority"):
        validate_devsecops_platform(root)


def test_checkout_credentials_must_not_persist(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / ".github" / "workflows" / "ci.yml"
    workflow = _load_base(path)
    workflow["jobs"]["validate"]["steps"][0]["with"]["persist-credentials"] = "true"
    _write(path, workflow)

    with pytest.raises(DevSecOpsPlatformError, match="must not persist"):
        validate_devsecops_platform(root)


def test_pull_request_target_is_forbidden(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / ".github" / "workflows" / "ci.yml"
    text = path.read_text(encoding="utf-8").replace(
        "  pull_request:\n", "  pull_request_target:\n"
    )
    path.write_text(text, encoding="utf-8")

    with pytest.raises(DevSecOpsPlatformError, match="forbidden authority"):
        validate_devsecops_platform(root)


def test_deployment_command_is_forbidden(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / ".github" / "workflows" / "release-candidate.yml"
    workflow = _load_base(path)
    workflow["jobs"]["build"]["steps"].append(
        {"name": "Deploy", "run": "kubectl apply -f deployment.yaml"}
    )
    _write(path, workflow)

    with pytest.raises(DevSecOpsPlatformError, match="forbidden authority"):
        validate_devsecops_platform(root)


def test_workflow_secret_expansion_is_forbidden(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / ".github" / "workflows" / "ci.yml"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "run: ./verify.sh",
            (
                "env:\n"
                "          API_KEY: ${{ secrets.API_KEY }}\n"
                "        run: ./verify.sh"
            ),
        ),
        encoding="utf-8",
    )

    with pytest.raises(DevSecOpsPlatformError, match="forbidden authority"):
        validate_devsecops_platform(root)


def test_scripts_cannot_suppress_failures(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "scripts" / "devsecops" / "security-scan.sh"
    path.write_text(
        path.read_text(encoding="utf-8") + "\nfalse || true\n", encoding="utf-8"
    )

    with pytest.raises(DevSecOpsPlatformError, match="suppresses failures"):
        validate_devsecops_platform(root)


def test_packaging_cannot_archive_repository(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "scripts" / "devsecops" / "package.sh"
    path.write_text(
        path.read_text(encoding="utf-8") + "\ntar -czf repo.tar.gz .\n",
        encoding="utf-8",
    )

    with pytest.raises(DevSecOpsPlatformError, match="project artifacts only"):
        validate_devsecops_platform(root)


def test_source_distribution_scope_is_minimal(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "pyproject.toml"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            '  "/src/jdgf_framework",', '  "/src/jdgf_framework",\n  "/scripts",'
        ),
        encoding="utf-8",
    )

    with pytest.raises(DevSecOpsPlatformError, match="include set is not minimal"):
        validate_devsecops_platform(root)


def test_registry_triggers_must_match_workflow(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "registry" / "devsecops.yaml"
    registry = yaml.safe_load(path.read_text(encoding="utf-8"))
    registry["workflows"][0]["triggers"].remove("workflow_dispatch")
    _write(path, registry)

    with pytest.raises(DevSecOpsPlatformError, match="triggers do not match"):
        validate_devsecops_platform(root)


def test_installable_requires_hosted_execution_evidence(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "manifests" / "devsecops-platform.yaml"
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    manifest["spec"]["installable"] = True
    _write(path, manifest)

    with pytest.raises(DevSecOpsPlatformError, match="hosted workflow tests"):
        validate_devsecops_platform(root)
