import re
from collections import defaultdict
from collections.abc import Sequence
from time import perf_counter
from typing import Protocol

import numpy as np
from rank_bm25 import BM25Okapi

from app.models import Chunk, RetrievalHit

TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:/-]*")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def ranked_indices(scores: Sequence[float], top_k: int) -> list[int]:
    return sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[:top_k]


def reciprocal_rank_fusion(rankings: Sequence[Sequence[int]], k: int = 60) -> dict[int, float]:
    fused: dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, item_index in enumerate(ranking, start=1):
            fused[item_index] += 1.0 / (k + rank)
    return dict(fused)


class QueryEmbedder(Protocol):
    def encode_query(self, query: str) -> np.ndarray: ...


class SentenceTransformerQueryEmbedder:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def encode_query(self, query: str) -> np.ndarray:
        return np.asarray(self.model.encode(query, normalize_embeddings=True), dtype=np.float32)


class Reranker(Protocol):
    def score(self, query: str, passages: list[str]) -> list[float]: ...


class CrossEncoderReranker:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(model_name)

    def score(self, query: str, passages: list[str]) -> list[float]:
        values = self.model.predict([(query, passage) for passage in passages])
        return [float(value) for value in values]


class HybridRetriever:
    """BM25 + dense retrieval, RRF fusion, and optional cross-encoder reranking."""

    def __init__(
        self,
        chunks: list[Chunk],
        embedding_model: str,
        reranker_model: str,
        enable_reranker: bool = True,
        rrf_k: int = 60,
        query_embedder: QueryEmbedder | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        if not chunks:
            raise ValueError("Retriever requires at least one indexed chunk")
        self.chunks = chunks
        self.rrf_k = rrf_k
        self._bm25 = BM25Okapi([tokenize(chunk.content) for chunk in chunks])
        self._matrix = np.asarray([chunk.embedding for chunk in chunks], dtype=np.float32)
        if self._matrix.ndim != 2 or not self._matrix.shape[1]:
            raise ValueError("Index contains invalid or missing embeddings")
        self._query_embedder = query_embedder or SentenceTransformerQueryEmbedder(
            embedding_model
        )
        self._reranker = (
            reranker
            if reranker is not None
            else CrossEncoderReranker(reranker_model)
            if enable_reranker
            else None
        )

    def retrieve(
        self,
        query: str,
        dense_top_k: int = 12,
        sparse_top_k: int = 12,
        final_top_k: int = 5,
    ) -> tuple[list[RetrievalHit], float]:
        started = perf_counter()
        sparse_scores = np.asarray(self._bm25.get_scores(tokenize(query)), dtype=np.float32)
        query_vector = self._query_embedder.encode_query(query)
        dense_scores = self._matrix @ query_vector

        dense_ranking = ranked_indices(dense_scores, min(dense_top_k, len(self.chunks)))
        sparse_ranking = ranked_indices(sparse_scores, min(sparse_top_k, len(self.chunks)))
        fused = reciprocal_rank_fusion([dense_ranking, sparse_ranking], self.rrf_k)
        candidates = sorted(fused, key=fused.get, reverse=True)

        reranker_scores: dict[int, float] = {}
        if self._reranker and candidates:
            values = self._reranker.score(
                query, [self.chunks[index].content for index in candidates]
            )
            reranker_scores = dict(zip(candidates, values, strict=True))
            candidates.sort(key=lambda index: reranker_scores[index], reverse=True)

        selected = candidates[: min(final_top_k, len(candidates))]
        hits = [
            RetrievalHit(
                chunk=self.chunks[index],
                rank=rank,
                rrf_score=fused[index],
                dense_score=float(dense_scores[index]),
                sparse_score=float(sparse_scores[index]),
                reranker_score=reranker_scores.get(index),
            )
            for rank, index in enumerate(selected, start=1)
        ]
        return hits, (perf_counter() - started) * 1000

