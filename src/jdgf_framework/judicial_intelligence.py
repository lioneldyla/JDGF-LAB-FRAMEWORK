"""Validation for the optional Judicial Intelligence extension profile."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
import yaml


@dataclass(frozen=True)
class JudicialIntelligenceSummary:
    version: str
    lifecycle: str
    enabled: bool
    outputs: tuple[str, ...]


class JudicialIntelligenceError(ValueError):
    """Raised when the extension contract violates its declared boundary."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise JudicialIntelligenceError(f"Missing file: {path}") from exc
    except yaml.YAMLError as exc:
        raise JudicialIntelligenceError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise JudicialIntelligenceError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise JudicialIntelligenceError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise JudicialIntelligenceError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def validate_judicial_intelligence(root: Path) -> JudicialIntelligenceSummary:
    """Validate extension composition without claiming an execution runtime."""

    root = root.resolve()
    manifest_path = root / "manifests" / "judicial-intelligence-platform.yaml"
    registry_path = root / "registry" / "judicial-intelligence.yaml"
    profile_path = root / "platform" / "judicial-intelligence" / "profile.yaml"
    manifest = _load_mapping(manifest_path)
    registry = _load_mapping(registry_path)
    profile = _load_mapping(profile_path)
    _validate(
        manifest,
        root / "manifests" / "judicial-intelligence-platform.schema.yaml",
        manifest_path,
    )
    _validate(
        registry,
        root / "registry" / "judicial-intelligence.schema.yaml",
        registry_path,
    )
    _validate(
        profile,
        root / "platform" / "judicial-intelligence" / "profile.schema.yaml",
        profile_path,
    )
    versions = {
        manifest["metadata"]["version"],
        registry["metadata"]["version"],
        profile["metadata"]["version"],
    }
    if len(versions) != 1:
        raise JudicialIntelligenceError("Judicial Intelligence versions do not match")
    entry = registry["extensions"][0]
    if entry["lifecycle"] != profile["metadata"]["lifecycle"]:
        raise JudicialIntelligenceError("Extension lifecycle does not match registry")
    if entry["enabled"] != profile["spec"]["enabled"]:
        raise JudicialIntelligenceError(
            "Extension enabled state does not match registry"
        )

    expected_composition = {
        "document_metadata": "knowledge/metadata.schema.yaml",
        "knowledge_registry": "registry/knowledge.yaml",
        "rag_engine": "platform/rag/rag-engine.yaml",
        "citation_engine": "platform/rag/citation-engine.yaml",
    }
    if profile["spec"]["composition"] != expected_composition:
        raise JudicialIntelligenceError(
            "Extension must compose authoritative Knowledge and RAG contracts"
        )
    for relative in expected_composition.values():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise JudicialIntelligenceError(
                f"Extension composition reference is missing: {relative}"
            )
    if profile["spec"]["runtime_implemented"] or manifest["spec"]["installable"]:
        raise JudicialIntelligenceError("Extension runtime must remain disabled")
    return JudicialIntelligenceSummary(
        version=versions.pop(),
        lifecycle=profile["metadata"]["lifecycle"],
        enabled=profile["spec"]["enabled"],
        outputs=tuple(profile["spec"]["outputs"]),
    )
