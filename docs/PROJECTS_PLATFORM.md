# Projects Platform

## Mission

The Projects Platform provides a standardized, schema-validated lifecycle for
framework project records. It does not host the source code or business logic
of independent products.

## Contract model

```text
projects/<record>/project.yaml
              |
              v
projects/project.schema.yaml
              |
              v
registry/projects.yaml -> control-plane validation
```

Each record declares:

- identity, semantic version, license and optional repository;
- lifecycle and accountable owner;
- human approval policy and optional governance roles;
- modules, services, data, knowledge and agent dependencies;
- framework capabilities consumed;
- release timeline and documentation paths.

## Repository boundary

Only `jdgf-framework` is registered here because it is the framework's own
record. `projects/example_project/` is a copyable, unregistered template.
External projects remain in independent repositories and may consume public
JDGF contracts without becoming core dependencies.

## Layout policy

A project record needs only a manifest and its referenced documentation. Empty
directory trees are not generated. Datasets, reports, agents or releases are
created by a consuming project only when implemented and governed.

## Lifecycle gates

- `proposed`: contract under review;
- `active`: owned, documented and eligible for registry inclusion;
- `paused`: temporarily inactive but retained;
- `retired`: immutable historical record;
- `template`: copyable example that cannot be registered.
