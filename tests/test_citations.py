from app.answering import build_citations, verified_quote
from app.models import Chunk, RetrievalHit


def test_citation_quote_is_exact_source_prefix() -> None:
    content = "Reduce retry concurrency before increasing upstream timeouts. " * 10
    chunk = Chunk(
        chunk_id="chk-1",
        document_id="doc-1",
        title="Retry runbook",
        section="Mitigation",
        content=content,
        source_path="runbooks/retry.md",
        content_hash="hash",
        embedding=[1.0, 0.0],
    )
    hit = RetrievalHit(chunk=chunk, rank=1, rrf_score=0.03)
    citation = build_citations([hit])[0]
    assert content.startswith(citation.quote.removesuffix("…"))
    assert citation.chunk_id == "chk-1"


def test_verified_quote_is_bounded() -> None:
    quote = verified_quote("word " * 200, max_chars=100)
    assert len(quote) <= 101
    assert quote.endswith("…")
