import shutil
from pathlib import Path

import pytest
import yaml

from jdgf_framework.orchestration_platform import (
    OrchestrationPlatformError,
    validate_orchestration_platform,
)

ROOT = Path(__file__).resolve().parents[1]


def _copy_contracts(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "orchestration", tmp_path / "orchestration")
    for relative in (
        "manifests/orchestration-platform.yaml",
        "manifests/orchestration-platform.schema.yaml",
        "registry/orchestrators.yaml",
        "registry/orchestrators.schema.yaml",
        "registry/workflows.yaml",
        "registry/workflows.schema.yaml",
        "registry/agents.yaml",
        "registry/ai-services.yaml",
        "registry/services.yaml",
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


def test_orchestration_platform_contracts_are_valid() -> None:
    summary = validate_orchestration_platform(ROOT)

    assert summary.version == "0.4.0"
    assert summary.lifecycle == "specified"
    assert summary.installable is False
    assert summary.orchestrator_ids == ("master-orchestrator",)
    assert set(summary.workflow_ids) == {
        "research",
        "framework",
        "publication",
        "rag",
        "project",
    }


def test_orchestrator_schema_rejects_unknown_fields(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "orchestration" / "orchestrator.yaml"
    orchestrator = _load(path)
    orchestrator["spec"]["auto_execute"] = True
    _write(path, orchestrator)

    with pytest.raises(OrchestrationPlatformError, match="Additional properties"):
        validate_orchestration_platform(root)


def test_route_must_remain_disabled(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "orchestration" / "router.yaml"
    router = _load(path)
    router["routes"][0]["enabled"] = True
    _write(path, router)

    with pytest.raises(OrchestrationPlatformError, match="route must remain disabled"):
        validate_orchestration_platform(root)


def test_route_must_reference_registered_ai_alias(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "registry" / "ai-services.yaml"
    registry = _load(path)
    registry["routing"] = [
        route for route in registry["routing"] if route["id"] != "reasoning"
    ]
    _write(path, registry)

    with pytest.raises(OrchestrationPlatformError, match="unknown AI route"):
        validate_orchestration_platform(root)


def test_workflow_dependency_must_precede_step(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "orchestration" / "workflows" / "research.yaml"
    workflow = _load(path)
    workflow["spec"]["steps"][0]["dependencies"] = ["approve"]
    _write(path, workflow)

    with pytest.raises(OrchestrationPlatformError, match="unavailable dependencies"):
        validate_orchestration_platform(root)


def test_workflow_agent_must_exist(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "orchestration" / "workflows" / "research.yaml"
    workflow = _load(path)
    workflow["spec"]["steps"][0]["handler"] = "agent:missing-agent"
    _write(path, workflow)

    with pytest.raises(OrchestrationPlatformError, match="unknown agent"):
        validate_orchestration_platform(root)


def test_workflow_requires_human_gate(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "orchestration" / "workflows" / "project.yaml"
    workflow = _load(path)
    workflow["spec"]["steps"][-1]["handler"] = "internal:approval-check"
    _write(path, workflow)

    with pytest.raises(OrchestrationPlatformError, match="lacks a human"):
        validate_orchestration_platform(root)


def test_workflow_side_effects_are_forbidden(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "orchestration" / "workflows" / "framework.yaml"
    workflow = _load(path)
    workflow["spec"]["side_effects"] = True
    _write(path, workflow)

    with pytest.raises(OrchestrationPlatformError, match="unsafe foundation mode"):
        validate_orchestration_platform(root)


def test_installable_requires_runtime_evidence(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "manifests" / "orchestration-platform.yaml"
    manifest = _load(path)
    manifest["spec"]["installable"] = True
    _write(path, manifest)

    with pytest.raises(OrchestrationPlatformError, match="runtime tests"):
        validate_orchestration_platform(root)
