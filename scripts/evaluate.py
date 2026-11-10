import argparse
import json
from pathlib import Path

from app.config import get_settings
from app.indexing import load_index
from app.retrieval import HybridRetriever


def reciprocal_rank(paths: list[str], expected: set[str]) -> float:
    for rank, path in enumerate(paths, start=1):
        if path in expected:
            return 1.0 / rank
    return 0.0


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Run retrieval evaluation")
    parser.add_argument("--dataset", type=Path, default=Path("data/evals/golden.jsonl"))
    parser.add_argument("--minimum-hit-rate", type=float, default=0.70)
    parser.add_argument("--output", type=Path, default=Path("docs/eval-report.json"))
    args = parser.parse_args()

    index = load_index(settings.index_path)
    retriever = HybridRetriever(
        index.chunks,
        embedding_model=index.embedding_model,
        reranker_model=settings.reranker_model,
        enable_reranker=settings.enable_reranker,
        rrf_k=settings.rrf_k,
    )
    cases = [
        json.loads(line)
        for line in args.dataset.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    outcomes = []
    for case in cases:
        hits, latency_ms = retriever.retrieve(
            case["question"],
            dense_top_k=settings.dense_top_k,
            sparse_top_k=settings.sparse_top_k,
            final_top_k=5,
        )
        paths = [hit.chunk.source_path for hit in hits]
        expected = set(case["expected_sources"])
        rr = reciprocal_rank(paths, expected)
        outcomes.append(
            {
                "id": case["id"],
                "hit_at_5": rr > 0,
                "reciprocal_rank": rr,
                "latency_ms": round(latency_ms, 2),
                "retrieved": paths,
            }
        )

    hit_rate = sum(item["hit_at_5"] for item in outcomes) / len(outcomes)
    mrr = sum(item["reciprocal_rank"] for item in outcomes) / len(outcomes)
    report = {
        "cases": len(outcomes),
        "hit_rate_at_5": round(hit_rate, 4),
        "mrr": round(mrr, 4),
        "passed": hit_rate >= args.minimum_hit_rate,
        "outcomes": outcomes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

