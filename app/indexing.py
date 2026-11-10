import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from app.chunking import load_and_chunk
from app.models import IndexPayload


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 50,
        )
        return vectors.tolist()


def build_index(
    source_dir: Path,
    index_path: Path,
    embedding_model: str,
    embedder: Embedder | None = None,
) -> IndexPayload:
    chunks = load_and_chunk(source_dir)
    if not chunks:
        raise ValueError(f"No Markdown documents found in {source_dir}")

    active_embedder = embedder or SentenceTransformerEmbedder(embedding_model)
    vectors = active_embedder.encode([chunk.content for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("Embedding model returned a different number of vectors than chunks")
    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk.embedding = vector

    payload = IndexPayload(
        built_at=datetime.now(UTC).isoformat(),
        embedding_model=embedding_model,
        source_dir=str(source_dir),
        chunks=chunks,
        metadata={
            "document_count": len({chunk.document_id for chunk in chunks}),
            "chunk_count": len(chunks),
        },
    )
    index_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = payload.model_dump()
    # Embeddings are excluded from normal API serialization but are required in
    # the persisted index used by the retriever.
    serialized["chunks"] = [
        {**chunk.model_dump(), "embedding": chunk.embedding} for chunk in payload.chunks
    ]
    index_path.write_text(json.dumps(serialized, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def load_index(index_path: Path) -> IndexPayload:
    if not index_path.exists():
        raise FileNotFoundError(
            f"Index not found at {index_path}. Run `python -m scripts.build_index` first."
        )
    return IndexPayload.model_validate_json(index_path.read_text(encoding="utf-8"))

