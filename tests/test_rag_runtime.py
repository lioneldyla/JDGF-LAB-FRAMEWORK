import pytest

from jdgf_framework.rag_runtime import (
    EvidenceDocument,
    RagRuntimeError,
    lexical_retrieve,
)

DOCUMENTS = (
    EvidenceDocument(
        id="doc-b",
        title="Governance",
        source="docs/governance.md",
        content="Data governance requires accountable stewardship.",
    ),
    EvidenceDocument(
        id="doc-a",
        title="Justice",
        source="docs/justice.md",
        content="Digital justice requires governed data and transparent evidence.",
    ),
)


def test_lexical_retrieval_is_ranked_and_cited() -> None:
    hits = lexical_retrieve("governed data evidence", DOCUMENTS)

    assert [hit.document_id for hit in hits] == ["doc-a", "doc-b"]
    assert hits[0].score == 1.0
    assert hits[0].source == "docs/justice.md"
    assert hits[0].matched_terms == ("data", "evidence", "governed")


def test_lexical_retrieval_is_deterministic_for_ties() -> None:
    documents = tuple(reversed(DOCUMENTS))

    hits = lexical_retrieve("data", documents)

    assert [hit.document_id for hit in hits] == ["doc-a", "doc-b"]


def test_lexical_retrieval_honors_top_k() -> None:
    assert len(lexical_retrieve("data", DOCUMENTS, top_k=1)) == 1


def test_lexical_retrieval_rejects_blank_query() -> None:
    with pytest.raises(RagRuntimeError, match="searchable terms"):
        lexical_retrieve("---", DOCUMENTS)


def test_lexical_retrieval_rejects_duplicate_ids() -> None:
    duplicate = (DOCUMENTS[0], DOCUMENTS[0])

    with pytest.raises(RagRuntimeError, match="Duplicate"):
        lexical_retrieve("data", duplicate)


def test_lexical_retrieval_returns_no_false_positive() -> None:
    assert lexical_retrieve("unmatched", DOCUMENTS) == ()
