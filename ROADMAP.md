# Roadmap

JDGF Lab Framework grows through small, independently validated control-plane
slices. A directory or archived specification does not make a capability
active.

## Foundation — active

- project and registry JSON Schemas with governance and lifecycle checks;
- deterministic project discovery;
- repository-bound manifest resolution;
- local validation CLI and tests.

## Governance — next

- policy and decision-record contracts;
- ownership and lifecycle enforcement;
- explicit approval gates for consequential external actions.

## Capability contracts — planned

- workflow and event contracts;
- knowledge-source and data-governance contracts.

Agent and tool capability declarations are now specified with all execution
disabled. A sandboxed agent runtime remains planned.

Orchestration routing and workflow contracts are now specified. The sandboxed
engine, durable audit trail, retries and multi-agent execution remain deferred.

Governance policies and evidence checks are now specified. Runtime RBAC, audit,
encryption verification, backups, compliance mapping and release signing remain
deferred.

CI, dependency auditing and release-candidate packaging are now specified.
Hosted execution evidence, signing, publishing and deployment remain deferred.

Project scaffolding and local Core diagnostics are active. Agent, module,
plugin and workflow generators remain deferred until they have authoritative
contracts and complete outputs. Update, backup and restore operations require
separate threat models and transactional implementations.

The Judicial Intelligence extension is specified as a disabled composition
profile. Its application runtime remains external and must not introduce
project-specific logic into the framework core.

Local TXT/Markdown processing and in-memory lexical retrieval are active.
Rich-document extraction, OCR, semantic retrieval, generation, memory and graph
adapters remain deferred.

Task lifecycle validation and approval recording are active in memory.
Multi-agent planning, execution, retries, concurrency, persistence and
publication remain deferred pending a sandbox and durable audit design.

A local read-only API preview now exposes health, projects and lexical
retrieval. The next useful backend slice is persistent project storage with a
transactional migration and tested backup/restore path. Authentication must be
implemented before any remote binding or mutating endpoint.

The framework remains pre-1.0. Portal, multi-tenancy, SSO, billing, marketplace,
distributed execution and enterprise-compliance claims are deferred until
working vertical slices and operational evidence exist.

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
