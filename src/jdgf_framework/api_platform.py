"""Contract validation for the loopback-only preview API."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi.routing import APIRoute
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
import yaml

from . import __version__
from .api import create_app


@dataclass(frozen=True)
class ApiPlatformSummary:
    version: str
    lifecycle: str
    endpoint_ids: tuple[str, ...]


class ApiPlatformError(ValueError):
    """Raised when API contracts diverge from the executable application."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ApiPlatformError(f"Missing file: {path}") from exc
    except yaml.YAMLError as exc:
        raise ApiPlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise ApiPlatformError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ApiPlatformError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise ApiPlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def validate_api_platform(root: Path) -> ApiPlatformSummary:
    """Cross-check API YAML contracts against generated FastAPI routes."""

    root = root.resolve()
    manifest_path = root / "manifests" / "api-platform.yaml"
    registry_path = root / "registry" / "api.yaml"
    manifest = _load_mapping(manifest_path)
    registry = _load_mapping(registry_path)
    _validate(manifest, root / "manifests" / "api-platform.schema.yaml", manifest_path)
    _validate(registry, root / "registry" / "api.schema.yaml", registry_path)
    versions = {
        manifest["metadata"]["version"],
        registry["metadata"]["version"],
        __version__,
    }
    if len(versions) != 1:
        raise ApiPlatformError("API contract and package versions do not match")

    entries = registry["endpoints"]
    endpoint_ids = [entry["id"] for entry in entries]
    if len(endpoint_ids) != len(set(endpoint_ids)):
        raise ApiPlatformError("Duplicate API endpoint id")
    declared = {(entry["method"], entry["path"]) for entry in entries}
    application = create_app(root)
    implemented = {
        (method, route.path)
        for route in application.routes
        if isinstance(route, APIRoute)
        and (route.path == "/healthz" or route.path.startswith("/api/v1/"))
        for method in route.methods
    }
    if declared != implemented:
        raise ApiPlatformError("API registry and implemented routes differ")
    if any(entry["mutating"] for entry in entries):
        raise ApiPlatformError("Preview API cannot expose mutating endpoints")
    spec = manifest["spec"]
    if spec["authentication"] == "none" and spec["network_scope"] != "loopback":
        raise ApiPlatformError("Unauthenticated API must remain loopback-only")
    if application.openapi()["info"]["version"] != __version__:
        raise ApiPlatformError("OpenAPI version does not match the package")
    return ApiPlatformSummary(
        version=versions.pop(),
        lifecycle=spec["lifecycle"],
        endpoint_ids=tuple(endpoint_ids),
    )
