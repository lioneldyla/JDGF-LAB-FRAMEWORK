# Agent Platform

## Mission

The Agent Platform defines portable profiles, capability declarations and
safety boundaries for future supervised agents. It does not implement an agent
runtime or autonomous orchestration.

## Contract flow

```text
agents/*/agent.yaml -> strict AgentProfile schema
          |                    |
          v                    v
   agent registry ----> control-plane validation
                               |
                               v
                    disabled execution boundary
```

## Specified profiles

- JDGF Architect;
- Research Architect;
- Coding Agent;
- Publication Agent;
- Benchmark Agent;
- Data Governance Agent.

These are reusable role contracts, not running identities. They contain no
project-specific corpus, credentials, prompts or persistent memory.

## Safety defaults

- every profile and tool is disabled;
- model selection uses validated LiteLLM route references, not hard-coded
  provider models;
- write, execute, delete and external-action permissions are empty or false;
- memory adapters are declared but disabled;
- network access and unattended execution are forbidden;
- human approval is mandatory;
- no empty prompt, skill, log or memory directories are generated.

## Runtime boundary

Activation requires an execution engine, sandboxing, audit logs, prompt and
tool integrity controls, permission enforcement, red-team tests and explicit
human approval. Multi-agent coordination belongs to a separate orchestration
contract and remains disabled.
