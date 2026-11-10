import numpy as np

from app.models import Chunk
from app.retrieval import HybridRetriever, reciprocal_rank_fusion, tokenize


class FakeQueryEmbedder:
    def encode_query(self, query: str) -> np.ndarray:
        return np.asarray([1.0, 0.0], dtype=np.float32)


class FakeReranker:
    def score(self, query: str, passages: list[str]) -> list[float]:
        return [10.0 if "retry" in passage else 0.0 for passage in passages]


def make_chunk(chunk_id: str, content: str, embedding: list[float]) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_id=f"doc-{chunk_id}",
        title=chunk_id,
        section="test",
        content=content,
        source_path=f"{chunk_id}.md",
        content_hash="hash",
        embedding=embedding,
    )


def test_tokenize_preserves_operational_identifiers() -> None:
    assert "http-503" in tokenize("Investigate HTTP-503 and payment.service")
    assert "payment.service" in tokenize("Investigate HTTP-503 and payment.service")


def test_rrf_rewards_items_present_in_both_rankings() -> None:
    fused = reciprocal_rank_fusion([[1, 2, 3], [3, 1, 4]], k=60)
    assert fused[1] > fused[2]
    assert fused[3] > fused[4]


def test_hybrid_retrieval_applies_reranker() -> None:
    chunks = [
        make_chunk("semantic", "general payment guidance", [1.0, 0.0]),
        make_chunk("retry", "reduce retry concurrency", [0.0, 1.0]),
    ]
    retriever = HybridRetriever(
        chunks,
        embedding_model="unused",
        reranker_model="unused",
        query_embedder=FakeQueryEmbedder(),
        reranker=FakeReranker(),
    )
    hits, _ = retriever.retrieve("payment retry storm", final_top_k=2)
    assert hits[0].chunk.chunk_id == "retry"
    assert hits[0].reranker_score == 10.0

