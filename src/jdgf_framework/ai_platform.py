"""AI platform manifest, registry and policy validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
import yaml


@dataclass(frozen=True)
class AiPlatformSummary:
    version: str
    lifecycle: str
    installable: bool
    service_ids: tuple[str, ...]
    route_ids: tuple[str, ...]


class AiPlatformError(ValueError):
    """Raised when AI platform contracts are inconsistent."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AiPlatformError(f"Missing AI platform artifact: {path}") from exc
    except yaml.YAMLError as exc:
        raise AiPlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise AiPlatformError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise AiPlatformError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise AiPlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def validate_ai_platform(root: Path) -> AiPlatformSummary:
    """Validate AI platform declarations and security policy invariants."""

    root = root.resolve()
    manifest_path = root / "manifests" / "ai-platform.yaml"
    registry_path = root / "registry" / "ai-services.yaml"
    manifest = _load_mapping(manifest_path)
    registry = _load_mapping(registry_path)
    _validate(manifest, root / "manifests" / "ai-platform.schema.yaml", manifest_path)
    _validate(registry, root / "registry" / "ai-services.schema.yaml", registry_path)

    services = registry["services"]
    service_ids = [service["id"] for service in services]
    if len(service_ids) != len(set(service_ids)):
        raise AiPlatformError("Duplicate AI service id")
    if set(manifest["spec"]["components"]) != set(service_ids):
        raise AiPlatformError("AI platform components do not match its registry")

    known_services = set(service_ids)
    for service in services:
        missing = set(service["dependencies"]) - known_services
        if missing:
            raise AiPlatformError(
                f"AI service {service['id']} references unknown dependencies: "
                + ", ".join(sorted(missing))
            )
        if service["lifecycle"] != "active" and service["enabled"]:
            raise AiPlatformError(
                f"Non-active AI service cannot be enabled: {service['id']}"
            )

    service_catalog = _load_mapping(root / "registry" / "services.yaml")
    catalog_states = {
        service["id"]: (service["lifecycle"], service["enabled"])
        for service in service_catalog["services"]
    }
    for service in services:
        if catalog_states.get(service["id"]) != (
            service["lifecycle"],
            service["enabled"],
        ):
            raise AiPlatformError(f"AI service catalog mismatch for {service['id']}")

    litellm_config = _load_mapping(
        root / "infrastructure" / "litellm" / "config" / "config.yaml"
    )
    model_aliases = {route["model_name"] for route in litellm_config["model_list"]}
    route_ids: list[str] = []
    for route in registry["routing"]:
        if route["id"] in route_ids:
            raise AiPlatformError(f"Duplicate AI route id: {route['id']}")
        if route["model_alias"] not in model_aliases:
            raise AiPlatformError(
                f"AI route references unknown model alias: {route['model_alias']}"
            )
        route_ids.append(route["id"])

    open_webui_policy = _load_mapping(
        root / "infrastructure" / "open-webui" / "config" / "config.yaml"
    )
    if open_webui_policy["spec"]["access"]["registration"]:
        raise AiPlatformError("Open WebUI registration must be disabled by default")
    if open_webui_policy["spec"]["features"]["web_search"]:
        raise AiPlatformError("Open WebUI web search must be disabled by default")

    openhands_policy = _load_mapping(
        root / "infrastructure" / "openhands" / "config" / "config.yaml"
    )
    security = openhands_policy["spec"]["security"]
    if not security["confirm_destructive_actions"]:
        raise AiPlatformError("OpenHands destructive actions require confirmation")
    if security["unattended_execution"]:
        raise AiPlatformError("OpenHands unattended execution must be disabled")

    spec = manifest["spec"]
    if spec["installable"] and (
        not spec["runtime_tested"]
        or not all(service["enabled"] for service in services)
    ):
        raise AiPlatformError(
            "AI platform cannot be installable before runtime tests and activation"
        )

    return AiPlatformSummary(
        version=manifest["metadata"]["version"],
        lifecycle=spec["lifecycle"],
        installable=spec["installable"],
        service_ids=tuple(service_ids),
        route_ids=tuple(route_ids),
    )
