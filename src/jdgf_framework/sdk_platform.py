"""Validated SDK contracts and safe project scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import shutil
import tempfile
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
import yaml

from .projects import PROJECT_ID, RegistryError, validate_project_manifest


@dataclass(frozen=True)
class SdkPlatformSummary:
    version: str
    lifecycle: str
    active_generators: tuple[str, ...]


class SdkPlatformError(ValueError):
    """Raised when SDK contracts or scaffold requests are invalid."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SdkPlatformError(f"Missing file: {path}") from exc
    except yaml.YAMLError as exc:
        raise SdkPlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise SdkPlatformError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise SdkPlatformError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise SdkPlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def validate_sdk_platform(root: Path) -> SdkPlatformSummary:
    """Validate the SDK manifest, definition and registry as one contract."""

    root = root.resolve()
    manifest_path = root / "manifests" / "sdk-platform.yaml"
    definition_path = root / "sdk" / "sdk.yaml"
    registry_path = root / "registry" / "sdk.yaml"
    manifest = _load_mapping(manifest_path)
    definition = _load_mapping(definition_path)
    registry = _load_mapping(registry_path)
    _validate(manifest, root / "manifests" / "sdk-platform.schema.yaml", manifest_path)
    _validate(definition, root / "sdk" / "sdk.schema.yaml", definition_path)
    _validate(registry, root / "registry" / "sdk.schema.yaml", registry_path)

    versions = {
        manifest["metadata"]["version"],
        definition["metadata"]["version"],
        registry["metadata"]["version"],
    }
    if len(versions) != 1:
        raise SdkPlatformError("SDK contract versions do not match")

    generators = {item["id"]: item for item in definition["spec"]["generators"]}
    capabilities = {item["id"]: item for item in registry["capabilities"]}
    if generators.keys() != capabilities.keys():
        raise SdkPlatformError("SDK definition and registry capabilities differ")
    for identifier, generator in generators.items():
        capability = capabilities[identifier]
        if generator["lifecycle"] != capability["lifecycle"]:
            raise SdkPlatformError(f"SDK lifecycle mismatch for {identifier}")
        if generator["lifecycle"] == "active":
            contract = generator["contract"]
            if contract is None or not (root / contract).is_file():
                raise SdkPlatformError(f"Active generator lacks contract: {identifier}")
            if capability["command"] is None:
                raise SdkPlatformError(f"Active generator lacks command: {identifier}")
        elif generator["contract"] is not None or capability["command"] is not None:
            raise SdkPlatformError(
                f"Deferred generator cannot claim implementation: {identifier}"
            )

    active = tuple(
        sorted(key for key, item in generators.items() if item["lifecycle"] == "active")
    )
    if set(active) != set(manifest["spec"]["active_generators"]):
        raise SdkPlatformError("SDK active generator declarations differ")
    if manifest["spec"]["installable"] and not (
        manifest["spec"]["lifecycle"] == "active" and manifest["spec"]["runtime_tested"]
    ):
        raise SdkPlatformError("Installable SDK requires active, tested implementation")
    return SdkPlatformSummary(
        version=versions.pop(),
        lifecycle=manifest["spec"]["lifecycle"],
        active_generators=active,
    )


def scaffold_project(root: Path, project_id: str, name: str, owner: str) -> Path:
    """Atomically create an unregistered project that satisfies the project schema."""

    root = root.resolve()
    if not PROJECT_ID.fullmatch(project_id):
        raise SdkPlatformError("Project id must match ^[a-z][a-z0-9-]{2,62}$")
    if not name.strip() or not owner.strip():
        raise SdkPlatformError("Project name and owner are required")
    projects_root = (root / "projects").resolve()
    if not projects_root.is_dir():
        raise SdkPlatformError(f"Projects root does not exist: {projects_root}")
    destination = (projects_root / project_id).resolve()
    if destination.parent != projects_root:
        raise SdkPlatformError("Project destination escapes projects root")
    if destination.exists():
        raise SdkPlatformError(f"Project already exists: {project_id}")

    today = date.today().isoformat()
    manifest = {
        "api_version": "jdgf.io/v1alpha1",
        "contract_version": "1.0",
        "kind": "Project",
        "metadata": {
            "id": project_id,
            "name": name.strip(),
            "version": "0.1.0",
            "description": f"JDGF-managed project: {name.strip()}.",
            "license": "UNLICENSED",
        },
        "spec": {
            "lifecycle": "proposed",
            "owner": owner.strip(),
            "governance": {"human_approval_required": True, "roles": {}},
            "architecture": {
                "modules": [],
                "services": [],
                "dependencies": [],
                "datasets": [],
                "knowledge": [],
                "agents": [],
            },
            "capabilities": [],
            "timeline": {"created": today, "updated": today, "release": "0.1.0"},
            "documentation": {"readme": f"projects/{project_id}/README.md"},
        },
    }
    temporary = Path(tempfile.mkdtemp(prefix=f".{project_id}-", dir=projects_root))
    try:
        (temporary / "README.md").write_text(
            f"# {name.strip()}\n\n"
            "This project is proposed and is not registered automatically. Review "
            "its manifest, then add it to `registry/projects.yaml` deliberately.\n",
            encoding="utf-8",
        )
        manifest_path = temporary / "project.yaml"
        manifest_path.write_text(
            yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
        )
        validate_project_manifest(manifest_path, projects_root / "project.schema.yaml")
        temporary.rename(destination)
    except (OSError, RegistryError) as exc:
        shutil.rmtree(temporary, ignore_errors=True)
        raise SdkPlatformError(f"Could not scaffold project: {exc}") from exc
    return destination
