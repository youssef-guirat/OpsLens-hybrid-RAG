from uuid import uuid4

from app.answering import GroundedAnswerer
from app.config import Settings
from app.indexing import IndexPayload, load_index
from app.models import AskResponse, SearchResult
from app.retrieval import HybridRetriever


class OpsLensService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.index: IndexPayload = load_index(settings.index_path)
        self.retriever = HybridRetriever(
            chunks=self.index.chunks,
            embedding_model=self.index.embedding_model,
            reranker_model=settings.reranker_model,
            enable_reranker=settings.enable_reranker,
            rrf_k=settings.rrf_k,
        )
        self.answerer = GroundedAnswerer(settings.openai_api_key, settings.openai_model)

    def retrieve(self, query: str, top_k: int | None = None) -> SearchResult:
        hits, latency_ms = self.retriever.retrieve(
            query=query,
            dense_top_k=self.settings.dense_top_k,
            sparse_top_k=self.settings.sparse_top_k,
            final_top_k=top_k or self.settings.final_top_k,
        )
        return SearchResult(query=query, results=hits, latency_ms=latency_ms)

    def ask(self, question: str, top_k: int | None = None) -> AskResponse:
        search = self.retrieve(question, top_k)
        generated = self.answerer.answer(question, search.results)
        return AskResponse(
            answer=generated.answer,
            citations=generated.citations,
            mode=generated.mode,
            retrieval_latency_ms=search.latency_ms,
            generation_latency_ms=generated.latency_ms,
            trace_id=f"tr_{uuid4().hex}",
        )

