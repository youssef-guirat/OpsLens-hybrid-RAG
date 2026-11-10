import json
from pathlib import Path

from app.indexing import build_index, load_index


class FakeEmbedder:
    def encode(self, texts: list[str]) -> list[list[float]]:
        return [[float(index), 1.0] for index, _ in enumerate(texts, start=1)]


def test_build_index_persists_embeddings(tmp_path: Path) -> None:
    source_dir = tmp_path / "documents"
    source_dir.mkdir()
    (source_dir / "sample.md").write_text("# Sample\n\nEvidence lives here.", encoding="utf-8")
    index_path = tmp_path / "index.json"

    payload = build_index(source_dir, index_path, "fake-model", embedder=FakeEmbedder())
    raw = json.loads(index_path.read_text(encoding="utf-8"))
    loaded = load_index(index_path)

    assert payload.metadata["document_count"] == 1
    assert raw["chunks"][0]["embedding"] == [1.0, 1.0]
    assert loaded.chunks[0].embedding == [1.0, 1.0]

