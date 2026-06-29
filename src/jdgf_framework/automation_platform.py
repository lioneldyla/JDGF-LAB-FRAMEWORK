"""Automation and monitoring platform contract validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


@dataclass(frozen=True)
class AutomationPlatformSummary:
    version: str
    lifecycle: str
    installable: bool
    service_ids: tuple[str, ...]


class AutomationPlatformError(ValueError):
    """Raised when automation or monitoring contracts are inconsistent."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AutomationPlatformError(f"Missing automation artifact: {path}") from exc
    except yaml.YAMLError as exc:
        raise AutomationPlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise AutomationPlatformError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise AutomationPlatformError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise AutomationPlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def _assert_blank_example_secret(root: Path, relative: str, key: str) -> None:
    values = dict(
        line.split("=", 1)
        for line in (root / relative).read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and "=" in line
    )
    if values.get(key) != "":
        raise AutomationPlatformError(f"Example secret must be blank: {key}")


def validate_automation_platform(root: Path) -> AutomationPlatformSummary:
    """Validate orchestration, search and observability declarations."""

    root = root.resolve()
    manifest_path = root / "manifests" / "automation-platform.yaml"
    registry_path = root / "registry" / "automation.yaml"
    manifest = _load_mapping(manifest_path)
    registry = _load_mapping(registry_path)
    _validate(
        manifest,
        root / "manifests" / "automation-platform.schema.yaml",
        manifest_path,
    )
    _validate(registry, root / "registry" / "automation.schema.yaml", registry_path)

    services = registry["services"]
    service_ids = [service["id"] for service in services]
    if len(service_ids) != len(set(service_ids)):
        raise AutomationPlatformError("Duplicate automation service id")
    if set(manifest["spec"]["components"]) != set(service_ids):
        raise AutomationPlatformError(
            "Automation platform components do not match its registry"
        )

    service_catalog = _load_mapping(root / "registry" / "services.yaml")
    catalog_states = {
        service["id"]: (service["lifecycle"], service["enabled"])
        for service in service_catalog["services"]
    }
    known_services = set(catalog_states)
    for service in services:
        missing = set(service["dependencies"]) - known_services
        if missing:
            raise AutomationPlatformError(
                f"Automation service {service['id']} references unknown dependencies: "
                + ", ".join(sorted(missing))
            )
        if service["lifecycle"] != "active" and service["enabled"]:
            raise AutomationPlatformError(
                f"Non-active automation service cannot be enabled: {service['id']}"
            )
        expected = (service["lifecycle"], service["enabled"])
        if catalog_states.get(service["id"]) != expected:
            raise AutomationPlatformError(
                f"Automation service catalog mismatch for {service['id']}"
            )

    for relative, key in (
        ("infrastructure/n8n/.env.example", "N8N_ENCRYPTION_KEY"),
        ("infrastructure/n8n/.env.example", "N8N_DB_PASSWORD"),
        ("infrastructure/n8n/.env.example", "N8N_REDIS_PASSWORD"),
        ("infrastructure/searxng/.env.example", "SEARXNG_SECRET"),
        (
            "infrastructure/monitoring/grafana/.env.example",
            "GRAFANA_ADMIN_PASSWORD",
        ),
    ):
        _assert_blank_example_secret(root, relative, key)

    n8n = _load_mapping(root / "infrastructure" / "n8n" / "compose.yaml")
    n8n_environment = n8n["services"]["n8n"]["environment"]
    if n8n_environment.get("N8N_BLOCK_ENV_ACCESS_IN_NODE") != "true":
        raise AutomationPlatformError(
            "n8n code-node environment access must be blocked"
        )
    if n8n_environment.get("N8N_DIAGNOSTICS_ENABLED") != "false":
        raise AutomationPlatformError("n8n diagnostics must be disabled by default")

    searxng = _load_mapping(
        root / "infrastructure" / "searxng" / "config" / "settings.yml"
    )
    if not searxng["server"]["limiter"]:
        raise AutomationPlatformError("SearXNG limiter must be enabled")
    if searxng["server"]["public_instance"]:
        raise AutomationPlatformError("SearXNG must not be public by default")

    grafana = _load_mapping(
        root / "infrastructure" / "monitoring" / "grafana" / "compose.yaml"
    )
    grafana_environment = grafana["services"]["grafana"]["environment"]
    if grafana_environment.get("GF_AUTH_ANONYMOUS_ENABLED") != "false":
        raise AutomationPlatformError("Grafana anonymous access must be disabled")

    prometheus = _load_mapping(
        root / "infrastructure" / "monitoring" / "prometheus" / "prometheus.yml"
    )
    jobs = {job["job_name"] for job in prometheus["scrape_configs"]}
    if jobs != {"prometheus", "loki", "n8n"}:
        raise AutomationPlatformError("Prometheus scrape jobs are not the approved set")

    spec = manifest["spec"]
    all_enabled = all(service["enabled"] for service in services)
    all_active = all(service["lifecycle"] == "active" for service in services)
    if spec["installable"] and not (
        spec["runtime_tested"] and all_enabled and all_active
    ):
        raise AutomationPlatformError(
            "Automation platform cannot be installable before runtime tests and activation"
        )

    return AutomationPlatformSummary(
        version=manifest["metadata"]["version"],
        lifecycle=spec["lifecycle"],
        installable=spec["installable"],
        service_ids=tuple(service_ids),
    )
