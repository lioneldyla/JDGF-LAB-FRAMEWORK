from pathlib import Path
import shutil

import pytest
import yaml
from jsonschema import Draft202012Validator

from jdgf_framework.document_processing import (
    DocumentProcessingError,
    process_document,
    validate_document_processing,
)


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def _copy_contracts(tmp_path: Path) -> Path:
    shutil.copytree(
        ROOT / "platform" / "document-processing",
        tmp_path / "platform" / "document-processing",
    )
    for relative in (
        "registry/document-processing.yaml",
        "registry/document-processing.schema.yaml",
        "manifests/document-processing-platform.yaml",
        "manifests/document-processing-platform.schema.yaml",
        "knowledge/metadata.schema.yaml",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def test_document_processing_contracts_are_valid() -> None:
    summary = validate_document_processing(ROOT)

    assert summary.version == "0.9.1"
    assert summary.active_formats == ("markdown", "text")
    assert summary.max_bytes == 1_048_576


def test_markdown_processing_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "governance_notes.md"
    path.write_bytes(b"# Governance\r\n\r\nAccountability and evidence.\r\n")

    first = process_document(path, tmp_path, max_chunk_chars=100)
    second = process_document(path, tmp_path, max_chunk_chars=100)

    assert first == second
    assert first.format == "markdown"
    assert first.source == "governance_notes.md"
    assert first.content == "# Governance\n\nAccountability and evidence."
    assert first.checksum.startswith("sha256:")
    assert len(first.chunks) == 1
    metadata_schema = _load(ROOT / "knowledge" / "metadata.schema.yaml")
    assert not list(Draft202012Validator(metadata_schema).iter_errors(first.metadata))


def test_long_document_is_chunked_with_stable_ids(tmp_path: Path) -> None:
    path = tmp_path / "long.txt"
    path.write_text("A" * 150 + "\n\n" + "B" * 80, encoding="utf-8")

    document = process_document(path, tmp_path, max_chunk_chars=100)

    assert [chunk.index for chunk in document.chunks] == [1, 2, 3]
    assert document.chunks[0].id.endswith("-0001")
    assert all(len(chunk.content) <= 100 for chunk in document.chunks)


def test_processing_rejects_path_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside", encoding="utf-8")

    with pytest.raises(DocumentProcessingError, match="escapes"):
        process_document(outside, tmp_path)


def test_processing_rejects_unsupported_format(tmp_path: Path) -> None:
    path = tmp_path / "document.pdf"
    path.write_bytes(b"not a PDF")

    with pytest.raises(DocumentProcessingError, match="Unsupported"):
        process_document(path, tmp_path)


def test_processing_rejects_non_utf8(tmp_path: Path) -> None:
    path = tmp_path / "binary.txt"
    path.write_bytes(b"\xff\xfe")

    with pytest.raises(DocumentProcessingError, match="UTF-8"):
        process_document(path, tmp_path)


def test_processing_rejects_oversized_input(tmp_path: Path) -> None:
    path = tmp_path / "large.txt"
    path.write_text("large", encoding="utf-8")

    with pytest.raises(DocumentProcessingError, match="exceeds"):
        process_document(path, tmp_path, max_bytes=2)


def test_external_connector_cannot_be_enabled(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "registry" / "document-processing.yaml"
    registry = _load(path)
    registry["connectors"][1]["enabled"] = True
    _write(path, registry)

    with pytest.raises(DocumentProcessingError, match="deferred"):
        validate_document_processing(root)


def test_contract_cannot_claim_unimplemented_format(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    schema_path = root / "platform" / "document-processing" / "engine.schema.yaml"
    schema = _load(schema_path)
    schema["properties"]["spec"]["properties"]["active_formats"]["items"][
        "enum"
    ].append("pdf")
    _write(schema_path, schema)
    engine_path = root / "platform" / "document-processing" / "engine.yaml"
    engine = _load(engine_path)
    engine["spec"]["active_formats"].append("pdf")
    engine["spec"]["deferred_formats"].remove("pdf")
    _write(engine_path, engine)

    with pytest.raises(DocumentProcessingError, match="implemented extractors"):
        validate_document_processing(root)
