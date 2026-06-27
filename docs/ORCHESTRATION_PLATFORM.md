# Orchestration Platform

## Mission

The Orchestration Platform defines supervised routing and workflow contracts.
It does not coordinate running agents or execute workflow steps in this release.

## Contract architecture

```text
validated AI route aliases       disabled agent profiles
             \                         /
              router -> orchestrator contract
                            |
                            v
                  disabled workflow registry
                            |
                            v
                 mandatory human approval gate
```

## Foundation contracts

- one disabled master orchestrator;
- planner, executor, reviewer and publisher role references, all disabled;
- five disabled workflows: research, framework, publication, RAG and project;
- sequential execution plans with ordered dependencies;
- model routing through existing LiteLLM aliases rather than provider models;
- explicit human gates in every workflow;
- audit required but not falsely declared operational.

## Safety defaults

- execution, routes, fallback, agents, memory and monitoring disabled;
- no recursive workflows;
- maximum declared concurrency of one;
- manual triggers only;
- no workflow side effects;
- no empty runtime, planner, executor, reviewer, log or configuration trees.

## Runtime boundary

Activation requires a sandboxed engine, durable audit sink, permission
enforcement, cancellation and retry semantics, secret isolation, cycle and
resource limits, integration tests and human approval. Until then the platform
is `specified`, non-installable and non-executable.
