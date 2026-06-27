# JDGF Data Platform

## Status

The data platform is a specified, opt-in adapter set. Compose contracts and
health checks are validated; no database is enabled, installed or claimed as
runtime-tested by the baseline.

## Responsibilities

- PostgreSQL: relational metadata, projects, configuration and audit records.
- Neo4j: generic entity and relationship graphs.
- Qdrant: vector collections and retrieval indexes.
- Redis: ephemeral cache, queues, rate limits and short-lived context.

Application schemas remain outside infrastructure configuration. Domain data
models belong to independent consuming projects.

## Security defaults

- immutable version-and-digest image references;
- loopback-only host ports;
- blank example secrets with installer-enforced minimum lengths;
- authentication required for all four services;
- Qdrant CORS disabled;
- named persistent volumes and no host backup-directory mount;
- services registered as `specified` and `enabled: false`.

## Backup boundary

Named volumes provide persistence, not backups. Operators must implement and
test encrypted exports before activation:

- `pg_dump` and restore verification for PostgreSQL;
- `neo4j-admin database dump` and restore verification for Neo4j;
- Qdrant snapshots with authenticated retrieval;
- Redis RDB/AOF export only when cached data requires recovery.

Backup files, retention, encryption keys and remote storage are never committed
to this repository.

## Data flow

```text
AI and application adapters
        |
        +-- PostgreSQL (relational)
        +-- Neo4j     (graph)
        +-- Qdrant    (vector)
        +-- Redis     (ephemeral cache)
```
