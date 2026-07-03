# JDGF Lab Framework

> A modular, governed framework for AI-assisted projects, knowledge systems and
> data-governance research.

## Vision

JDGF Lab Framework is an open and extensible control framework for declaring,
validating and operating AI-assisted projects. Domain products remain
independent consumers connected through versioned manifests and adapters.

The framework is designed to support:

- AI and knowledge engineering;
- data governance and public-sector innovation;
- reproducible research automation;
- multi-agent and workflow contracts;
- retrieval-augmented generation;
- project governance and controlled releases.

## Core principles

- Modular and open source
- Contracts and documentation first
- Security and governance by design
- Local first and cloud portable
- Reproducible and versioned
- Human approval for consequential actions
- No project-specific business logic in the core

## Current foundation

The executable `v0.10.0` developer preview provides:

- an active Projects Platform with versioned manifests, governance and
  documentation boundaries;
- JSON Schema validation through the `jdgf` CLI;
- repository-bound path and identifier checks;
- a locked Python 3.12 environment;
- an experimental Advanced RAG contract set with nine validated components;
- pinned, hardened Docker contracts for Ollama and LiteLLM, disabled by default;
- pinned AI interface contracts for Open WebUI and gated OpenHands Docker use;
- schema-validated PostgreSQL, Redis, Neo4j and Qdrant service contracts;
- opt-in n8n, SearXNG, Prometheus, Grafana and Loki service contracts.
- a schema-validated, corpus-neutral Knowledge Platform foundation.
- six schema-validated Agent Platform profiles, disabled by default.
- five supervised orchestration workflow contracts with execution disabled.
- nine evidence-aware governance policy contracts without runtime enforcement.
- least-privilege CI, dependency auditing and release-candidate packaging.
- a safe project scaffolder and an offline framework doctor.
- a disabled Judicial Intelligence extension profile that composes existing
  Knowledge and RAG contracts without importing project-specific logic.
- bounded TXT/Markdown processing with schema-compatible metadata and stable
  chunks.
- deterministic in-memory lexical retrieval with source citations.
- an approval-gated, side-effect-free task lifecycle controller.
- a loopback-only FastAPI service for health, project discovery and bounded
  lexical retrieval.

Semantic RAG, answer generation, multi-agent execution and every external
service adapter remain disabled until their implementations, security reviews
and integration tests exist.

## Architecture

```text
contracts -> registries -> control plane -> optional adapters -> projects
```

Dependencies point inward: projects may consume public JDGF contracts, while
the framework core never imports project-specific code.

## Repository structure

```text
docs/          Architecture and operating documentation
manifests/     Framework and capability declarations
platform/      Versioned platform contracts
projects/      Project manifests and copyable template
registry/      Authoritative indexes
scripts/       Controlled lifecycle helpers
src/           Python control plane
tests/         Contract and adversarial tests
```

Deferred directories are created only when a validated vertical slice requires
them; the repository does not use empty scaffolding to imply functionality.

## Adapter status

Ollama, LiteLLM, Open WebUI, PostgreSQL, Redis, Neo4j, Qdrant, n8n, SearXNG,
Prometheus, Grafana and Loki have versioned Compose contracts and explicit
installation scripts. OpenHands also has an opt-in Docker contract, but its
socket access requires explicit risk acceptance; its upstream `uv` launcher is
preferred. All service contracts remain disabled until runtime verification;
hosted model providers remain architectural candidates.

## Quick start

[`uv`](https://docs.astral.sh/uv/) is required.

```bash
./install.sh
.venv/bin/jdgf projects
.venv/bin/jdgf serve
./verify.sh
```

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Roadmap](ROADMAP.md)
- [Advanced RAG Engine](docs/ADVANCED_RAG_ENGINE.md)
- [Data Platform](docs/DATABASE_ARCHITECTURE.md)
- [Automation and Monitoring](docs/AUTOMATION_ARCHITECTURE.md)
- [Knowledge Platform](docs/KNOWLEDGE_PLATFORM.md)
- [Agent Platform](docs/AGENT_PLATFORM.md)
- [Orchestration Platform](docs/ORCHESTRATION_PLATFORM.md)
- [Governance Platform](docs/GOVERNANCE_PLATFORM.md)
- [DevSecOps Platform](docs/DEVSECOPS_PLATFORM.md)
- [SDK and CLI Platform](docs/SDK_PLATFORM.md)
- [Framework Core Platform](docs/FRAMEWORK_CORE_PLATFORM.md)
- [Judicial Intelligence Extension](docs/JUDICIAL_INTELLIGENCE_PLATFORM.md)
- [Document Processing Engine](docs/DOCUMENT_PROCESSING_ENGINE.md)
- [Runtime Control Platform](docs/RUNTIME_CONTROL_PLATFORM.md)
- [Local API Preview](docs/LOCAL_API.md)
- [Release Readiness Criteria](docs/RELEASE_CRITERIA.md)
- [Historical archive integration](docs/ARCHIVE_INTEGRATION.md)
- [JDGF concept note](docs/JDGF_CONCEPT_NOTE.md)
- [JDGF Lab Framework state audit](docs/JDGF_LAB_FRAMEWORK_STATE_AUDIT.md)
- [Judicial Intelligence extension plan](docs/JUDICIAL_INTELLIGENCE_EXTENSION_PLAN.md)
- [Next vertical slice](docs/NEXT_VERTICAL_SLICE.md)

## Version

`0.10.0`

## License

MIT License. See [LICENSE](LICENSE).
