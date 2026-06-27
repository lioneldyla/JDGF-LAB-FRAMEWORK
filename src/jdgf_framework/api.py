"""Loopback-only preview API over implemented JDGF control-plane capabilities."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from .core_platform import CorePlatformError, run_doctor
from .projects import RegistryError, load_project_registry, repository_root
from .rag_runtime import EvidenceDocument, RagRuntimeError, lexical_retrieve


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(StrictModel):
    status: str
    version: str
    checks: list[str]


class ProjectResponse(StrictModel):
    id: str
    name: str
    version: str
    lifecycle: str
    owner: str


class EvidenceInput(StrictModel):
    id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,127}$")]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    source: Annotated[str, Field(min_length=1, max_length=500)]
    content: Annotated[str, Field(min_length=1, max_length=100_000)]


class LexicalSearchRequest(StrictModel):
    query: Annotated[str, Field(min_length=1, max_length=500)]
    top_k: Annotated[int, Field(ge=1, le=20)] = 5
    documents: Annotated[list[EvidenceInput], Field(min_length=1, max_length=50)]


class RetrievalHitResponse(StrictModel):
    document_id: str
    title: str
    source: str
    score: float
    matched_terms: list[str]
    excerpt: str


class LexicalSearchResponse(StrictModel):
    query: str
    hits: list[RetrievalHitResponse]


def create_app(root: Path | None = None) -> FastAPI:
    """Build the API for one explicit framework repository root."""

    framework_root = (root or repository_root()).resolve()
    app = FastAPI(
        title="JDGF Lab Framework API",
        version=__version__,
        description="Local read-only preview API for implemented JDGF capabilities.",
    )
    app.state.framework_root = framework_root

    @app.get("/healthz", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        try:
            report = run_doctor(framework_root)
        except CorePlatformError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return HealthResponse(
            status="ok", version=report.version, checks=list(report.checks)
        )

    @app.get(
        "/api/v1/projects", response_model=list[ProjectResponse], tags=["projects"]
    )
    def projects() -> list[ProjectResponse]:
        try:
            records = load_project_registry(framework_root)
        except RegistryError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return [
            ProjectResponse(
                id=record.project_id,
                name=record.name,
                version=record.version,
                lifecycle=record.lifecycle,
                owner=record.owner,
            )
            for record in records
        ]

    @app.post(
        "/api/v1/retrieval/lexical",
        response_model=LexicalSearchResponse,
        tags=["retrieval"],
    )
    def lexical_search(request: LexicalSearchRequest) -> LexicalSearchResponse:
        documents = (
            EvidenceDocument(
                id=document.id,
                title=document.title,
                source=document.source,
                content=document.content,
            )
            for document in request.documents
        )
        try:
            hits = lexical_retrieve(request.query, documents, top_k=request.top_k)
        except RagRuntimeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return LexicalSearchResponse(
            query=request.query,
            hits=[
                RetrievalHitResponse(
                    document_id=hit.document_id,
                    title=hit.title,
                    source=hit.source,
                    score=hit.score,
                    matched_terms=list(hit.matched_terms),
                    excerpt=hit.excerpt,
                )
                for hit in hits
            ],
        )

    return app
