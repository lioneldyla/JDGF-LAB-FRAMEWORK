# JDGF Automation and Monitoring Platform

## Status

This platform is a specified, opt-in set of adapters. Its Compose definitions,
configuration and contracts are validated, but no service is enabled or claimed
as runtime-tested.

## Components

- n8n defines local workflow execution backed by PostgreSQL and Redis.
- SearXNG provides private metasearch with a limiter and safe-search defaults.
- Prometheus collects metrics from endpoints that explicitly expose them.
- Grafana provisions Prometheus and Loki data sources.
- Loki stores logs, but no collector is included in this release.

```text
workflow clients ----> n8n ----> optional adapters
search clients ------> SearXNG

metric endpoints ----> Prometheus ----> Grafana
future log collector -> Loki ----------> Grafana
```

## Security defaults

- immutable image versions and digests;
- loopback-only host ports;
- external secrets with installer-enforced minimum lengths;
- anonymous Grafana access and user sign-up disabled;
- n8n diagnostics, personalization and environment access from code disabled;
- SearXNG limiter enabled and instance declared non-public;
- external JDGF network shared without implicit service startup.

The baseline n8n example reuses the `jdgf` PostgreSQL database and user with an
`n8n_` table prefix; its password must match the PostgreSQL deployment. Its
Redis password must likewise match the Redis deployment. Dedicated identities
and databases should replace this compatibility setup before production use.

## Honest monitoring boundary

The baseline provisions data sources, not dashboards or alerts. Loki has no log
collector, and raw or authenticated database endpoints are not misrepresented
as immediately scrapeable Prometheus targets. Runtime verification must be
completed before the manifest can become installable.
