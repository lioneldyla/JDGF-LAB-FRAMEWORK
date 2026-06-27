# Advanced RAG Engine

## Status

The Advanced RAG Engine is a validated capability specification. It is not an
installed runtime: every external adapter and memory backend remains disabled
until an implementation, security review and integration test exist.

## Contract

The capability is governed by four layers:

1. `manifests/rag-engine.yaml` declares lifecycle, installability and entry
   points;
2. `registry/rag.yaml` versions components, capabilities and dependencies;
3. `platform/rag/compatibility.yaml` defines supported API and contract
   versions;
4. JSON Schemas reject unknown fields, incorrect types and incomplete
   documents.

Contract version `1.0` follows semantic versioning. The validator accepts only
the current contract version and explicitly supported API versions. A future
contract requires a compatibility-policy update and migration documentation.

## Expected behavior

The intended runtime will provide citation-aware, explainable and governed
retrieval-augmented generation for generic organizational knowledge.

## Contract flow

```text
question -> hybrid retrieval -> reranking -> context building
         -> citation composition -> answer validation -> confidence result
```

The registry declares nine component configurations. JSON Schemas validate the
manifest, registry, engine and every component before the control plane reports
success.

### Declared capabilities

- lexical, semantic, hybrid and graph retrieval;
- evidence reranking and citation-preserving context construction;
- explicit citations, confidence thresholds and limitations;
- optional memory and graph adapters, disabled by default;
- source alignment, contradiction and unsupported-claim checks.

## Not implemented

No retriever, reranker, embedding pipeline, graph traversal, model call,
persistent memory or answer-generation runtime is implemented. The product
demonstrator found in the reviewed source archive is not used as an
implementation because it performs only title matching and synthesized text
formatting.

All six external dependencies are explicitly registered as `unavailable`.
Every component has `experimental` maturity, the capability lifecycle remains
`specified`, and `installable` is `false`.

## Activation requirements

Runtime activation requires an adapter contract, secret-management strategy,
data-governance review, observable failure modes and integration tests. Merely
declaring a backend in configuration does not activate it.

Promotion to `active` additionally requires compatible component versions,
available mandatory dependencies and a maturity review from `experimental` to
at least `preview`.
