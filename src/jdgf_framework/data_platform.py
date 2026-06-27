"""Data platform manifest, registry and security-policy validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
import yaml


@dataclass(frozen=True)
class DataPlatformSummary:
    version: str
    lifecycle: str
    installable: bool
    service_ids: tuple[str, ...]


class DataPlatformError(ValueError):
    """Raised when data-platform contracts are invalid or inconsistent."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DataPlatformError(f"Missing data platform artifact: {path}") from exc
    except yaml.YAMLError as exc:
        raise DataPlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise DataPlatformError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise DataPlatformError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise DataPlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def validate_data_platform(root: Path) -> DataPlatformSummary:
    """Validate data-service declarations and conservative activation gates."""

    root = root.resolve()
    manifest_path = root / "manifests" / "database-platform.yaml"
    registry_path = root / "registry" / "database-services.yaml"
    manifest = _load_mapping(manifest_path)
    registry = _load_mapping(registry_path)
    _validate(
        manifest,
        root / "manifests" / "database-platform.schema.yaml",
        manifest_path,
    )
    _validate(
        registry,
        root / "registry" / "database-services.schema.yaml",
        registry_path,
    )

    services = registry["services"]
    service_ids = [service["id"] for service in services]
    if len(service_ids) != len(set(service_ids)):
        raise DataPlatformError("Duplicate database service id")
    if set(manifest["spec"]["components"]) != set(service_ids):
        raise DataPlatformError("Data platform components do not match its registry")

    known_services = set(service_ids)
    for service in services:
        missing = set(service["dependencies"]) - known_services
        if missing:
            raise DataPlatformError(
                f"Database service {service['id']} references unknown dependencies: "
                + ", ".join(sorted(missing))
            )
        if service["lifecycle"] != "active" and service["enabled"]:
            raise DataPlatformError(
                f"Non-active database service cannot be enabled: {service['id']}"
            )

    service_catalog = _load_mapping(root / "registry" / "services.yaml")
    catalog_states = {
        service["id"]: (service["lifecycle"], service["enabled"])
        for service in service_catalog["services"]
    }
    for service in services:
        expected = (service["lifecycle"], service["enabled"])
        if catalog_states.get(service["id"]) != expected:
            raise DataPlatformError(
                f"Database service catalog mismatch for {service['id']}"
            )

    services_by_id = {service["id"]: service for service in services}
    expected_types = {
        "default_sql": "relational",
        "default_graph": "graph",
        "default_vector": "vector",
        "default_cache": "cache",
    }
    for connection, expected_type in expected_types.items():
        service_id = registry["connections"][connection]
        service = services_by_id.get(service_id)
        if service is None:
            raise DataPlatformError(
                f"Database connection {connection} references unknown service: {service_id}"
            )
        if service["type"] != expected_type:
            raise DataPlatformError(
                f"Database connection {connection} requires type {expected_type}"
            )

    postgres_config = (
        root / "infrastructure" / "postgres" / "config" / "postgresql.conf"
    ).read_text(encoding="utf-8")
    if "password_encryption = 'scram-sha-256'" not in postgres_config:
        raise DataPlatformError("PostgreSQL must use SCRAM-SHA-256 password storage")

    redis_compose = (root / "infrastructure" / "redis" / "compose.yaml").read_text(
        encoding="utf-8"
    )
    if "--requirepass" not in redis_compose:
        raise DataPlatformError("Redis authentication must be enabled")

    qdrant = _load_mapping(root / "infrastructure" / "qdrant" / "compose.yaml")
    qdrant_environment = qdrant["services"]["qdrant"]["environment"]
    if not qdrant_environment.get("QDRANT__SERVICE__API_KEY"):
        raise DataPlatformError("Qdrant API-key authentication must be configured")
    if qdrant_environment.get("QDRANT__SERVICE__ENABLE_CORS") != "false":
        raise DataPlatformError("Qdrant CORS must be disabled by default")

    spec = manifest["spec"]
    all_enabled = all(service["enabled"] for service in services)
    all_active = all(service["lifecycle"] == "active" for service in services)
    if spec["installable"] and not (
        spec["runtime_tested"]
        and spec["backup"]["runtime_tested"]
        and spec["healthchecks"]["configured"]
        and all_enabled
        and all_active
    ):
        raise DataPlatformError(
            "Data platform cannot be installable before runtime, restore and activation checks"
        )

    return DataPlatformSummary(
        version=manifest["metadata"]["version"],
        lifecycle=spec["lifecycle"],
        installable=spec["installable"],
        service_ids=tuple(service_ids),
    )
