import shutil
from pathlib import Path

import pytest
import yaml

from jdgf_framework.ai_platform import AiPlatformError, validate_ai_platform

ROOT = Path(__file__).resolve().parents[1]


def copy_ai_contracts(target: Path) -> None:
    for directory in ("infrastructure", "manifests", "registry"):
        shutil.copytree(ROOT / directory, target / directory)


def test_repository_ai_platform_is_valid() -> None:
    summary = validate_ai_platform(ROOT)

    assert summary.version == "0.2.0"
    assert summary.lifecycle == "specified"
    assert summary.installable is False
    assert set(summary.service_ids) == {"ollama", "litellm", "open-webui", "openhands"}
    assert set(summary.route_ids) == {"default-chat", "coding", "reasoning"}


def test_unknown_model_alias_is_rejected(tmp_path: Path) -> None:
    copy_ai_contracts(tmp_path)
    registry_path = tmp_path / "registry" / "ai-services.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["routing"][0]["model_alias"] = "missing-model"
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")

    with pytest.raises(AiPlatformError, match="unknown model alias"):
        validate_ai_platform(tmp_path)


def test_non_active_service_cannot_be_enabled(tmp_path: Path) -> None:
    copy_ai_contracts(tmp_path)
    registry_path = tmp_path / "registry" / "ai-services.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["services"][0]["enabled"] = True
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")

    with pytest.raises(AiPlatformError, match="cannot be enabled"):
        validate_ai_platform(tmp_path)


def test_openhands_unattended_execution_is_rejected(tmp_path: Path) -> None:
    copy_ai_contracts(tmp_path)
    policy_path = tmp_path / "infrastructure" / "openhands" / "config" / "config.yaml"
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    policy["spec"]["security"]["unattended_execution"] = True
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")

    with pytest.raises(AiPlatformError, match="unattended execution"):
        validate_ai_platform(tmp_path)
