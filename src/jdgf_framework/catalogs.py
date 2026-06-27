"""Bootstrap manifest and registry catalog validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
import yaml


MANIFEST_FILES = ("framework.yaml", "modules.yaml", "projects.yaml")
REGISTRY_FILES = (
    "services.yaml",
    "models.yaml",
    "modules.yaml",
    "ports.yaml",
    "networks.yaml",
    "volumes.yaml",
)


@dataclass(frozen=True)
class CatalogSummary:
    manifest_count: int
    registry_count: int
    service_count: int


class CatalogError(ValueError):
    """Raised when a bootstrap catalog is invalid."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogError(f"Missing bootstrap catalog: {path}") from exc
    except yaml.YAMLError as exc:
        raise CatalogError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise CatalogError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise CatalogError(f"Invalid schema in {schema_path}: {exc.message}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise CatalogError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def _unique_ids(entries: list[dict[str, Any]], label: str) -> set[str]:
    identifiers = [entry["id"] for entry in entries]
    if len(identifiers) != len(set(identifiers)):
        raise CatalogError(f"Duplicate identifier in {label}")
    return set(identifiers)


def validate_bootstrap_catalogs(root: Path) -> CatalogSummary:
    """Validate bootstrap manifests, registries and their cross-references."""

    root = root.resolve()
    manifests = {
        name: _load_mapping(root / "manifests" / name) for name in MANIFEST_FILES
    }
    registries = {
        name: _load_mapping(root / "registry" / name) for name in REGISTRY_FILES
    }
    for name, document in manifests.items():
        _validate(
            document,
            root / "manifests" / "bootstrap.schema.yaml",
            root / "manifests" / name,
        )
    for name, document in registries.items():
        _validate(
            document,
            root / "registry" / "bootstrap-catalog.schema.yaml",
            root / "registry" / name,
        )

    manifest_modules = {
        entry["id"]: entry["lifecycle"]
        for entry in manifests["modules.yaml"]["modules"]
    }
    registry_modules = {
        entry["id"]: entry["lifecycle"]
        for entry in registries["modules.yaml"]["modules"]
    }
    if manifest_modules != registry_modules:
        raise CatalogError("Module manifest and registry do not match")

    active_capabilities = set(
        manifests["framework.yaml"]["spec"]["active_capabilities"]
    )
    if not active_capabilities.issubset(manifest_modules):
        raise CatalogError("Framework declares an unknown active capability")

    project_registry = root / manifests["projects.yaml"]["registry"]
    if not project_registry.is_file():
        raise CatalogError("Project registry reference is missing")

    services = registries["services.yaml"]["services"]
    service_ids = _unique_ids(services, "service registry")
    for service in services:
        if service["lifecycle"] != "active" and service["enabled"]:
            raise CatalogError(f"Deferred service cannot be enabled: {service['id']}")

    ports = registries["ports.yaml"]["ports"]
    port_numbers = [entry["port"] for entry in ports]
    if len(port_numbers) != len(set(port_numbers)):
        raise CatalogError("Duplicate port reservation")
    unknown_services = {entry["service"] for entry in ports} - service_ids
    if unknown_services:
        raise CatalogError(
            "Port registry references unknown services: "
            + ", ".join(sorted(unknown_services))
        )

    _unique_ids(registries["models.yaml"]["categories"], "model registry")
    _unique_ids(registries["networks.yaml"]["networks"], "network registry")
    _unique_ids(registries["volumes.yaml"]["volumes"], "volume registry")

    return CatalogSummary(
        manifest_count=len(manifests),
        registry_count=len(registries),
        service_count=len(services),
    )
