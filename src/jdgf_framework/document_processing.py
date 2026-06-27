"""Bounded, deterministic processing for local UTF-8 text documents."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import unicodedata
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
import yaml


SUPPORTED_SUFFIXES = {".txt": "text", ".md": "markdown"}


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    index: int
    content: str


@dataclass(frozen=True)
class ProcessedDocument:
    id: str
    title: str
    format: str
    checksum: str
    source: str
    content: str
    chunks: tuple[DocumentChunk, ...]

    @property
    def metadata(self) -> dict[str, object]:
        """Return metadata compatible with the Knowledge Platform schema."""

        return {
            "id": self.id,
            "title": self.title,
            "language": "und",
            "document_type": "documentation" if self.format == "markdown" else "other",
            "source": {"kind": "file", "locator": self.source},
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class DocumentProcessingSummary:
    version: str
    active_formats: tuple[str, ...]
    max_bytes: int


class DocumentProcessingError(ValueError):
    """Raised when a document or processing contract is invalid."""


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DocumentProcessingError(f"Missing file: {path}") from exc
    except yaml.YAMLError as exc:
        raise DocumentProcessingError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise DocumentProcessingError(f"Expected a YAML mapping in {path}")
    return document


def _validate(document: dict[str, Any], schema_path: Path, path: Path) -> None:
    schema = _load_mapping(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise DocumentProcessingError(
            f"Invalid schema in {schema_path}: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise DocumentProcessingError(
            f"{path} violates {schema_path.name} at {location}: {error.message}"
        )


def validate_document_processing(root: Path) -> DocumentProcessingSummary:
    """Validate processing contracts and their conservative capability claims."""

    root = root.resolve()
    engine_path = root / "platform" / "document-processing" / "engine.yaml"
    registry_path = root / "registry" / "document-processing.yaml"
    manifest_path = root / "manifests" / "document-processing-platform.yaml"
    engine = _load_mapping(engine_path)
    registry = _load_mapping(registry_path)
    manifest = _load_mapping(manifest_path)
    _validate(
        engine,
        root / "platform" / "document-processing" / "engine.schema.yaml",
        engine_path,
    )
    _validate(
        registry,
        root / "registry" / "document-processing.schema.yaml",
        registry_path,
    )
    _validate(
        manifest,
        root / "manifests" / "document-processing-platform.schema.yaml",
        manifest_path,
    )
    versions = {
        engine["metadata"]["version"],
        registry["metadata"]["version"],
        manifest["metadata"]["version"],
    }
    if len(versions) != 1:
        raise DocumentProcessingError("Document Processing versions do not match")
    expected_formats = set(SUPPORTED_SUFFIXES.values())
    if set(engine["spec"]["active_formats"]) != expected_formats:
        raise DocumentProcessingError(
            "Active formats do not match implemented extractors"
        )
    metadata_schema = (root / engine["spec"]["metadata_schema"]).resolve()
    if not metadata_schema.is_relative_to(root) or not metadata_schema.is_file():
        raise DocumentProcessingError("Knowledge metadata schema is missing")
    connectors = {item["id"]: item for item in registry["connectors"]}
    if connectors["local-filesystem"] != {
        "id": "local-filesystem",
        "lifecycle": "active",
        "enabled": True,
    }:
        raise DocumentProcessingError("Local filesystem connector must be active")
    if any(
        item["enabled"] or item["lifecycle"] != "deferred"
        for identifier, item in connectors.items()
        if identifier != "local-filesystem"
    ):
        raise DocumentProcessingError("External connectors must remain deferred")
    spec = manifest["spec"]
    if spec["installable"] and not (
        spec["lifecycle"] == "active" and spec["runtime_tested"]
    ):
        raise DocumentProcessingError(
            "Installable document processing requires an active, tested runtime"
        )
    return DocumentProcessingSummary(
        version=versions.pop(),
        active_formats=tuple(sorted(expected_formats)),
        max_bytes=engine["spec"]["limits"]["max_bytes"],
    )


def _chunks(
    content: str, document_id: str, max_chars: int
) -> tuple[DocumentChunk, ...]:
    paragraphs = [
        part.strip() for part in re.split(r"\n\s*\n", content) if part.strip()
    ]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        segments = [
            paragraph[index : index + max_chars]
            for index in range(0, len(paragraph), max_chars)
        ]
        for segment in segments:
            candidate = f"{current}\n\n{segment}" if current else segment
            if len(candidate) <= max_chars:
                current = candidate
            else:
                chunks.append(current)
                current = segment
    if current:
        chunks.append(current)
    return tuple(
        DocumentChunk(id=f"{document_id}-{index:04d}", index=index, content=value)
        for index, value in enumerate(chunks, start=1)
    )


def process_document(
    path: Path,
    source_root: Path,
    *,
    max_bytes: int = 1_048_576,
    max_chunk_chars: int = 1_000,
) -> ProcessedDocument:
    """Read and transform one repository-bound TXT or Markdown document."""

    source_root = source_root.resolve()
    path = path.resolve()
    if not path.is_relative_to(source_root):
        raise DocumentProcessingError("Document path escapes the allowed source root")
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise DocumentProcessingError(f"Unsupported document format: {path.suffix}")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise DocumentProcessingError(f"Cannot access document: {path}") from exc
    if size > max_bytes:
        raise DocumentProcessingError(f"Document exceeds {max_bytes} byte limit")
    try:
        raw = path.read_bytes()
        decoded = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise DocumentProcessingError("Document must be readable UTF-8 text") from exc
    content = unicodedata.normalize(
        "NFC", decoded.replace("\r\n", "\n").replace("\r", "\n")
    ).strip()
    if not content:
        raise DocumentProcessingError("Document content is empty")
    if max_chunk_chars < 100:
        raise DocumentProcessingError("Chunk size must be at least 100 characters")
    digest = sha256(raw).hexdigest()
    document_id = f"doc-{digest[:16]}"
    return ProcessedDocument(
        id=document_id,
        title=path.stem.replace("_", " ").replace("-", " ").strip(),
        format=SUPPORTED_SUFFIXES[path.suffix.lower()],
        checksum=f"sha256:{digest}",
        source=path.relative_to(source_root).as_posix(),
        content=content,
        chunks=_chunks(content, document_id, max_chunk_chars),
    )
