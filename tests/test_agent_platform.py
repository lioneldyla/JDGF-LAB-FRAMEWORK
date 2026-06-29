import shutil
from pathlib import Path

import pytest
import yaml

from jdgf_framework.agent_platform import AgentPlatformError, validate_agent_platform

ROOT = Path(__file__).resolve().parents[1]


def _copy_contracts(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "agents", tmp_path / "agents")
    for relative in (
        "manifests/agent-platform.yaml",
        "manifests/agent-platform.schema.yaml",
        "manifests/framework.yaml",
        "registry/agents.yaml",
        "registry/agents.schema.yaml",
        "registry/ai-services.yaml",
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


def test_agent_platform_contracts_are_valid() -> None:
    summary = validate_agent_platform(ROOT)

    assert summary.version == "0.3.0"
    assert summary.lifecycle == "specified"
    assert summary.installable is False
    assert len(summary.agent_ids) == 6


def test_agent_schema_rejects_unknown_fields(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    profile_path = root / "agents" / "jdgf_architect" / "agent.yaml"
    profile = _load(profile_path)
    profile["spec"]["autonomous"] = True
    _write(profile_path, profile)

    with pytest.raises(AgentPlatformError, match="Additional properties"):
        validate_agent_platform(root)


def test_agent_registry_and_profile_state_must_match(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    profile_path = root / "agents" / "jdgf_architect" / "agent.yaml"
    profile = _load(profile_path)
    profile["spec"]["enabled"] = True
    _write(profile_path, profile)

    with pytest.raises(AgentPlatformError, match="enabled state mismatch"):
        validate_agent_platform(root)


def test_non_active_agent_cannot_be_enabled(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    registry_path = root / "registry" / "agents.yaml"
    registry = _load(registry_path)
    registry["agents"][0]["enabled"] = True
    _write(registry_path, registry)
    profile_path = root / "agents" / "jdgf_architect" / "agent.yaml"
    profile = _load(profile_path)
    profile["spec"]["enabled"] = True
    _write(profile_path, profile)

    with pytest.raises(AgentPlatformError, match="Non-active agent"):
        validate_agent_platform(root)


def test_agent_tool_cannot_be_enabled_before_runtime(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    profile_path = root / "agents" / "coding_agent" / "agent.yaml"
    profile = _load(profile_path)
    profile["spec"]["tools"][0]["enabled"] = True
    _write(profile_path, profile)

    with pytest.raises(AgentPlatformError, match="tools must remain disabled"):
        validate_agent_platform(root)


def test_agent_cannot_receive_write_permission(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    profile_path = root / "agents" / "coding_agent" / "agent.yaml"
    profile = _load(profile_path)
    profile["spec"]["permissions"]["write"] = ["repository"]
    _write(profile_path, profile)

    with pytest.raises(AgentPlatformError, match="consequential permissions"):
        validate_agent_platform(root)


def test_agent_cannot_execute_unattended(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    profile_path = root / "agents" / "coding_agent" / "agent.yaml"
    profile = _load(profile_path)
    profile["spec"]["execution"]["unattended"] = True
    _write(profile_path, profile)

    with pytest.raises(AgentPlatformError, match="execution policy is unsafe"):
        validate_agent_platform(root)


def test_agent_memory_must_remain_disabled(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    profile_path = root / "agents" / "research_architect" / "agent.yaml"
    profile = _load(profile_path)
    profile["spec"]["memory"]["short_term"]["enabled"] = True
    _write(profile_path, profile)

    with pytest.raises(AgentPlatformError, match="memory must remain disabled"):
        validate_agent_platform(root)


def test_installable_requires_runtime_evidence(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    manifest_path = root / "manifests" / "agent-platform.yaml"
    manifest = _load(manifest_path)
    manifest["spec"]["installable"] = True
    _write(manifest_path, manifest)

    with pytest.raises(AgentPlatformError, match="runtime tests"):
        validate_agent_platform(root)
