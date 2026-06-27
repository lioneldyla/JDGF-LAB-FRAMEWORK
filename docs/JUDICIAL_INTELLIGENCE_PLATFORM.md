# Judicial Intelligence Extension

## Boundary

Judicial Intelligence is an optional domain profile, not framework business
logic and not an execution runtime. It composes the existing Knowledge and RAG
contracts for source-aware search and cited-answer contracts.

The profile is disabled and non-installable. It does not ingest documents,
generate embeddings, give legal advice, expose an API or claim dashboards.
Those capabilities require separately reviewed adapters and runtime evidence.

Mandatory safeguards are source traceability, confidence labels and human
review. The extension contains no hard-coded consumer project and creates no
dependency from the generic framework core toward an external product.

## Reused contracts

- `knowledge/metadata.schema.yaml`
- `registry/knowledge.yaml`
- `platform/rag/rag-engine.yaml`
- `platform/rag/citation-engine.yaml`
