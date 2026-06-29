# Security policy

## Supported versions

JDGF Lab Framework is a developer preview. Only the current default branch is
maintained; no production support or response-time commitment is offered.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for this repository. Do not place
secrets, exploit details or personal data in a public issue.

Include the affected version, reproduction conditions, impact and any proposed
mitigation. Maintainers will acknowledge the report when available.

## Verified repository controls

As audited on 2026-06-28, GitHub Secret Scanning, push protection, Dependabot
alerts and security updates, private vulnerability reporting, and full-SHA
workflow pin enforcement are enabled. Dependency and workflow checks also run
locally and in CI.

Branch protection is not currently enabled. The repository must not claim that
control until GitHub reports it active.

The local API is unauthenticated and loopback-only. It must not be exposed to a
network until authentication, authorization, rate limiting and durable audit
are implemented and reviewed.
