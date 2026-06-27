# JDGF Lab Framework Operating Guide

## Mission

JDGF Lab Framework is an independent, governed foundation for declaring and
operating AI-assisted projects. Keep the framework generic: domain projects
integrate through manifests and adapters, not through hard-coded paths or
project-specific business logic.

## Runtime

- Use the Python 3.12 environment managed by `uv`.
- Use the repository-local `.venv`.
- Keep `uv.lock` synchronized with `pyproject.toml`.
- Keep dependencies small and justified.
- Never commit secrets, `.env` files, local databases, logs, caches or virtual
  environments.

## Setup

```bash
./bootstrap.sh
```

## Validation

```bash
./verify.sh
```

## Change Policy

- Build the smallest complete vertical slice before adding infrastructure.
- Preserve declarative contracts in `projects/`, `registry/` and `manifests/`.
- Do not add placeholder directories for deferred infrastructure services.
- Do not introduce links to external projects without an explicit integration
  decision.
- Keep human approval gates for consequential external actions.
