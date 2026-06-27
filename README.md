# JDGF Lab Framework

JDGF Lab Framework is an independent, manifest-driven foundation for governed
AI projects. Its first executable slice provides a project contract, a central
registry and a local validation CLI.

The repository intentionally contains only implemented artifacts. A component
becomes supported when it has a contract, tests and an explicit lifecycle.

## Current foundation

- Project manifests live in `projects/<project>/project.yaml`.
- `registry/projects.yaml` is the authoritative project index.
- JSON Schemas enforce the registry and project manifest contracts.
- `jdgf validate` checks registry, schema and manifest integrity.
- `jdgf projects` lists registered projects.

## Quick start

[`uv`](https://docs.astral.sh/uv/) is required. The bootstrap selects Python
3.12 and installs the exact dependency set recorded in `uv.lock`.

```bash
./bootstrap.sh
.venv/bin/jdgf projects
./verify.sh
```

## Add a project

1. Copy `projects/example_project` to a new directory.
2. Give the project a unique lowercase identifier.
3. Add its manifest path to `registry/projects.yaml`.
4. Run `.venv/bin/jdgf validate`.

External products are intentionally not coupled to the framework at this
stage. Future integrations must use explicit adapters and portable
configuration rather than machine-specific paths.

## Roadmap principle

Development proceeds in thin, validated slices:

1. project registry and contracts;
2. governance policies and decision records;
3. agent capability contracts;
4. workflow orchestration;
5. knowledge and infrastructure adapters.

See [ARCHITECTURE.md](ARCHITECTURE.md) for boundaries and design rules and
[ROADMAP.md](ROADMAP.md) for capability sequencing.
The filtered integration record for the historical specification archive is in
[docs/ARCHIVE_INTEGRATION.md](docs/ARCHIVE_INTEGRATION.md).
