"""Project registry loading and validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

PROJECT_ID = re.compile(r"^[a-z][a-z0-9-]{2,62}$")
LIFECYCLES = {"proposed", "active", "paused", "retired", "template"}


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    name: str
    version: str
    lifecycle: str
    owner: str
    human_approval_required: bool
    capabilities: tuple[str, ...]
    documentation: tuple[str, ...]
    manifest_path: Path


@dataclass(frozen=True)
class ProjectsPlatformSummary:
    version: str
    lifecycle: str
    installable: bool
    project_ids: tuple[str, ...]


class RegistryError(ValueError):
    """Raised when registry or project contracts are invalid."""


def repository_root(start: Path | None = None) -> Path:
    """Find the framework root by its project registry."""

    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "registry" / "projects.yaml").is_file():
            return candidate
    raise RegistryError("Could not locate registry/projects.yaml")


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryError(f"Missing file: {path}") from exc
    except yaml.YAMLError as exc:
        raise RegistryError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(content, dict):
        raise RegistryError(f"Expected a YAML mapping in {path}")
    return content


def _required_mapping(value: Any, label: str, path: Path) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RegistryError(f"{path}: '{label}' must be a mapping")
    return value


def _validate_document(document: dict[str, Any], schema_path: Path, label: str) -> None:
    """Validate a YAML document against its authoritative JSON Schema."""

    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise RegistryError(f"Invalid schema in {schema_path}: {exc.message}") from exc

    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
            document
        ),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise RegistryError(
            f"{label} violates {schema_path.name} at {location}: {error.message}"
        )


def validate_project_manifest(
    path: Path, schema_path: Path | None = None
) -> ProjectRecord:
    """Validate one project manifest and return its normalized record."""

    document = _load_mapping(path)
    schema_path = schema_path or path.parent.parent / "project.schema.yaml"
    _validate_document(document, schema_path, str(path))

    metadata = _required_mapping(document.get("metadata"), "metadata", path)
    spec = _required_mapping(document.get("spec"), "spec", path)
    project_id = metadata.get("id")
    name = metadata.get("name")
    version = metadata.get("version")
    lifecycle = spec.get("lifecycle")
    owner = spec.get("owner")
    governance = _required_mapping(spec.get("governance"), "governance", path)
    capabilities = tuple(spec.get("capabilities", ()))
    documentation = _required_mapping(spec.get("documentation"), "documentation", path)

    if not isinstance(project_id, str) or not PROJECT_ID.fullmatch(project_id):
        raise RegistryError(f"{path}: metadata.id is not a valid project id")
    if not isinstance(name, str) or not name.strip():
        raise RegistryError(f"{path}: metadata.name is required")
    if not isinstance(version, str):
        raise RegistryError(f"{path}: metadata.version is required")
    if lifecycle not in LIFECYCLES:
        raise RegistryError(
            f"{path}: spec.lifecycle must be one of {sorted(LIFECYCLES)}"
        )
    if not isinstance(owner, str) or not owner.strip():
        raise RegistryError(f"{path}: spec.owner is required")

    return ProjectRecord(
        project_id=project_id,
        name=name.strip(),
        version=version,
        lifecycle=lifecycle,
        owner=owner.strip(),
        human_approval_required=governance["human_approval_required"],
        capabilities=capabilities,
        documentation=tuple(documentation.values()),
        manifest_path=path,
    )


def load_project_registry(root: Path | None = None) -> list[ProjectRecord]:
    """Load and cross-check all manifests in the authoritative registry."""

    root = (root or repository_root()).resolve()
    registry_path = root / "registry" / "projects.yaml"
    registry = _load_mapping(registry_path)
    _validate_document(
        registry,
        root / "registry" / "project-registry.schema.yaml",
        str(registry_path),
    )
    entries = registry["projects"]

    records: list[ProjectRecord] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise RegistryError(f"{registry_path}: projects[{index}] must be a mapping")
        project_id = entry.get("id")
        relative_manifest = entry.get("manifest")
        if not isinstance(relative_manifest, str) or not relative_manifest:
            raise RegistryError(
                f"{registry_path}: projects[{index}].manifest is required"
            )
        manifest_path = (root / relative_manifest).resolve()
        if not manifest_path.is_relative_to(root):
            raise RegistryError(f"{registry_path}: manifest path escapes repository")
        projects_root = (root / "projects").resolve()
        if not manifest_path.is_relative_to(projects_root):
            raise RegistryError(
                f"{registry_path}: manifest must be located under projects/"
            )
        record = validate_project_manifest(
            manifest_path, root / "projects" / "project.schema.yaml"
        )
        if project_id != record.project_id:
            raise RegistryError(
                f"{registry_path}: id '{project_id}' does not match '{record.project_id}'"
            )
        if entry["version"] != record.version:
            raise RegistryError(
                f"{registry_path}: version for '{project_id}' does not match its manifest"
            )
        if entry["lifecycle"] != record.lifecycle:
            raise RegistryError(
                f"{registry_path}: lifecycle for '{project_id}' does not match its manifest"
            )
        if record.project_id in seen:
            raise RegistryError(f"{registry_path}: duplicate id '{record.project_id}'")
        seen.add(record.project_id)
        records.append(record)
    return records


def validate_projects_platform(root: Path) -> ProjectsPlatformSummary:
    """Validate the active Projects Platform and its repository boundaries."""

    root = root.resolve()
    manifest_path = root / "manifests" / "projects-platform.yaml"
    manifest = _load_mapping(manifest_path)
    _validate_document(
        manifest,
        root / "manifests" / "projects-platform.schema.yaml",
        str(manifest_path),
    )
    registry = _load_mapping(root / "registry" / "projects.yaml")
    records = load_project_registry(root)

    version = manifest["metadata"]["version"]
    if registry["metadata"]["version"] != version:
        raise RegistryError("Projects Platform and project registry versions differ")

    expected_components = {
        "project-registry",
        "project-schema",
        "governance",
        "lifecycle",
        "documentation",
    }
    if set(manifest["spec"]["components"]) != expected_components:
        raise RegistryError("Projects Platform component set is incomplete")

    module_manifest = _load_mapping(root / "manifests" / "modules.yaml")
    known_capabilities = {module["id"] for module in module_manifest["modules"]}
    for record in records:
        if record.lifecycle == "template":
            raise RegistryError(
                f"Template project cannot be registered: {record.project_id}"
            )
        if record.lifecycle == "active" and not record.human_approval_required:
            raise RegistryError(
                f"Active project requires human approval: {record.project_id}"
            )
        unknown = set(record.capabilities) - known_capabilities
        if unknown:
            raise RegistryError(
                f"Project {record.project_id} references unknown capabilities: "
                + ", ".join(sorted(unknown))
            )
        for relative in record.documentation:
            path = (root / relative).resolve()
            if not path.is_relative_to(root):
                raise RegistryError(
                    f"Project documentation escapes repository: {record.project_id}"
                )
            if not path.is_file():
                raise RegistryError(
                    f"Project documentation is missing for {record.project_id}: {relative}"
                )

    spec = manifest["spec"]
    if spec["installable"] and not (
        spec["lifecycle"] == "active" and spec["runtime_tested"]
    ):
        raise RegistryError(
            "Projects Platform cannot be installable before activation and tests"
        )

    return ProjectsPlatformSummary(
        version=version,
        lifecycle=spec["lifecycle"],
        installable=spec["installable"],
        project_ids=tuple(record.project_id for record in records),
    )
