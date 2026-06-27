# Release Readiness Criteria

## Current classification

JDGF Lab Framework `0.10.0` is a local developer preview. It is not a stable,
production or enterprise release.

## Required before 1.0

A stable 1.0 release requires evidence for all of the following:

1. a supported public API and compatibility policy;
2. authenticated and authorized access for every non-local or mutating API;
3. persistent storage with migrations, backup and tested restoration;
4. threat model, dependency review and secret-management design;
5. integration tests for each enabled external adapter;
6. operational telemetry, resource limits and documented failure modes;
7. signed, reproducible release artifacts and an authorized publication path;
8. upgrade, rollback and disaster-recovery exercises;
9. hosted CI evidence on supported platforms;
10. removal or disposition of repository-local legacy artifacts.

Directories, YAML declarations, generated OpenAPI documentation and successful
unit tests are necessary evidence, but they do not independently establish
production readiness or compliance.
