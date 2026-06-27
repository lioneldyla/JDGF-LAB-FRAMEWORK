# Contributing

JDGF Lab Framework evolves through small, validated vertical slices.

## Workflow

1. Create a focused branch from the latest stable baseline.
2. Add or update a versioned contract before implementing a capability.
3. Add positive and adversarial tests.
4. Run `./verify.sh` and `git diff --check`.
5. Document lifecycle, dependencies, security implications and limitations.

Do not commit secrets, generated artifacts, empty scaffolding, machine-specific
paths or project-specific business logic. External services remain disabled
until their adapters and integration tests are complete.
