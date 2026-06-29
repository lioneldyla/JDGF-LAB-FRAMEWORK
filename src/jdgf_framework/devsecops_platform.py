"""DevSecOps workflow, packaging and supply-chain policy validation."""

from __future__ import annotations

import re
import stat
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

ACTION_PIN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")


@dataclass(frozen=True)
class DevSecOpsPlatformSummary:
    version: str
    lifecycle: str
    installable: bool
    workflow_ids: tuple[str, ...]
    tool_ids: tuple[str, ...]


class DevSecOpsPlatformError(ValueError):
    """Raised when CI/CD declarations violate reproducibility or security policy."""


def _load_mapping(path: Path, *, base_loader: bool = False) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        if base_loader:
            loader = yaml.BaseLoader(text)
            try:
                document = loader.get_single_data()
            finally:
                loader.dispose()  # type: ignore[no-untyped-call]
        else:
            document = yaml.safe_load(text)
    except FileNotFoundError as exc:
        raise DevSecOpsPlatformError(f"Missing DevSecOps artifact: {path}") from exc
    except yaml.YAMLError as exc:
        raise DevSecOpsPlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise DevSecOpsPlatformError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise DevSecOpsPlatformError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise DevSecOpsPlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def _resolve(root: Path, relative: str, boundary: str | None = None) -> Path:
    path = (root / relative).resolve()
    allowed = (root / boundary).resolve() if boundary else root
    if not path.is_relative_to(allowed):
        raise DevSecOpsPlatformError(f"DevSecOps path escapes repository: {relative}")
    if not path.is_file():
        raise DevSecOpsPlatformError(f"DevSecOps artifact does not exist: {relative}")
    return path


def _workflow_steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    jobs = workflow.get("jobs", {})
    if not isinstance(jobs, dict) or not jobs:
        raise DevSecOpsPlatformError("GitHub workflow must declare jobs")
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            raise DevSecOpsPlatformError(f"GitHub workflow job is invalid: {job_id}")
        if "timeout-minutes" not in job:
            raise DevSecOpsPlatformError(f"GitHub workflow job lacks timeout: {job_id}")
        job_steps = job.get("steps", [])
        if not isinstance(job_steps, list) or not job_steps:
            raise DevSecOpsPlatformError(f"GitHub workflow job lacks steps: {job_id}")
        steps.extend(step for step in job_steps if isinstance(step, dict))
    return steps


def validate_devsecops_platform(root: Path) -> DevSecOpsPlatformSummary:
    """Validate CI workflows without claiming deployment or release publishing."""

    root = root.resolve()
    manifest_path = root / "manifests" / "devsecops-platform.yaml"
    registry_path = root / "registry" / "devsecops.yaml"
    config_path = root / "devsecops" / "devsecops.yaml"
    manifest = _load_mapping(manifest_path)
    registry = _load_mapping(registry_path)
    config = _load_mapping(config_path)
    _validate(
        manifest,
        root / "manifests" / "devsecops-platform.schema.yaml",
        manifest_path,
    )
    _validate(
        registry,
        root / "registry" / "devsecops.schema.yaml",
        registry_path,
    )
    _validate(config, root / "devsecops" / "devsecops.schema.yaml", config_path)

    version = manifest["metadata"]["version"]
    if registry["metadata"]["version"] != version:
        raise DevSecOpsPlatformError("DevSecOps manifest and registry versions differ")
    expected_components = {
        "github-actions",
        "dependency-updates",
        "ci",
        "security",
        "quality",
        "packaging",
        "release-candidates",
    }
    if set(manifest["spec"]["components"]) != expected_components:
        raise DevSecOpsPlatformError("DevSecOps component set is incomplete")

    expected_workflows = {
        "continuous-integration": ".github/workflows/ci.yml",
        "container-contracts": ".github/workflows/container-contracts.yml",
        "release-candidate": ".github/workflows/release-candidate.yml",
    }
    workflow_root = root / ".github" / "workflows"
    actual_workflows = {
        path.relative_to(root).as_posix()
        for pattern in ("*.yml", "*.yaml")
        for path in workflow_root.glob(pattern)
    }
    if actual_workflows != set(expected_workflows.values()):
        unexpected = sorted(actual_workflows - set(expected_workflows.values()))
        missing = sorted(set(expected_workflows.values()) - actual_workflows)
        details = []
        if unexpected:
            details.append("unregistered: " + ", ".join(unexpected))
        if missing:
            details.append("missing: " + ", ".join(missing))
        raise DevSecOpsPlatformError(
            "GitHub workflow inventory differs from registry ("
            + "; ".join(details)
            + ")"
        )
    workflow_ids = [entry["id"] for entry in registry["workflows"]]
    if len(workflow_ids) != len(set(workflow_ids)):
        raise DevSecOpsPlatformError("Duplicate DevSecOps workflow id")
    if {
        entry["id"]: entry["path"] for entry in registry["workflows"]
    } != expected_workflows:
        raise DevSecOpsPlatformError("DevSecOps workflow registry is not canonical")

    forbidden_fragments = (
        "pull_request_target",
        "permissions: write-all",
        "contents: write",
        "id-token: write",
        "${{ secrets.",
        "git push",
        "docker push",
        "gh release create",
        "kubectl apply",
    )
    for entry in registry["workflows"]:
        path = _resolve(root, entry["path"], ".github/workflows")
        text = path.read_text(encoding="utf-8")
        workflow = _load_mapping(path, base_loader=True)
        if any(fragment in text for fragment in forbidden_fragments):
            raise DevSecOpsPlatformError(
                f"GitHub workflow contains forbidden authority: {entry['id']}"
            )
        permissions = workflow.get("permissions")
        if permissions != {"contents": "read"}:
            raise DevSecOpsPlatformError(
                f"GitHub workflow permissions are not minimal: {entry['id']}"
            )
        triggers = workflow.get("on")
        if not isinstance(triggers, dict):
            raise DevSecOpsPlatformError(
                f"GitHub workflow triggers are invalid: {entry['id']}"
            )
        if set(triggers) != set(entry["triggers"]):
            raise DevSecOpsPlatformError(
                f"GitHub workflow triggers do not match registry: {entry['id']}"
            )

        checkout_seen = False
        for step in _workflow_steps(workflow):
            action = step.get("uses")
            if action is not None:
                if not isinstance(action, str) or not ACTION_PIN.fullmatch(action):
                    raise DevSecOpsPlatformError(
                        f"GitHub action is not pinned by full SHA: {entry['id']}"
                    )
                if action.startswith("actions/checkout@"):
                    checkout_seen = True
                    options = step.get("with", {})
                    if options.get("persist-credentials") != "false":
                        raise DevSecOpsPlatformError(
                            f"Checkout credentials must not persist: {entry['id']}"
                        )
        if not checkout_seen:
            raise DevSecOpsPlatformError(
                f"GitHub workflow does not check out deterministically: {entry['id']}"
            )
        if entry["publishes"] or entry["deploys"]:
            raise DevSecOpsPlatformError(
                f"Publishing and deployment must remain disabled: {entry['id']}"
            )

    tool_ids = [tool["id"] for tool in registry["tools"]]
    if len(tool_ids) != len(set(tool_ids)):
        raise DevSecOpsPlatformError("Duplicate DevSecOps tool id")
    if set(tool_ids) != {"uv", "pytest", "ruff", "mypy", "pip-audit", "bash"}:
        raise DevSecOpsPlatformError("DevSecOps tool registry is incomplete")

    dependabot_path = _resolve(root, ".github/dependabot.yml", ".github")
    dependabot = _load_mapping(dependabot_path)
    if dependabot.get("version") != 2:
        raise DevSecOpsPlatformError("Dependabot configuration must use version 2")
    updates = dependabot.get("updates")
    if not isinstance(updates, list):
        raise DevSecOpsPlatformError("Dependabot updates must be a list")
    expected_ecosystems = {"uv", "github-actions"}
    ecosystems = {
        entry.get("package-ecosystem") for entry in updates if isinstance(entry, dict)
    }
    if ecosystems != expected_ecosystems or len(updates) != len(expected_ecosystems):
        raise DevSecOpsPlatformError("Dependabot ecosystem set is incomplete")
    allowed_dependabot_keys = {
        "package-ecosystem",
        "directory",
        "schedule",
        "open-pull-requests-limit",
    }
    for entry in updates:
        if set(entry) - allowed_dependabot_keys:
            raise DevSecOpsPlatformError(
                "Dependabot configuration uses unsupported options"
            )
        if entry.get("directory") != "/" or entry.get("schedule") != {
            "interval": "weekly"
        }:
            raise DevSecOpsPlatformError(
                "Dependabot update location or schedule is invalid"
            )

    scripts = {
        "lint": _resolve(root, "scripts/devsecops/run-lint.sh"),
        "tests": _resolve(root, "scripts/devsecops/run-tests.sh"),
        "security": _resolve(root, "scripts/devsecops/security-scan.sh"),
        "package": _resolve(root, "scripts/devsecops/package.sh"),
        "release": _resolve(root, "scripts/devsecops/build-release.sh"),
    }
    for name, path in scripts.items():
        if not path.stat().st_mode & stat.S_IXUSR:
            raise DevSecOpsPlatformError(f"DevSecOps script is not executable: {name}")
        text = path.read_text(encoding="utf-8")
        if "|| true" in text:
            raise DevSecOpsPlatformError(
                f"DevSecOps script suppresses failures: {name}"
            )
    package_text = scripts["package"].read_text(encoding="utf-8")
    if "uv build" not in package_text or "tar -czf" in package_text:
        raise DevSecOpsPlatformError("Packaging must build project artifacts only")
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    sdist_include = pyproject["tool"]["hatch"]["build"]["targets"]["sdist"]["include"]
    if set(sdist_include) != {
        "/LICENSE",
        "/README.md",
        "/pyproject.toml",
        "/src/jdgf_framework",
    }:
        raise DevSecOpsPlatformError("Source distribution include set is not minimal")
    security_text = scripts["security"].read_text(encoding="utf-8")
    if "pip-audit" not in security_text:
        raise DevSecOpsPlatformError("Dependency audit is not configured")

    config_spec = config["spec"]
    manifest_spec = manifest["spec"]
    if manifest_spec["deployment_enabled"] or any(config_spec["deployment"].values()):
        raise DevSecOpsPlatformError("Deployment must remain disabled")
    if (
        manifest_spec["release_publishing_enabled"]
        or config_spec["release"]["publishing"]
    ):
        raise DevSecOpsPlatformError("Release publishing must remain disabled")
    if manifest_spec["installable"] and not (
        manifest_spec["lifecycle"] == "active" and manifest_spec["runtime_tested"]
    ):
        raise DevSecOpsPlatformError(
            "DevSecOps Platform cannot be installable before hosted workflow tests"
        )

    return DevSecOpsPlatformSummary(
        version=version,
        lifecycle=manifest_spec["lifecycle"],
        installable=manifest_spec["installable"],
        workflow_ids=tuple(workflow_ids),
        tool_ids=tuple(tool_ids),
    )
