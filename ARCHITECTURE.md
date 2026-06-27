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

Agent execution, orchestration engines, databases, vector stores, automation,
monitoring, application services, portals, SDKs and release automation are
architectural placeholders. They remain inactive until a small use case
demonstrates the need and receives its own contract, tests and operating
documentation.

## Governance invariants

- Configuration contains no secrets.
- Consequential external actions require an explicit human gate.
- Every active component has an owner and lifecycle state.
- Registries are deterministic and reviewable in Git.
- Integrations are portable and never depend on a developer's absolute path.
