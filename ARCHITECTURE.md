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

The initial control plane reads `registry/projects.yaml`, resolves each
manifest within the repository and validates the required project contract.
Paths that escape the repository are rejected. A registry identifier must
match the identifier declared by its manifest.

```text
registry/projects.yaml
        |
        v
projects/<name>/project.yaml --> contract validation --> CLI result
```

## Deferred capabilities

Agent execution, orchestration engines, application services, portals, SDKs and
release automation remain architectural placeholders. Database, vector-store,
automation and monitoring contracts now exist, but their runtimes remain
inactive until integration and recovery tests provide operational evidence.

## Specified slice: Advanced RAG contracts

The RAG capability manifest resolves an engine definition and component
registry. Each component configuration is schema-validated and repository
bound. This slice defines portable contracts only: storage, model and graph
adapters are disabled and the capability is not installable.

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

## Governance invariants

- Configuration contains no secrets.
- Consequential external actions require an explicit human gate.
- Every active component has an owner and lifecycle state.
- Registries are deterministic and reviewable in Git.
- Integrations are portable and never depend on a developer's absolute path.
