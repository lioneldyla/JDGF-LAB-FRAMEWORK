# SDK and CLI Platform

## Scope

The SDK exposes one production-quality generator: `scaffold-project`. It creates
a proposed project atomically, validates the generated manifest against the
authoritative project schema and never edits the project registry implicitly.

```bash
.venv/bin/jdgf scaffold-project new-project \
  --name "New Project" \
  --owner "Accountable owner"
```

The generated project must be reviewed before a maintainer adds it to
`registry/projects.yaml`. Existing destinations are never overwritten and
identifiers cannot contain path separators.

Agent, module, plugin and workflow generators remain deferred. Adding them
requires an authoritative schema, a complete non-empty output and adversarial
tests; empty directory scaffolds are not SDK implementations.

## Contracts

- `sdk/sdk.yaml` defines generator lifecycle and safety properties.
- `registry/sdk.yaml` exposes implemented commands.
- `manifests/sdk-platform.yaml` declares platform readiness.
