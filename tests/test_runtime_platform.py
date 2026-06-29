import shutil
from pathlib import Path

import pytest
import yaml

from jdgf_framework.runtime_platform import (
    RuntimePlatformError,
    TaskRecord,
    transition_task,
    validate_runtime_platform,
)

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def _copy_contracts(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "runtime", tmp_path / "runtime")
    for relative in (
        "registry/runtime.yaml",
        "registry/runtime.schema.yaml",
        "manifests/runtime-platform.yaml",
        "manifests/runtime-platform.schema.yaml",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def test_runtime_platform_contracts_are_valid() -> None:
    summary = validate_runtime_platform(ROOT)

    assert summary.version == "0.9.3"
    assert summary.execution_enabled is False
    assert summary.active_components == ("lifecycle-controller",)


def test_task_can_reach_approval_with_explicit_reference() -> None:
    task = TaskRecord(id="task-one", owner="Owner", workflow_ref="research")
    task, _ = transition_task(task, "validated", actor="validator")
    task, _ = transition_task(task, "awaiting-approval", actor="controller")
    task, event = transition_task(
        task,
        "approved",
        actor="reviewer",
        approval_reference="decision-42",
    )

    assert task.state == "approved"
    assert event.previous_state == "awaiting-approval"
    assert event.approval_reference == "decision-42"


def test_approval_transition_requires_reference() -> None:
    task = TaskRecord(
        id="task-one",
        owner="Owner",
        workflow_ref="research",
        state="awaiting-approval",
    )

    with pytest.raises(RuntimePlatformError, match="Approval reference"):
        transition_task(task, "approved", actor="reviewer")


def test_execution_state_is_not_available() -> None:
    task = TaskRecord(
        id="task-one", owner="Owner", workflow_ref="research", state="approved"
    )

    with pytest.raises(RuntimePlatformError, match="not allowed"):
        transition_task(task, "executing", actor="executor")


def test_side_effecting_task_is_rejected() -> None:
    task = TaskRecord(
        id="task-one",
        owner="Owner",
        workflow_ref="research",
        side_effects=True,
    )

    with pytest.raises(RuntimePlatformError, match="side-effect free"):
        transition_task(task, "validated", actor="validator")


def test_invalid_task_identity_is_rejected() -> None:
    task = TaskRecord(id="../task", owner="Owner", workflow_ref="research")

    with pytest.raises(RuntimePlatformError, match="invalid"):
        transition_task(task, "validated", actor="validator")


def test_runtime_transition_policy_must_match_code(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "runtime" / "runtime.yaml"
    profile = _load(path)
    profile["spec"]["transitions"].pop()
    _write(path, profile)

    with pytest.raises(RuntimePlatformError, match="differs"):
        validate_runtime_platform(root)


def test_executor_cannot_be_enabled(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    schema_path = root / "registry" / "runtime.schema.yaml"
    schema = _load(schema_path)
    schema["properties"]["components"]["items"]["properties"]["enabled"] = {
        "type": "boolean"
    }
    _write(schema_path, schema)
    path = root / "registry" / "runtime.yaml"
    registry = _load(path)
    registry["components"][3]["enabled"] = True
    _write(path, registry)

    with pytest.raises(RuntimePlatformError, match="Only the lifecycle"):
        validate_runtime_platform(root)
