"""Small, deterministic retrieval slice for the otherwise specified RAG engine."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

TOKEN = re.compile(r"\w+(?:['-]\w+)*", re.UNICODE)


@dataclass(frozen=True)
class EvidenceDocument:
    id: str
    title: str
    source: str
    content: str


@dataclass(frozen=True)
class RetrievalHit:
    document_id: str
    title: str
    source: str
    score: float
    matched_terms: tuple[str, ...]
    excerpt: str


class RagRuntimeError(ValueError):
    """Raised when local retrieval input is invalid."""


def _terms(value: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return tuple(TOKEN.findall(normalized))


def lexical_retrieve(
    query: str, documents: Iterable[EvidenceDocument], *, top_k: int = 5
) -> tuple[RetrievalHit, ...]:
    """Rank in-memory documents by query-term coverage with stable citations."""

    query_terms = set(_terms(query))
    if not query_terms:
        raise RagRuntimeError("Retrieval query must contain searchable terms")
    if top_k < 1:
        raise RagRuntimeError("top_k must be at least 1")

    hits: list[RetrievalHit] = []
    seen: set[str] = set()
    for document in documents:
        if not all(
            value.strip()
            for value in (
                document.id,
                document.title,
                document.source,
                document.content,
            )
        ):
            raise RagRuntimeError(
                "Evidence documents require id, title, source and content"
            )
        if document.id in seen:
            raise RagRuntimeError(f"Duplicate evidence document id: {document.id}")
        seen.add(document.id)
        document_terms = set(_terms(document.content))
        matched = tuple(sorted(query_terms & document_terms))
        if not matched:
            continue
        score = len(matched) / len(query_terms)
        excerpt = " ".join(document.content.split())[:300]
        hits.append(
            RetrievalHit(
                document_id=document.id,
                title=document.title,
                source=document.source,
                score=score,
                matched_terms=matched,
                excerpt=excerpt,
            )
        )
    hits.sort(key=lambda hit: (-hit.score, hit.document_id))
    return tuple(hits[:top_k])
