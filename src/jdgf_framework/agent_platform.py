"""Agent Platform profile, registry and safety-policy validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
import yaml


@dataclass(frozen=True)
class AgentPlatformSummary:
    version: str
    lifecycle: str
    installable: bool
    agent_ids: tuple[str, ...]


class AgentPlatformError(ValueError):
    """Raised when agent declarations violate contracts or safety policy."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AgentPlatformError(f"Missing Agent Platform artifact: {path}") from exc
    except yaml.YAMLError as exc:
        raise AgentPlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise AgentPlatformError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise AgentPlatformError(f"Invalid schema in {schema_path}: {exc.message}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise AgentPlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def _resolve(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    agents_root = (root / "agents").resolve()
    if not path.is_relative_to(agents_root):
        raise AgentPlatformError(f"Agent manifest escapes agents directory: {relative}")
    if not path.is_file():
        raise AgentPlatformError(f"Agent manifest does not exist: {relative}")
    return path


def validate_agent_platform(root: Path) -> AgentPlatformSummary:
    """Validate agent profiles while keeping execution and tools disabled."""

    root = root.resolve()
    manifest_path = root / "manifests" / "agent-platform.yaml"
    registry_path = root / "registry" / "agents.yaml"
    profile_schema = root / "agents" / "agent.schema.yaml"
    manifest = _load_mapping(manifest_path)
    registry = _load_mapping(registry_path)
    _validate(
        manifest,
        root / "manifests" / "agent-platform.schema.yaml",
        manifest_path,
    )
    _validate(registry, root / "registry" / "agents.schema.yaml", registry_path)

    version = manifest["metadata"]["version"]
    if registry["metadata"]["version"] != version:
        raise AgentPlatformError("Agent manifest and registry versions differ")
    expected_components = {"profiles", "registry", "permissions", "routing", "memory"}
    if set(manifest["spec"]["components"]) != expected_components:
        raise AgentPlatformError("Agent Platform component set is incomplete")

    ai_registry = _load_mapping(root / "registry" / "ai-services.yaml")
    known_routes = {route["id"] for route in ai_registry["routing"]}
    entries = registry["agents"]
    agent_ids = [entry["id"] for entry in entries]
    if len(agent_ids) != len(set(agent_ids)):
        raise AgentPlatformError("Duplicate agent id")

    for entry in entries:
        path = _resolve(root, entry["manifest"])
        profile = _load_mapping(path)
        _validate(profile, profile_schema, path)
        metadata = profile["metadata"]
        spec = profile["spec"]
        if entry["id"] != metadata["id"]:
            raise AgentPlatformError(
                f"Agent registry id does not match profile: {entry['id']}"
            )
        if entry["version"] != metadata["version"]:
            raise AgentPlatformError(f"Agent version mismatch: {entry['id']}")
        if entry["lifecycle"] != metadata["lifecycle"]:
            raise AgentPlatformError(f"Agent lifecycle mismatch: {entry['id']}")
        if entry["enabled"] != spec["enabled"]:
            raise AgentPlatformError(f"Agent enabled state mismatch: {entry['id']}")
        if entry["route_ref"] != spec["route_ref"]:
            raise AgentPlatformError(f"Agent route mismatch: {entry['id']}")
        if spec["route_ref"] not in known_routes:
            raise AgentPlatformError(f"Agent references unknown route: {entry['id']}")
        if metadata["lifecycle"] != "active" and spec["enabled"]:
            raise AgentPlatformError(f"Non-active agent cannot be enabled: {entry['id']}")

        tools = spec["tools"]
        tool_ids = [tool["id"] for tool in tools]
        if len(tool_ids) != len(set(tool_ids)):
            raise AgentPlatformError(f"Duplicate tool declaration: {entry['id']}")
        if any(tool["enabled"] for tool in tools):
            raise AgentPlatformError(f"Agent tools must remain disabled: {entry['id']}")
        if any(store["enabled"] for store in spec["memory"].values()):
            raise AgentPlatformError(f"Agent memory must remain disabled: {entry['id']}")

        permissions = spec["permissions"]
        if (
            permissions["write"]
            or permissions["execute"]
            or permissions["delete"]
            or permissions["external_actions"]
        ):
            raise AgentPlatformError(
                f"Agent has consequential permissions before activation: {entry['id']}"
            )
        execution = spec["execution"]
        if (
            execution["unattended"]
            or execution["network_access"]
            or not execution["human_approval_required"]
        ):
            raise AgentPlatformError(f"Agent execution policy is unsafe: {entry['id']}")

    spec = manifest["spec"]
    if spec["installable"] and not (
        spec["lifecycle"] == "active"
        and spec["runtime_tested"]
        and all(entry["enabled"] for entry in entries)
    ):
        raise AgentPlatformError(
            "Agent Platform cannot be installable before runtime tests and activation"
        )

    return AgentPlatformSummary(
        version=version,
        lifecycle=spec["lifecycle"],
        installable=spec["installable"],
        agent_ids=tuple(agent_ids),
    )
