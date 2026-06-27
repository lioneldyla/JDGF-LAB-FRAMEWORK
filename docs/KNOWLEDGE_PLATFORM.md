# JDGF Knowledge Platform

## Mission

The Knowledge Platform provides governed, portable contracts for source
metadata, collections, ontologies, indexing and retrieval. It is framework
infrastructure, not a repository for a particular domain corpus.

## Contract flow

```text
external source ownership
          |
          v
metadata JSON Schema -> collection registry -> disabled ingestion plan
                                                |             |
                                                v             v
                                      disabled vector   disabled graph
                                           adapter          adapter
                                                \             /
                                                 RAG contract
```

## Foundation contents

- strict document metadata JSON Schema with SHA-256 provenance;
- generic ontology and matching graph schema;
- six empty-by-default collection contracts;
- deterministic, idempotent ingestion plan;
- vector profiles without invented model availability;
- integration reference to the existing Advanced RAG contract;
- Python validation of schemas, paths and cross-artifact invariants.

## Supported metadata source kinds

- repository-bound file;
- URL;
- source repository.

File formats are deliberately not claimed as supported until an extraction
adapter and its adversarial tests exist.

## Runtime boundary

No corpus is committed. Ingestion, embedding, graph extraction, Qdrant, Neo4j
and RAG execution remain disabled. A future activation must define source
ownership, licensing, retention, deletion, access control, model dimensions,
re-indexing and recovery tests.
