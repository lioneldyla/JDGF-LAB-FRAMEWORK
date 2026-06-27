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

## Adapters — deferred

Model gateways, databases, vector stores, automation, monitoring, APIs and user
interfaces will be introduced only through portable adapters backed by a real
use case, tests and operating documentation.

Named external projects and domain-specific business logic are outside the
framework repository. They may consume public contracts without becoming core
dependencies.
