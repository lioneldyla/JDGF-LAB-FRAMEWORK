# Governance Platform

## Mission

The Governance Platform declares reviewable policies and connects
machine-verifiable rules to local evidence. It does not claim that policy text
alone provides RBAC, compliance, auditability, encryption or backups.

## Policy model

```text
policy declaration -> lifecycle status -> enforcement mode -> evidence paths
                                                   |
                                                   v
                                      control-plane validation
```

Nine policy contracts cover access control, data, AI, security, versioning,
documentation, quality, backup and release governance.

## Enforcement truthfulness

Every rule declares:

- `schema`, `test`, `manual` or `runtime` enforcement;
- whether that enforcement is implemented;
- repository-bound evidence when implementation is claimed.

The validator rejects implemented rules without evidence and rejects evidence
claims for unimplemented rules. Runtime rules remain unimplemented.

## Current boundary

- contract and adversarial-test evidence: available;
- human approval defaults: validated;
- secret-free examples and loopback service bindings: tested;
- RBAC runtime: unavailable;
- durable audit sink: unavailable;
- encryption verification: unavailable;
- backup and restoration automation: unavailable;
- signed releases and automated deployment: unavailable.

Policies remain in `draft` or `review`, disabled and non-installable until an
authorized approval process and real enforcement adapters exist.
