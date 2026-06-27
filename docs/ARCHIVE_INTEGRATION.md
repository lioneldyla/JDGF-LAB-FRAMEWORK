# Historical archive integration

The `JDGF-LAB-FRAMEWORK-v2-complete-commits-000001-000031.zip` archive was
reviewed as a specification source. It is not a Git history and several of its
files explicitly describe scaffolds rather than executable, production-ready
components.

## Integrated

- the generic capability inventory was reconciled with the framework roadmap;
- project and registry contracts are enforced as JSON Schema;
- verification has a single failure-preserving entry point;
- deferred capabilities are recorded without being activated.

## Deliberately deferred

- agent execution and multi-agent runtime;
- knowledge, retrieval and document-processing engines;
- infrastructure and monitoring compositions;
- backend, identity, portal, SDK and release services;
- enterprise deployment features.

These areas require their own contracts, tests, security model and lifecycle
decision before code or configuration is imported.

## Deliberately excluded

- descriptors for named external projects;
- research-project and domain-specific application artifacts;
- scripts that suppress failures or mutate the host automatically;
- example credentials, hard-coded secrets and database URLs;
- placeholder APIs and Compose stacks presented without integration tests.

This filtering preserves JDGF Lab Framework as an autonomous, generic control
framework rather than a container for unrelated products.
