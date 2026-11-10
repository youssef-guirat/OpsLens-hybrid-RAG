from typing import Any

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    section: str | None = None
    content: str
    source_path: str
    source_url: str | None = None
    license: str | None = None
    content_hash: str
    embedding: list[float] = Field(default_factory=list, exclude=True)


class RetrievalHit(BaseModel):
    chunk: Chunk
    rank: int
    rrf_score: float
    dense_score: float | None = None
    sparse_score: float | None = None
    reranker_score: float | None = None


class Citation(BaseModel):
    number: int
    document_id: str
    chunk_id: str
    title: str
    section: str | None = None
    source_path: str
    source_url: str | None = None
    quote: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2_000)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    query: str
    results: list[RetrievalHit]
    latency_ms: float


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)
    top_k: int = Field(default=5, ge=1, le=10)


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    mode: str
    retrieval_latency_ms: float
    generation_latency_ms: float
    trace_id: str


class HealthResponse(BaseModel):
    status: str
    indexed_chunks: int
    embedding_model: str
    reranker_enabled: bool
    answer_mode: str


class IndexPayload(BaseModel):
    schema_version: int = 1
    built_at: str
    embedding_model: str
    source_dir: str
    chunks: list[Chunk]
    metadata: dict[str, Any] = Field(default_factory=dict)
