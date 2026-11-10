# OpsLens

> A production-minded operations knowledge copilot built with hybrid retrieval, cross-encoder reranking, measurable evaluation, and verified citations.

OpsLens answers incident-response questions over runbooks, policies, postmortems, and open Kubernetes documentation. It combines BM25 keyword retrieval with local sentence-transformer embeddings, fuses both rankings with Reciprocal Rank Fusion (RRF), and reranks the best candidates before producing an evidence-backed response.

No paid LLM API is required. By default, OpsLens runs in free extractive mode using local models. OpenAI generation can be enabled through environment configuration.

## Why this is more than "chat with a PDF"

- **Real hybrid retrieval:** BM25 finds exact error codes, alert identifiers, and service names; sentence embeddings find semantically similar passages.
- **Rank fusion:** RRF combines rankings without assuming BM25 and cosine scores share the same scale.
- **Reranking:** a cross-encoder scores each query-passage pair before evidence reaches the answer layer.
- **Verified citations:** source IDs, sections, paths, URLs, and quotes come from stored chunks instead of model-generated metadata.
- **Provider-optional:** the complete retrieval pipeline works without an API key; OpenAI generation is optional.
- **Evaluated:** a versioned golden set reports Hit Rate@5 and Mean Reciprocal Rank.
- **Reproducible:** deterministic ingestion, pinned open documents, provenance records, tests, CI, Docker, and a locked dependency graph.

## Technology stack

| Area | Technology |
|---|---|
| API | FastAPI and Pydantic |
| Interface | Streamlit |
| Keyword retrieval | BM25 via `rank-bm25` |
| Semantic retrieval | `sentence-transformers/all-MiniLM-L6-v2` |
| Rank fusion | Reciprocal Rank Fusion |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Optional generation | OpenAI API |
| Packaging | `uv` and `uv.lock` |
| Quality | Pytest, Ruff, and GitHub Actions |

## Architecture

```text
Markdown + attributed open documents
                  |
           clean and chunk
                  |
       local embedding index
                  |
User question ----+------> BM25 ranking --------+
                  +------> semantic ranking ----+--> RRF fusion
                                                           |
                                                   cross-encoder
                                                      reranking
                                                           |
                                                  top evidence
                                                           |
                                      extractive or generated answer
                                                           |
                                               verified citations
```

See [docs/architecture.md](docs/architecture.md) for component and trust-boundary details.

## Quick start

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- Approximately 2 GB of free disk space for dependencies and local models

Use GitHub's **Code** button to clone or download the repository, then open a terminal in the repository root.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
uv sync --extra dev
uv run python -m scripts.build_index
```

### macOS or Linux

```bash
cp .env.example .env
uv sync --extra dev
uv run python -m scripts.build_index
```

The repository already contains the attributed documents used by the demo. Run `uv run python -m scripts.fetch_open_docs` only when intentionally refreshing the pinned Kubernetes documentation and provenance manifest.

The first index build downloads the local embedding model. The first query downloads the local reranker. Later runs reuse the local model cache.

## Run the application

Start the FastAPI backend:

```bash
uv run uvicorn app.main:app --reload
```

In another terminal, start the Streamlit interface:

```bash
uv run streamlit run ui/streamlit_app.py
```

Open:

- UI: <http://localhost:8501>
- API documentation: <http://localhost:8000/docs>
- Health endpoint: <http://localhost:8000/health>

## Try these questions

- How should we mitigate a payment retry storm?
- What should I inspect when checkout returns HTTP 503 and the Pods look healthy?
- What customer impact qualifies as a P1 incident?
- Should TLS verification be disabled when a certificate expires?
- Can adding more application replicas make database connection exhaustion worse?
- What is the difference between readiness and liveness probes?

## Answer modes

### Free extractive mode (default)

Leave `OPENAI_API_KEY` empty in `.env`. OpsLens returns exact evidence excerpts with verified citations. Retrieval, fusion, reranking, evaluation, the API, and the UI all work without a paid LLM API.

The health endpoint reports:

```json
{
  "answer_mode": "extractive-demo"
}
```

### Generated answer mode (optional)

Set a key and a model available to your account in `.env`:

```dotenv
OPENAI_API_KEY=replace_with_your_key
OPENAI_MODEL=replace_with_an_available_model
```

Restart the API. The model receives only the reranked evidence and must use numbered citations. Citation objects are still constructed from stored chunks in application code.

Never commit `.env`; it is excluded by `.gitignore`.

## Example API call

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"How should we mitigate a payment retry storm?","top_k":5}'
```

Example response shape:

```json
{
  "answer": "Reduce retry concurrency before increasing upstream timeouts... [1]",
  "citations": [
    {
      "number": 1,
      "document_id": "doc_...",
      "chunk_id": "chk_...",
      "title": "Runbook: Payment Retry Storm",
      "section": "Immediate mitigation",
      "source_path": "runbooks/payment-retry-storm.md",
      "source_url": null,
      "quote": "Reduce payment retry concurrency before increasing upstream timeouts..."
    }
  ],
  "mode": "extractive-demo",
  "retrieval_latency_ms": 42.7,
  "generation_latency_ms": 0.2,
  "trace_id": "tr_..."
}
```

## How hybrid retrieval works

1. Markdown documents are cleaned and split by section, then divided into overlapping word windows.
2. Stable document and chunk IDs are derived from paths and content.
3. `all-MiniLM-L6-v2` creates normalized local embeddings.
4. BM25 and cosine similarity independently produce candidate rankings for each question.
5. RRF assigns each candidate `1 / (60 + rank)` from each ranking.
6. `ms-marco-MiniLM-L-6-v2` reranks the fused candidates as query-passage pairs.
7. Only the final passages reach the answer layer.
8. Citation identifiers and quotes are mapped back to stored chunks programmatically.

Settings are environment-configurable; see [.env.example](.env.example).

## Evaluation

Build the index, then run:

```bash
uv run python -m scripts.evaluate
```

The checked-in dataset at `data/evals/golden.jsonl` contains questions and human-authored expected source paths. The report includes:

- Hit Rate@5 - whether an expected source appears in the first five results
- MRR - how early the first expected source appears
- Per-question retrieved paths and latency

### Current measured baseline

The checked-in report was produced with 19 documents, 301 chunks, and 10 reviewed questions:

| Configuration | Hit Rate@5 | MRR | Questions |
|---|---:|---:|---:|
| BM25 + MiniLM semantic search + RRF + cross-encoder | 1.00 | 1.00 | 10 |

This is a small, corpus-specific regression set. The result demonstrates reproducibility and protects against regressions; it is not a claim of 100% performance on unseen organizational data. See [docs/eval-report.json](docs/eval-report.json) for the complete report.

## Tests and quality checks

```bash
uv run pytest
uv run ruff check .
```

The test suite covers stable chunking, embedding persistence, RRF, hybrid ranking, reranker ordering, and exact citation provenance. GitHub Actions runs lint and tests on every push and pull request.

## Docker

```bash
docker compose up --build
```

The API image builds the local index, and the UI waits for the API health check. Open <http://localhost:8501> when both services are healthy.

## Data and licensing

The `architecture/`, `runbooks/`, `policies/`, and `postmortems/` documents are original fictional material distributed under this repository's MIT license.

The project includes a small pinned subset of Kubernetes documentation under CC BY 4.0. `data/provenance.json` records upstream source URLs, the pinned commit, retrieval timestamps, and SHA-256 hashes. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Do not add real customer data, credentials, or confidential employer documents to this repository.

## Repository structure

```text
app/                 FastAPI, indexing, retrieval, reranking, answering
scripts/             open-document import, index build, evaluation
ui/                  Streamlit interface
data/documents/      original and attributed open-source documents
data/evals/          reviewed retrieval questions
tests/               deterministic unit tests
docs/                architecture and evaluation report
.github/workflows/   continuous integration
```

## Production boundaries

OpsLens is a production-minded portfolio MVP, not a production-certified service. Before using private organizational data, add authentication, per-document authorization filters, durable vector storage, incremental indexing and deletion workflows, PII controls, rate limiting, distributed telemetry, calibrated abstention, and a substantially larger reviewed evaluation set.

The first release intentionally excludes multi-agent orchestration, text-to-SQL, semantic response caching, and LoRA. These features belong after the retrieval baseline is reliable and measured.

## Roadmap

- **v0.1:** hybrid retrieval, reranking, citations, API, UI, evaluation, and CI (current)
- **v0.2:** PostgreSQL/pgvector persistence and semantic cache with version invalidation
- **v0.3:** guarded read-only incident analytics and one bounded LangGraph router
- **v0.4:** production-log evaluation candidate generation with human review

## License

Application code and original OpsLens content are MIT licensed. Fetched Kubernetes documentation remains CC BY 4.0 and retains upstream attribution.
