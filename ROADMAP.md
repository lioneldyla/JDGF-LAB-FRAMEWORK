# Roadmap

JDGF Lab Framework grows through small, independently validated control-plane
slices. A directory or archived specification does not make a capability
active.

## Foundation — active

- project and registry JSON Schemas;
- deterministic project discovery;
- repository-bound manifest resolution;
- local validation CLI and tests.

## Governance — next

- policy and decision-record contracts;
- ownership and lifecycle enforcement;
- explicit approval gates for consequential external actions.

## Capability contracts — planned

- agent and tool capability declarations;
- workflow and event contracts;
- knowledge-source and data-governance contracts.

Advanced RAG component contracts are now specified. Runtime retrieval,
generation, memory and graph adapters remain deferred.

The Knowledge Platform foundation now validates metadata, collections,
ontology and pipeline contracts. Extraction, indexing and retrieval runtimes
remain deferred until tested adapters exist.

## Adapter runtimes — deferred

Model, database, vector-store, automation, monitoring and interface contracts
are specified. Their runtime activation remains deferred until portable
adapters are backed by integration, security and recovery tests plus operating
documentation.

Named external projects and domain-specific business logic are outside the
framework repository. They may consume public contracts without becoming core
dependencies.
