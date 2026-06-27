# Runtime Control Platform

## Implemented scope

The Runtime Control Platform validates a side-effect-free task lifecycle:

```text
proposed -> validated -> awaiting-approval -> approved
    |           |                |                |
    +-----------+----------------+----------> cancelled
```

Approval requires a non-empty decision reference. Transitions return immutable
task and event records and are not persisted.

## Explicit boundary

This is not a multi-agent executor. Planning, supervision, execution, review,
publication, scheduling, model routing and event transport remain disabled.
There is no network access, tool invocation, retry loop, concurrency, durable
audit or unattended operation.
