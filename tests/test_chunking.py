from pathlib import Path

from app.chunking import chunk_document, parse_frontmatter, read_document, window_words


def test_parse_frontmatter() -> None:
    metadata, body = parse_frontmatter(
        '---\ntitle: "Example"\nlicense: "MIT"\n---\n\n# Heading\nBody'
    )
    assert metadata == {"title": "Example", "license": "MIT"}
    assert body.startswith("# Heading")


def test_word_windows_overlap() -> None:
    windows = window_words(" ".join(f"w{i}" for i in range(20)), max_words=10, overlap_words=2)
    assert windows[0].split()[-2:] == windows[1].split()[:2]


def test_chunk_ids_are_stable(tmp_path: Path) -> None:
    source = tmp_path / "runbook.md"
    source.write_text("# Runbook\n\n## Check\n\nInspect service endpoints.", encoding="utf-8")
    document = read_document(source)
    first = chunk_document(document, tmp_path)
    second = chunk_document(document, tmp_path)
    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert first[0].source_path == "runbook.md"

