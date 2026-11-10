import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from app import __version__
from app.config import get_settings
from app.models import (
    AskRequest,
    AskResponse,
    HealthResponse,
    SearchRequest,
    SearchResult,
)
from app.service import OpsLensService

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("opslens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("loading_index path=%s", settings.index_path)
    app.state.service = OpsLensService(settings)
    logger.info("index_loaded chunks=%s", len(app.state.service.index.chunks))
    yield


app = FastAPI(
    title="OpsLens API",
    description="Hybrid BM25 + semantic RAG with reranking and verified citations",
    version=__version__,
    lifespan=lifespan,
)


def service_from(request: Request) -> OpsLensService:
    return request.app.state.service


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health(request: Request) -> HealthResponse:
    service = service_from(request)
    return HealthResponse(
        status="ok",
        indexed_chunks=len(service.index.chunks),
        embedding_model=service.index.embedding_model,
        reranker_enabled=settings.enable_reranker,
        answer_mode=service.answerer.mode,
    )


@app.post("/api/v1/search", response_model=SearchResult, tags=["retrieval"])
def search(payload: SearchRequest, request: Request) -> SearchResult:
    try:
        return service_from(request).retrieve(payload.query, payload.top_k)
    except Exception as exc:
        logger.exception("search_failed")
        raise HTTPException(status_code=500, detail="Search failed") from exc


@app.post("/api/v1/ask", response_model=AskResponse, tags=["rag"])
def ask(payload: AskRequest, request: Request) -> AskResponse:
    try:
        return service_from(request).ask(payload.question, payload.top_k)
    except Exception as exc:
        logger.exception("answer_failed")
        raise HTTPException(status_code=500, detail="Answer generation failed") from exc


@app.get("/api/v1/sources", tags=["retrieval"])
def sources(request: Request) -> dict[str, list[dict[str, str | None]]]:
    service = service_from(request)
    unique: dict[str, dict[str, str | None]] = {}
    for chunk in service.index.chunks:
        unique.setdefault(
            chunk.document_id,
            {
                "document_id": chunk.document_id,
                "title": chunk.title,
                "source_path": chunk.source_path,
                "source_url": chunk.source_url,
                "license": chunk.license,
            },
        )
    return {"sources": list(unique.values())}
