"""Governance Platform policy, evidence and honesty validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


@dataclass(frozen=True)
class GovernancePlatformSummary:
    version: str
    lifecycle: str
    installable: bool
    policy_ids: tuple[str, ...]
    implemented_rule_count: int


class GovernancePlatformError(ValueError):
    """Raised when governance declarations are invalid or overclaim enforcement."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GovernancePlatformError(f"Missing governance artifact: {path}") from exc
    except yaml.YAMLError as exc:
        raise GovernancePlatformError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise GovernancePlatformError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise GovernancePlatformError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise GovernancePlatformError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def _resolve(root: Path, relative: str, boundary: str | None = None) -> Path:
    path = (root / relative).resolve()
    allowed = (root / boundary).resolve() if boundary else root
    if not path.is_relative_to(allowed):
        raise GovernancePlatformError(f"Governance path escapes repository: {relative}")
    if not path.exists():
        raise GovernancePlatformError(f"Governance evidence does not exist: {relative}")
    return path


def validate_governance_platform(root: Path) -> GovernancePlatformSummary:
    """Validate governance policies and machine-verifiable evidence claims."""

    root = root.resolve()
    manifest_path = root / "manifests" / "governance-platform.yaml"
    registry_path = root / "registry" / "governance.yaml"
    manifest = _load_mapping(manifest_path)
    registry = _load_mapping(registry_path)
    _validate(
        manifest,
        root / "manifests" / "governance-platform.schema.yaml",
        manifest_path,
    )
    _validate(
        registry,
        root / "registry" / "governance.schema.yaml",
        registry_path,
    )

    version = manifest["metadata"]["version"]
    if registry["metadata"]["version"] != version:
        raise GovernancePlatformError(
            "Governance manifest and registry versions differ"
        )
    expected_components = {
        "policies",
        "access-control",
        "ai-governance",
        "data-governance",
        "release",
        "quality",
        "audit",
    }
    if set(manifest["spec"]["components"]) != expected_components:
        raise GovernancePlatformError("Governance component set is incomplete")

    framework_path = _resolve(root, registry["framework"], "governance")
    framework = _load_mapping(framework_path)
    _validate(
        framework,
        root / "governance" / "governance.schema.yaml",
        framework_path,
    )
    domains = set(framework["spec"]["domains"])
    policy_schema = root / "governance" / "policy.schema.yaml"
    policy_ids: list[str] = []
    implemented_rule_count = 0

    for entry in registry["policies"]:
        if entry["id"] in policy_ids:
            raise GovernancePlatformError("Duplicate governance policy id")
        path = _resolve(root, entry["manifest"], "governance/policies")
        policy = _load_mapping(path)
        _validate(policy, policy_schema, path)
        metadata = policy["metadata"]
        spec = policy["spec"]
        if entry["id"] != metadata["id"] or entry["version"] != metadata["version"]:
            raise GovernancePlatformError(
                f"Governance registry/policy mismatch: {entry['id']}"
            )
        if entry["status"] != metadata["status"]:
            raise GovernancePlatformError(
                f"Governance policy status mismatch: {entry['id']}"
            )
        if spec["domain"] not in domains:
            raise GovernancePlatformError(
                f"Governance policy uses unknown domain: {entry['id']}"
            )
        if entry["enabled"]:
            raise GovernancePlatformError(
                f"Governance policy enforcement must remain disabled: {entry['id']}"
            )

        rule_ids = [rule["id"] for rule in spec["rules"]]
        if len(rule_ids) != len(set(rule_ids)):
            raise GovernancePlatformError(f"Duplicate governance rule: {entry['id']}")
        for rule in spec["rules"]:
            if rule["implemented"]:
                implemented_rule_count += 1
                if not rule["evidence"]:
                    raise GovernancePlatformError(
                        f"Implemented governance rule lacks evidence: {entry['id']}/{rule['id']}"
                    )
                if rule["enforcement"] == "runtime":
                    raise GovernancePlatformError(
                        f"Runtime governance rule cannot be claimed implemented: {entry['id']}/{rule['id']}"
                    )
                for evidence in rule["evidence"]:
                    _resolve(root, evidence)
            elif rule["evidence"]:
                raise GovernancePlatformError(
                    f"Unimplemented governance rule cannot claim evidence: {entry['id']}/{rule['id']}"
                )

        roles = spec["parameters"].get("roles", [])
        role_ids = [role["id"] for role in roles]
        if len(role_ids) != len(set(role_ids)):
            raise GovernancePlatformError(f"Duplicate governance role: {entry['id']}")
        policy_ids.append(entry["id"])

    access_policy = _load_mapping(
        root / "governance" / "policies" / "access-control.yaml"
    )
    access_roles = {
        role["id"]: set(role["permissions"])
        for role in access_policy["spec"]["parameters"]["roles"]
    }
    if (
        "administrator" not in access_roles
        or "administer" not in access_roles["administrator"]
    ):
        raise GovernancePlatformError("Access-control policy lacks administrator role")
    if access_roles.get("observer") != {"read"}:
        raise GovernancePlatformError("Observer role must remain read-only")

    ai_policy = _load_mapping(root / "governance" / "policies" / "ai-governance.yaml")
    ai_rules = {rule["id"]: rule for rule in ai_policy["spec"]["rules"]}
    for required in ("human-oversight", "no-unattended-execution"):
        if not ai_rules.get(required, {}).get("implemented"):
            raise GovernancePlatformError(f"AI governance rule is missing: {required}")

    backup_policy = _load_mapping(root / "governance" / "policies" / "backup.yaml")
    if any(rule["implemented"] for rule in backup_policy["spec"]["rules"]):
        raise GovernancePlatformError(
            "Backup policy cannot claim runtime implementation"
        )

    spec = manifest["spec"]
    policies_enabled = any(entry["enabled"] for entry in registry["policies"])
    if spec["policies_enabled"] != policies_enabled:
        raise GovernancePlatformError(
            "Governance policy activation claim is inconsistent"
        )
    governance_enforcement = framework["spec"]["enforcement"]
    if spec["rbac_enforced"] != governance_enforcement["rbac_runtime"]:
        raise GovernancePlatformError("RBAC enforcement claim is inconsistent")
    audit_enabled = governance_enforcement["audit_sink"] is not None
    if spec["audit_enabled"] != audit_enabled:
        raise GovernancePlatformError("Audit activation claim is inconsistent")
    if spec["installable"] and not (
        spec["lifecycle"] == "active"
        and spec["runtime_tested"]
        and spec["policies_enabled"]
        and spec["rbac_enforced"]
        and spec["audit_enabled"]
    ):
        raise GovernancePlatformError(
            "Governance Platform cannot be installable before enforcement and runtime tests"
        )

    return GovernancePlatformSummary(
        version=version,
        lifecycle=spec["lifecycle"],
        installable=spec["installable"],
        policy_ids=tuple(policy_ids),
        implemented_rule_count=implemented_rule_count,
    )
