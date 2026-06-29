"""Orchestration Platform contract and safety-invariant validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


@dataclass(frozen=True)
class OrchestrationPlatformSummary:
    version: str
    lifecycle: str
    installable: bool
    orchestrator_ids: tuple[str, ...]
    workflow_ids: tuple[str, ...]


class OrchestrationPlatformError(ValueError):
    """Raised when orchestration contracts are invalid or unsafe."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OrchestrationPlatformError(
            f"Missing orchestration artifact: {path}"
        ) from exc
    except yaml.YAMLError as exc:
        raise OrchestrationPlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise OrchestrationPlatformError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise OrchestrationPlatformError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise OrchestrationPlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def _resolve(root: Path, relative: str, parent: str) -> Path:
    path = (root / relative).resolve()
    boundary = (root / parent).resolve()
    if not path.is_relative_to(boundary):
        raise OrchestrationPlatformError(
            f"Orchestration artifact escapes {parent}/: {relative}"
        )
    if not path.is_file():
        raise OrchestrationPlatformError(
            f"Orchestration artifact does not exist: {relative}"
        )
    return path


def validate_orchestration_platform(root: Path) -> OrchestrationPlatformSummary:
    """Validate routing and workflows while enforcing a disabled runtime."""

    root = root.resolve()
    manifest_path = root / "manifests" / "orchestration-platform.yaml"
    orchestrators_path = root / "registry" / "orchestrators.yaml"
    workflows_path = root / "registry" / "workflows.yaml"
    manifest = _load_mapping(manifest_path)
    orchestrators = _load_mapping(orchestrators_path)
    workflows = _load_mapping(workflows_path)
    _validate(
        manifest,
        root / "manifests" / "orchestration-platform.schema.yaml",
        manifest_path,
    )
    _validate(
        orchestrators,
        root / "registry" / "orchestrators.schema.yaml",
        orchestrators_path,
    )
    _validate(
        workflows,
        root / "registry" / "workflows.schema.yaml",
        workflows_path,
    )

    version = manifest["metadata"]["version"]
    if orchestrators["metadata"]["version"] != version:
        raise OrchestrationPlatformError("Orchestrator registry version mismatch")
    if workflows["metadata"]["version"] != version:
        raise OrchestrationPlatformError("Workflow registry version mismatch")
    expected_components = {
        "orchestrator",
        "router",
        "workflows",
        "routing",
        "human-gates",
        "audit",
    }
    if set(manifest["spec"]["components"]) != expected_components:
        raise OrchestrationPlatformError(
            "Orchestration Platform component set is incomplete"
        )

    router_path = _resolve(root, manifest["spec"]["router"], "orchestration")
    router = _load_mapping(router_path)
    _validate(router, root / "orchestration" / "router.schema.yaml", router_path)
    ai_registry = _load_mapping(root / "registry" / "ai-services.yaml")
    known_routes = {route["id"] for route in ai_registry["routing"]}
    route_intents = [route["intent"] for route in router["routes"]]
    if len(route_intents) != len(set(route_intents)):
        raise OrchestrationPlatformError("Duplicate orchestration route intent")
    for route in router["routes"]:
        if route["route_ref"] not in known_routes:
            raise OrchestrationPlatformError(
                f"Orchestration route references unknown AI route: {route['intent']}"
            )
        if route["enabled"]:
            raise OrchestrationPlatformError(
                f"Orchestration route must remain disabled: {route['intent']}"
            )
    if router["fallback"]["route_ref"] not in known_routes:
        raise OrchestrationPlatformError("Router fallback references unknown AI route")
    if router["fallback"]["enabled"]:
        raise OrchestrationPlatformError("Router fallback must remain disabled")

    agent_registry = _load_mapping(root / "registry" / "agents.yaml")
    agents = {entry["id"]: entry for entry in agent_registry["agents"]}
    service_registry = _load_mapping(root / "registry" / "services.yaml")
    services = {entry["id"]: entry for entry in service_registry["services"]}

    orchestrator_ids: list[str] = []
    for entry in orchestrators["orchestrators"]:
        if entry["id"] in orchestrator_ids:
            raise OrchestrationPlatformError("Duplicate orchestrator id")
        path = _resolve(root, entry["manifest"], "orchestration")
        orchestrator = _load_mapping(path)
        _validate(
            orchestrator,
            root / "orchestration" / "orchestrator.schema.yaml",
            path,
        )
        metadata = orchestrator["metadata"]
        spec = orchestrator["spec"]
        if entry["id"] != metadata["id"] or entry["version"] != metadata["version"]:
            raise OrchestrationPlatformError("Orchestrator registry/profile mismatch")
        if entry["lifecycle"] != metadata["lifecycle"]:
            raise OrchestrationPlatformError("Orchestrator lifecycle mismatch")
        if entry["enabled"] != spec["enabled"]:
            raise OrchestrationPlatformError("Orchestrator enabled state mismatch")
        if spec["enabled"]:
            raise OrchestrationPlatformError(
                "Orchestrator runtime must remain disabled"
            )
        for role, declaration in spec["roles"].items():
            agent = agents.get(declaration["agent_ref"])
            if agent is None:
                raise OrchestrationPlatformError(
                    f"Orchestrator role references unknown agent: {role}"
                )
            if declaration["enabled"] or agent["enabled"]:
                raise OrchestrationPlatformError(
                    f"Orchestrator role must remain disabled: {role}"
                )
        orchestrator_ids.append(entry["id"])

    workflow_ids: list[str] = []
    for entry in workflows["workflows"]:
        if entry["id"] in workflow_ids:
            raise OrchestrationPlatformError("Duplicate workflow id")
        path = _resolve(root, entry["manifest"], "orchestration/workflows")
        workflow = _load_mapping(path)
        _validate(workflow, root / "orchestration" / "workflow.schema.yaml", path)
        metadata = workflow["metadata"]
        spec = workflow["spec"]
        if entry["id"] != metadata["id"] or entry["version"] != metadata["version"]:
            raise OrchestrationPlatformError(
                f"Workflow registry/profile mismatch: {entry['id']}"
            )
        if entry["lifecycle"] != metadata["lifecycle"]:
            raise OrchestrationPlatformError(
                f"Workflow lifecycle mismatch: {entry['id']}"
            )
        if entry["enabled"] != spec["enabled"] or spec["enabled"]:
            raise OrchestrationPlatformError(
                f"Workflow must remain disabled: {entry['id']}"
            )
        if spec["mode"] != "sequential" or spec["side_effects"]:
            raise OrchestrationPlatformError(
                f"Workflow uses unsafe foundation mode: {entry['id']}"
            )

        step_ids = [step["id"] for step in spec["steps"]]
        if len(step_ids) != len(set(step_ids)):
            raise OrchestrationPlatformError(f"Duplicate workflow step: {entry['id']}")
        seen: set[str] = set()
        human_gate = False
        for step in spec["steps"]:
            unavailable = set(step["dependencies"]) - seen
            if unavailable:
                raise OrchestrationPlatformError(
                    f"Workflow step has unavailable dependencies: {entry['id']}/{step['id']}"
                )
            handler_type, handler_id = step["handler"].split(":", 1)
            if handler_type == "agent" and handler_id not in agents:
                raise OrchestrationPlatformError(
                    f"Workflow references unknown agent: {handler_id}"
                )
            if handler_type == "service" and handler_id not in services:
                raise OrchestrationPlatformError(
                    f"Workflow references unknown service: {handler_id}"
                )
            if handler_type == "human":
                human_gate = True
            seen.add(step["id"])
        if not human_gate:
            raise OrchestrationPlatformError(
                f"Workflow lacks a human approval gate: {entry['id']}"
            )
        workflow_ids.append(entry["id"])

    spec = manifest["spec"]
    execution_enabled = any(
        entry["enabled"] for entry in orchestrators["orchestrators"]
    ) or any(entry["enabled"] for entry in workflows["workflows"])
    if spec["execution_enabled"] != execution_enabled:
        raise OrchestrationPlatformError("Execution activation claim is inconsistent")
    if spec["agents_enabled"] != any(agent["enabled"] for agent in agents.values()):
        raise OrchestrationPlatformError("Agent activation claim is inconsistent")
    if spec["installable"] and not (
        spec["lifecycle"] == "active"
        and spec["runtime_tested"]
        and spec["execution_enabled"]
    ):
        raise OrchestrationPlatformError(
            "Orchestration Platform cannot be installable before runtime tests and activation"
        )

    return OrchestrationPlatformSummary(
        version=version,
        lifecycle=spec["lifecycle"],
        installable=spec["installable"],
        orchestrator_ids=tuple(orchestrator_ids),
        workflow_ids=tuple(workflow_ids),
    )
