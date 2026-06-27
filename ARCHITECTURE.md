# Architecture

## Design intent

JDGF is a control framework, not a monolithic application. It defines portable
contracts for projects, agents, workflows, knowledge and governance while
leaving execution engines behind adapters.

## Layers

1. **Contracts** — versioned YAML schemas and manifests.
2. **Registry** — authoritative indexes of available capabilities.
3. **Control plane** — validation, policy checks and lifecycle commands.
4. **Adapters** — optional integrations with model, data and automation
   services.
5. **Projects** — isolated consumers of framework capabilities.

Dependencies point inward: projects may depend on public JDGF contracts, while
the JDGF core must not import project-specific code.

## Active slice: project registry

The control plane reads `registry/projects.yaml`, resolves each manifest within
the repository and validates identity, version, lifecycle, governance,
architecture and documentation. Paths that escape the repository are rejected;
registry identity, version and lifecycle must match the manifest. Templates are
never registered.

```text
registry/projects.yaml
        |
        v
projects/<name>/project.yaml --> contract validation --> CLI result
```

## Deferred capabilities

Agent execution, orchestration engines, application services, portals and
release automation remain deferred. Agent profiles, database, vector-store,
automation and monitoring contracts now exist, but their runtimes remain
inactive until integration and recovery tests provide operational evidence.

## Specified engine with active local RAG slice

The RAG capability manifest resolves an engine definition and component
registry. Each component configuration is schema-validated and repository
bound. A deterministic in-memory lexical retriever preserves source citations;
storage, semantic, model and graph adapters remain disabled and the complete
capability is not installable.

## Specified slice: Docker service contracts

Ollama and LiteLLM have opt-in Compose definitions with immutable image
digests, loopback-only port bindings, health checks and an external JDGF
network. Their registry lifecycle is `specified` and `enabled` remains false;
operators must invoke the dedicated installers explicitly.

## Specified slice: AI interface contracts

Open WebUI is local-only with registration, sharing and web search disabled by
default. OpenHands is isolated behind an explicit dangerous profile because its
Docker deployment grants daemon-level authority through the Docker socket. Both
interfaces remain disabled and the AI platform is not installable.

## Specified slice: data service contracts

PostgreSQL, Redis, Neo4j and Qdrant have strict manifests, a typed service
registry and pinned Compose definitions. Ports bind only to loopback; password
or API-key authentication is required. Installation remains disabled at the
platform level until service health checks and backup restoration have been
tested with every component active.

## Specified slice: automation and monitoring contracts

n8n and SearXNG define local workflow and metasearch adapters. Prometheus,
Grafana and Loki define an observability foundation with explicit gaps for
dashboards, alerts and log collection. Every service remains local-only,
disabled and non-installable until integration tests demonstrate the complete
dependency chain.

## Specified slice: Knowledge Platform foundation

The Knowledge Platform validates generic ontologies, document metadata,
collection catalogs, indexing plans and RAG integration without owning a domain
corpus. All ingestion, vector and graph runtimes remain disabled; consuming
projects keep their source ownership and connect through versioned metadata.

## Specified slice: Agent Platform contracts

Six generic agent profiles declare capabilities, route references, tools,
memory and permissions. Profiles, tools and stores are disabled. The control
plane rejects write, execution, deletion, network and unattended authority;
there is no agent execution engine in this release.

## Specified slice: Orchestration Platform contracts

The orchestration layer defines a disabled router, orchestrator roles and five
sequential workflows. Every workflow ends in a human gate and has no declared
side effects. Runtime execution, recursion, concurrency, audit persistence and
agent coordination remain unavailable.

## Specified slice: Governance Platform contracts

Nine policies declare lifecycle, enforcement mode, implementation state and
local evidence. Validation prevents unsupported enforcement claims. RBAC,
durable audit, encryption verification, backups and release automation remain
unavailable runtime capabilities.

## Specified slice: DevSecOps contracts

Three least-privilege GitHub workflows define validation, container-contract
checks and manual release-candidate builds. Actions are SHA-pinned and
dependencies are lock-bound. Publishing, image pushes, signing and deployment
remain disabled because no authorized targets or credentials exist.

## Active slice: SDK and Framework Core

The SDK currently implements one validated vertical slice: atomic project
scaffolding without implicit registry mutation. The Core reuses existing
authoritative configuration and adds an offline, read-only doctor. Unsupported
generators, updates, backups and restores remain explicitly deferred.

## Specified extension: Judicial Intelligence

The optional Judicial Intelligence profile composes authoritative Knowledge
and RAG contracts. It remains disabled, non-installable and outside the generic
core boundary; it contains no consumer-project references or runtime claims.

## Active slice: local document processing

TXT and Markdown files can be processed within an explicit source boundary.
The engine normalizes text, fingerprints original bytes, emits Knowledge
Platform-compatible metadata and creates deterministic chunks. Rich formats,
OCR, archives, external connectors and persistence remain deferred.

## Active control slice: task lifecycle

The Runtime Control Platform implements immutable, side-effect-free lifecycle
transitions and an explicit approval reference. It does not execute agents or
tools. Planning, concurrency, persistence, model routing and publishing remain
deferred.

## Active preview slice: local API

A FastAPI application exposes health, registered projects and in-memory lexical
retrieval. The route registry is checked against generated application routes.
The CLI binds only to loopback, CORS is absent and no endpoint mutates framework
state. Authentication, persistence, uploads and remote deployment remain out of
scope until their security and operational contracts are implemented.

## Governance invariants

- Configuration contains no secrets.
- Consequential external actions require an explicit human gate.
- Every active component has an owner and lifecycle state.
- Registries are deterministic and reviewable in Git.
- Integrations are portable and never depend on a developer's absolute path.
