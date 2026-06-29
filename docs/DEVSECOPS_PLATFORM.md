# DevSecOps Platform

## Mission

The DevSecOps Platform provides least-privilege continuous integration,
dependency auditing and verified Python package candidates. It does not deploy
services or publish releases.

## Pipelines

- Continuous integration runs lint, all contract tests and dependency audits.
- Container contract validation renders Compose definitions without starting
  the service stack.
- Release candidate builds run manually and upload wheel, source distribution
  and SHA-256 sums with seven-day retention.

## Supply-chain controls

- GitHub Actions are pinned by full commit SHA.
- Workflow token permissions are limited to `contents: read`.
- Checkout credentials are not persisted.
- Python and uv versions come from repository contracts.
- Dependencies are synchronized from `uv.lock` with `--frozen`.
- Dependabot monitors the `uv` and GitHub Actions ecosystems weekly.
- Every workflow file must be registered; undeclared automation is rejected.
- CI failures, audit findings and missing artifacts are never suppressed.
- Strict mypy analysis covers every packaged Python module.
- Tracked secret-bearing filenames and private-key headers are rejected.

## Honest delivery boundary

The repository has no first-party Dockerfile, deployment target, package index
credentials or signing identity. Consequently this release does not build or
push container images, publish packages, create GitHub releases, sign artifacts
or deploy to staging/production.

Hosted workflow execution must succeed on GitHub before this platform can move
from `specified` to `active` or become installable.
