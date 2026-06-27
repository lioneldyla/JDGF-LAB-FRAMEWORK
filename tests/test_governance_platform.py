from pathlib import Path
import shutil

import pytest
import yaml

from jdgf_framework.governance_platform import (
    GovernancePlatformError,
    validate_governance_platform,
)


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def _copy_contracts(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "governance", tmp_path / "governance")
    for relative in (
        "manifests/governance-platform.yaml",
        "manifests/governance-platform.schema.yaml",
        "registry/governance.yaml",
        "registry/governance.schema.yaml",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    for policy_path in (tmp_path / "governance" / "policies").glob("*.yaml"):
        policy = _load(policy_path)
        for rule in policy["spec"]["rules"]:
            for relative in rule["evidence"]:
                target = tmp_path / relative
                if relative == "tests":
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.touch(exist_ok=True)
    return tmp_path


def test_governance_platform_contracts_are_valid() -> None:
    summary = validate_governance_platform(ROOT)

    assert summary.version == "0.5.0"
    assert summary.lifecycle == "specified"
    assert summary.installable is False
    assert len(summary.policy_ids) == 9
    assert summary.implemented_rule_count == 12


def test_policy_schema_rejects_unknown_fields(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "governance" / "policies" / "security.yaml"
    policy = _load(path)
    policy["spec"]["certified"] = True
    _write(path, policy)

    with pytest.raises(GovernancePlatformError, match="Additional properties"):
        validate_governance_platform(root)


def test_implemented_rule_requires_evidence(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "governance" / "policies" / "quality.yaml"
    policy = _load(path)
    policy["spec"]["rules"][0]["evidence"] = []
    _write(path, policy)

    with pytest.raises(GovernancePlatformError, match="lacks evidence"):
        validate_governance_platform(root)


def test_unimplemented_rule_cannot_claim_evidence(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "governance" / "policies" / "backup.yaml"
    policy = _load(path)
    policy["spec"]["rules"][0]["evidence"] = ["README.md"]
    _write(path, policy)

    with pytest.raises(GovernancePlatformError, match="cannot claim evidence"):
        validate_governance_platform(root)


def test_runtime_rule_cannot_claim_implementation(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "governance" / "policies" / "backup.yaml"
    policy = _load(path)
    policy["spec"]["rules"][0]["implemented"] = True
    policy["spec"]["rules"][0]["evidence"] = ["README.md"]
    _write(path, policy)
    (root / "README.md").touch()

    with pytest.raises(GovernancePlatformError, match="Runtime governance rule"):
        validate_governance_platform(root)


def test_evidence_path_must_exist(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "governance" / "policies" / "quality.yaml"
    policy = _load(path)
    policy["spec"]["rules"][0]["evidence"] = ["missing/evidence.txt"]
    _write(path, policy)

    with pytest.raises(GovernancePlatformError, match="evidence does not exist"):
        validate_governance_platform(root)


def test_policy_enforcement_must_remain_disabled(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "registry" / "governance.yaml"
    registry = _load(path)
    registry["policies"][0]["enabled"] = True
    _write(path, registry)

    with pytest.raises(GovernancePlatformError, match="must remain disabled"):
        validate_governance_platform(root)


def test_policy_status_must_match_registry(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "registry" / "governance.yaml"
    registry = _load(path)
    registry["policies"][0]["status"] = "draft"
    _write(path, registry)

    with pytest.raises(GovernancePlatformError, match="status mismatch"):
        validate_governance_platform(root)


def test_observer_role_is_read_only(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "governance" / "policies" / "access-control.yaml"
    policy = _load(path)
    policy["spec"]["parameters"]["roles"][-1]["permissions"].append("write")
    _write(path, policy)

    with pytest.raises(GovernancePlatformError, match="Observer role"):
        validate_governance_platform(root)


def test_installable_requires_real_enforcement(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "manifests" / "governance-platform.yaml"
    manifest = _load(path)
    manifest["spec"]["installable"] = True
    _write(path, manifest)

    with pytest.raises(GovernancePlatformError, match="runtime tests"):
        validate_governance_platform(root)
