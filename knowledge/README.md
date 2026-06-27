# JDGF Knowledge Platform

The Knowledge Platform defines portable contracts for governed source
collections, metadata, indexing, vector profiles and knowledge graphs.

It does not contain a domain corpus and does not make project content part of
the framework. Consuming projects retain ownership of their sources and may
register them through versioned adapters.

## Foundation status

- metadata and configuration validation: implemented;
- ontology and collection contracts: specified;
- ingestion, embedding, graph extraction and retrieval runtimes: disabled;
- Qdrant and Neo4j adapters: declared but disabled;
- committed source corpus: none.

Use `../scripts/install/20_initialize_knowledge.sh` to validate this contract
slice. The command does not download content or create empty corpus trees.
