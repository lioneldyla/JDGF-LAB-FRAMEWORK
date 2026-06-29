"""Validation-only task lifecycle control; no agent execution is provided."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

TRANSITIONS = {
    ("proposed", "validated"): False,
    ("proposed", "cancelled"): False,
    ("validated", "awaiting-approval"): False,
    ("validated", "cancelled"): False,
    ("awaiting-approval", "approved"): True,
    ("awaiting-approval", "cancelled"): False,
    ("approved", "cancelled"): False,
}
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{2,62}$")


@dataclass(frozen=True)
class TaskRecord:
    id: str
    owner: str
    workflow_ref: str
    state: str = "proposed"
    side_effects: bool = False
    approval_required: bool = True


@dataclass(frozen=True)
class TransitionEvent:
    task_id: str
    previous_state: str
    state: str
    actor: str
    approval_reference: str | None


@dataclass(frozen=True)
class RuntimePlatformSummary:
    version: str
    execution_enabled: bool
    active_components: tuple[str, ...]


class RuntimePlatformError(ValueError):
    """Raised when runtime control contracts or transitions are unsafe."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimePlatformError(f"Missing file: {path}") from exc
    except yaml.YAMLError as exc:
        raise RuntimePlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise RuntimePlatformError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise RuntimePlatformError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise RuntimePlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def _check_schema(path: Path) -> None:
    schema = _load_mapping(path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise RuntimePlatformError(f"Invalid schema in {path}: {exc.message}") from exc


def validate_runtime_platform(root: Path) -> RuntimePlatformSummary:
    """Validate that control exists without implying multi-agent execution."""

    root = root.resolve()
    profile_path = root / "runtime" / "runtime.yaml"
    registry_path = root / "registry" / "runtime.yaml"
    manifest_path = root / "manifests" / "runtime-platform.yaml"
    profile = _load_mapping(profile_path)
    registry = _load_mapping(registry_path)
    manifest = _load_mapping(manifest_path)
    _validate(profile, root / "runtime" / "runtime.schema.yaml", profile_path)
    _validate(registry, root / "registry" / "runtime.schema.yaml", registry_path)
    _validate(
        manifest,
        root / "manifests" / "runtime-platform.schema.yaml",
        manifest_path,
    )
    _check_schema(root / "runtime" / "task.schema.yaml")
    _check_schema(root / "runtime" / "event.schema.yaml")
    versions = {
        profile["metadata"]["version"],
        registry["metadata"]["version"],
        manifest["metadata"]["version"],
    }
    if len(versions) != 1:
        raise RuntimePlatformError("Runtime Platform versions do not match")
    declared_transitions = {
        (item["from"], item["to"]): item["approval_required"]
        for item in profile["spec"]["transitions"]
    }
    if declared_transitions != TRANSITIONS:
        raise RuntimePlatformError(
            "Runtime transition policy differs from implementation"
        )
    components = {item["id"]: item for item in registry["components"]}
    active = tuple(sorted(key for key, value in components.items() if value["enabled"]))
    if active != ("lifecycle-controller",):
        raise RuntimePlatformError("Only the lifecycle controller may be enabled")
    if any(
        value["lifecycle"] != "deferred"
        for key, value in components.items()
        if key != "lifecycle-controller"
    ):
        raise RuntimePlatformError("Execution components must remain deferred")
    if set(active) != set(manifest["spec"]["active_components"]):
        raise RuntimePlatformError("Runtime active component declarations differ")
    if profile["spec"]["execution_enabled"] or manifest["spec"]["execution_enabled"]:
        raise RuntimePlatformError("Multi-agent execution must remain disabled")
    return RuntimePlatformSummary(
        version=versions.pop(),
        execution_enabled=False,
        active_components=active,
    )


def transition_task(
    task: TaskRecord,
    target_state: str,
    *,
    actor: str,
    approval_reference: str | None = None,
) -> tuple[TaskRecord, TransitionEvent]:
    """Apply one allowed, side-effect-free lifecycle transition."""

    if not actor.strip():
        raise RuntimePlatformError("Transition actor is required")
    if not IDENTIFIER.fullmatch(task.id) or not IDENTIFIER.fullmatch(task.workflow_ref):
        raise RuntimePlatformError("Task id and workflow reference are invalid")
    if not task.owner.strip():
        raise RuntimePlatformError("Task owner is required")
    if task.side_effects or not task.approval_required:
        raise RuntimePlatformError(
            "Runtime tasks must remain side-effect free and gated"
        )
    approval_required = TRANSITIONS.get((task.state, target_state))
    if approval_required is None:
        raise RuntimePlatformError(
            f"Transition is not allowed: {task.state} -> {target_state}"
        )
    if approval_required and not (approval_reference and approval_reference.strip()):
        raise RuntimePlatformError("Approval reference is required")
    if not approval_required and approval_reference is not None:
        raise RuntimePlatformError(
            "Approval reference is not valid for this transition"
        )
    updated = replace(task, state=target_state)
    event = TransitionEvent(
        task_id=task.id,
        previous_state=task.state,
        state=target_state,
        actor=actor.strip(),
        approval_reference=approval_reference.strip() if approval_reference else None,
    )
    return updated, event
