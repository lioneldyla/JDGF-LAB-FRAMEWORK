# Framework Core Platform

## Scope

The Framework Core is the existing Python control plane and its lifecycle
entry points. It does not introduce a second configuration system. `VERSION`,
`pyproject.toml`, `manifests/framework.yaml` and the registries remain the
authoritative sources.

The local doctor is deliberately read-only and offline:

```bash
.venv/bin/jdgf doctor
```

It verifies Python compatibility, version consistency, the locked environment
and Core contracts. Docker is not a framework-wide prerequisite because all
container adapters remain optional.

Update, backup and restore are deferred. The framework does not run implicit
`git pull`, archive the working tree wholesale or extract untrusted archives
over the repository. Release-candidate packaging remains the explicit,
approval-gated DevSecOps operation.
