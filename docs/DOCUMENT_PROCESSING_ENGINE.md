# Document Processing Engine

## Implemented scope

The Document Processing Engine provides deterministic local processing for
UTF-8 text and Markdown files. It confines reads to an explicit source root,
enforces a one-megabyte default limit, normalizes line endings and Unicode,
computes a SHA-256 fingerprint and creates stable character-bounded chunks.

Generated metadata conforms to `knowledge/metadata.schema.yaml`. The engine
does not persist content or call a model.

```bash
.venv/bin/jdgf process-document docs/ARCHITECTURE.md
```

## Deferred scope

PDF, Office documents, HTML, structured data, images, OCR and archives remain
deferred. GitHub, Google Drive, Notion, SharePoint and web connectors are also
disabled. Each requires format-specific safety limits, dependency review,
fixtures and adversarial tests before activation.
