"""Framework Core contracts and non-mutating repository diagnostics."""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


@dataclass(frozen=True)
class CorePlatformSummary:
    version: str
    lifecycle: str
    active_operations: tuple[str, ...]


@dataclass(frozen=True)
class DoctorReport:
    version: str
    checks: tuple[str, ...]


class CorePlatformError(ValueError):
    """Raised when core contracts or diagnostics fail."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CorePlatformError(f"Missing file: {path}") from exc
    except yaml.YAMLError as exc:
        raise CorePlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise CorePlatformError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise CorePlatformError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise CorePlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def validate_core_platform(root: Path) -> CorePlatformSummary:
    """Validate core lifecycle declarations against their implementations."""

    root = root.resolve()
    definition_path = root / "core" / "framework.yaml"
    manifest_path = root / "manifests" / "framework-core-platform.yaml"
    definition = _load_mapping(definition_path)
    manifest = _load_mapping(manifest_path)
    _validate(definition, root / "core" / "framework.schema.yaml", definition_path)
    _validate(
        manifest,
        root / "manifests" / "framework-core-platform.schema.yaml",
        manifest_path,
    )
    if definition["metadata"]["version"] != manifest["metadata"]["version"]:
        raise CorePlatformError("Framework Core contract versions do not match")

    active: list[str] = []
    seen: set[str] = set()
    for operation in definition["spec"]["operations"]:
        identifier = operation["id"]
        if identifier in seen:
            raise CorePlatformError(f"Duplicate core operation: {identifier}")
        seen.add(identifier)
        implementation = operation["implementation"]
        if operation["lifecycle"] == "active":
            active.append(identifier)
            if implementation is None or not (root / implementation).is_file():
                raise CorePlatformError(
                    f"Active core operation lacks implementation: {identifier}"
                )
        elif implementation is not None:
            raise CorePlatformError(
                f"Deferred core operation cannot claim implementation: {identifier}"
            )
        if (
            operation["mutating"]
            and identifier in {"package", "update", "backup", "restore"}
            and not operation["approval_required"]
        ):
            raise CorePlatformError(
                f"Consequential core operation requires approval: {identifier}"
            )

    declared = set(manifest["spec"]["active_operations"])
    if declared != set(active):
        raise CorePlatformError("Framework Core active operation declarations differ")
    if manifest["spec"]["installable"] and not manifest["spec"]["runtime_tested"]:
        raise CorePlatformError("Installable Framework Core must be runtime tested")
    return CorePlatformSummary(
        version=manifest["metadata"]["version"],
        lifecycle=manifest["spec"]["lifecycle"],
        active_operations=tuple(sorted(active)),
    )


def run_doctor(root: Path) -> DoctorReport:
    """Check local, authoritative state without contacting external services."""

    root = root.resolve()
    if sys.version_info[:2] != (3, 12):
        raise CorePlatformError("JDGF requires Python 3.12")
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    with (root / "pyproject.toml").open("rb") as stream:
        project_version = tomllib.load(stream)["project"]["version"]
    framework_version = _load_mapping(root / "manifests" / "framework.yaml")[
        "metadata"
    ]["version"]
    from . import __version__

    versions = {version, project_version, framework_version, __version__}
    if len(versions) != 1:
        raise CorePlatformError("Framework version sources are inconsistent")
    required = (
        "uv.lock",
        "bootstrap.sh",
        "verify.sh",
        "registry/modules.yaml",
        "registry/projects.yaml",
    )
    missing = [relative for relative in required if not (root / relative).is_file()]
    if missing:
        raise CorePlatformError("Missing core files: " + ", ".join(missing))
    validate_core_platform(root)
    return DoctorReport(
        version=version,
        checks=(
            "python-3.12",
            "version-consistency",
            "locked-environment",
            "core-contracts",
        ),
    )
