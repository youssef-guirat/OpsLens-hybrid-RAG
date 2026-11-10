# Portfolio Project: OpsLens — Production Knowledge and Analytics Copilot

## 1. Executive decision: should all six ideas be used?

No. They should not all have equal weight in the first version. A noticeable portfolio project is a coherent, finished product with measurements and production controls—not a collection of fashionable features.

Use this scope:

| Concept | Decision | Role in the project |
|---|---|---|
| Hybrid RAG + reranking + citations | **Core** | The main product and deepest implementation |
| Agent orchestration + tools + memory + HITL | **Core, but small** | One LangGraph router with two tools and one approval path |
| Semantic caching | **Core** | A measured LLMOps feature with safe invalidation |
| Evaluations from logs | **Core** | Demonstrates that improvements are evidence-based |
| Safe text-to-SQL | **Contained differentiator** | One read-only analytics tool with deterministic protection |
| LoRA fine-tuning | **Optional extension** | A separate notebook and benchmark, not a dependency of the app |

This gives the project one clear story while still demonstrating the six concepts. Build and publish the core first. Add LoRA only if the application, tests, evaluation report, and documentation are already complete.

## 2. The project idea

**OpsLens** is an internal knowledge and incident-analytics copilot for a fictional SaaS company.

It answers two kinds of questions:

1. **Knowledge questions** over runbooks, service documentation, security policies, and incident postmortems, with exact citations.
2. **Analytics questions** over a PostgreSQL incident/ticket database, using guarded read-only text-to-SQL.

Example questions:

- “How should an engineer respond to repeated payment API timeouts?”
- “Which postmortem explains the retry storm, and what actions were assigned?”
- “How many P1 incidents affected the payments service last quarter?”
- “Compare the most common causes of P1 incidents by service.”

The system routes each question to document retrieval, safe SQL analytics, or both. It keeps short session context, asks for human approval when a request is ambiguous or expensive, returns evidence, caches safe repeated requests, and learns an evaluation set from reviewed production feedback.

## 3. Why this will stand out

Many portfolio RAG projects stop at “upload a PDF and chat.” OpsLens demonstrates that you understand the difficult parts employers care about:

- retrieval quality is measured against a baseline;
- citations are tied to real stored chunks;
- unstructured documents and structured data use different tools;
- an LLM cannot directly execute arbitrary SQL;
- agent routes are bounded and observable;
- caching has permission and index-version safety;
- production failures become reviewed regression tests;
- the repository is reproducible, tested, and honest about limitations.

The value is in this engineering evidence, not in adding many agents.

## 4. Target users and data

### User

An on-call engineer or support lead who needs fast, evidence-backed answers about services and incidents.

### Synthetic portfolio data

Use only synthetic or public-safe data:

- 40–80 Markdown/PDF documents;
- runbooks for 5 fictional services;
- architecture and troubleshooting guides;
- 10–20 incident postmortems;
- security and escalation policies;
- 500–1,000 synthetic incident/ticket rows.

Generate the data deterministically with a seed so reviewers can reproduce the demo. Do not use confidential employer or university documents.

### Recommended free/open data strategy

Use a mixed corpus instead of either copying arbitrary web pages or generating everything with an LLM:

1. **Real technical base:** use a small pinned subset of the [Kubernetes documentation repository](https://github.com/kubernetes/website), whose documentation is CC BY 4.0. Select roughly 15–25 English troubleshooting, logging, workload, service, and debugging pages—not the entire repository.
2. **Coherent application architecture:** use [Google Cloud's Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo), an Apache-2.0 sample with multiple Kubernetes/gRPC services, as the fictional company's technical system. Its services give the runbooks and incidents something consistent to describe.
3. **Postmortem examples:** use the structure and a small attributed subset of the MIT-licensed [incident-postmortems](https://github.com/Garinheslop/incident-postmortems) repository, or write original postmortems following that format.
4. **Original internal layer:** write 15–20 original OpsLens documents—service ownership, severity policy, escalation policy, payment timeout runbook, certificate-expiry runbook, database-pool runbook, and incidents tied to the Online Boutique services.
5. **Structured analytics data:** generate 500–1,000 fictional incident rows whose services, causes, and dates agree with those original documents.

The GitLab Handbook is a useful example of searchable internal-company documentation and is published under CC BY-SA 4.0. Because ShareAlike adds redistribution obligations, use it as a design reference unless you deliberately include attribution and compatible licensing. Google's SRE books are excellent and free to read online, but “free to read” is not the same as permission to redistribute their text; use them for learning rather than bundling chapters in the repository.

For every third-party file, store provenance:

```text
source_url, upstream_repository, upstream_path, license,
retrieved_at, commit_sha, content_hash, local_path
```

Add `THIRD_PARTY_NOTICES.md`, keep the upstream license/attribution required for vendored content, and pin a commit or release so the evaluation corpus does not silently change.

### Fastest portfolio-ready corpus

The first release only needs:

| Corpus section | Quantity | Source |
|---|---:|---|
| Kubernetes troubleshooting pages | 15–25 | Pinned CC BY 4.0 upstream files |
| Service/architecture descriptions | 5–10 | Online Boutique plus original summaries |
| OpsLens runbooks and policies | 10–15 | Original repository content |
| OpsLens postmortems | 6–10 | Original or clearly attributed MIT examples |
| Incident table | 500 rows | Deterministic synthetic generator |
| Reviewed evaluation questions | 40 initially | Written from the final corpus |

This is large enough to demonstrate hybrid retrieval and exact identifiers, but small enough to inspect citations and labels manually.

### Suggested incident schema

```text
incidents(
  incident_id,
  title,
  service,
  severity,
  status,
  root_cause_category,
  opened_at,
  resolved_at,
  resolution_minutes,
  customer_impact,
  region
)
```

Do not store raw personal customer data.

## 5. User-facing features

### Feature A — Evidence-backed document answers

- index Markdown, text, and PDF documents;
- preserve source, page/section, timestamps, and stable document/chunk IDs;
- run PostgreSQL full-text search and pgvector dense search;
- merge rankings with Reciprocal Rank Fusion;
- rerank the fused candidates with a cross-encoder;
- generate an answer only from the selected evidence;
- return clickable source citations and exact verified excerpts;
- say “insufficient evidence” when the index cannot support an answer.

### Feature B — Small, controlled agent workflow

Use one LangGraph workflow rather than a multi-agent team:

```text
User question
    |
validate/authenticate
    |
classify route
    +----> search_docs --------+
    +----> query_incidents ----+--> evidence check
    +----> both ---------------+        |
                                      +-- sufficient --> answer + citations
                                      +-- ambiguous/expensive --> human approval
                                      +-- weak evidence --> safe fallback
```

The only initial tools should be:

1. `search_docs(query, filters)`
2. `query_incidents(question)`

Conversation memory stores recent user preferences and references such as “that incident.” It must not replace authoritative evidence. Checkpoint state by session/thread ID and cap every retry loop.

### Feature C — Semantic response cache

Store an embedding of eligible normalized questions plus:

- answer and citation IDs;
- route and filters;
- tenant/user access scope;
- prompt/model version;
- document index version and database snapshot/version;
- creation time and TTL.

Reuse a response only when semantic similarity exceeds a validated threshold and all safety/version fields match. Do not cache sensitive, personalized, low-confidence, human-review, or volatile SQL responses.

Measure cache hit rate, false-hit review results, latency saved, tokens saved, and estimated cost avoided. “Cuts the API bill in half” is a hypothesis, not a claim. Report the actual result from a replay workload.

### Feature D — Evaluation dataset generator from logs

For each request, log a privacy-safe record:

```text
trace_id, timestamp, redacted_question, route, filters,
retrieved_chunk_ids, reranked_chunk_ids, generated_answer,
citation_ids, cache_hit, latency, token_usage, model_version,
user_feedback, error_type
```

A scheduled/offline command should:

1. select negative-feedback, low-evidence, high-latency, and representative queries;
2. redact PII and secrets;
3. deduplicate semantically similar cases;
4. create a draft expected answer and expected source IDs;
5. send the case to a simple reviewer screen or JSON review queue;
6. add only approved cases to the frozen golden dataset.

Synthetic LLM-generated answers are **candidate labels**, not automatic ground truth.

### Feature E — Guarded text-to-SQL

The LLM proposes SQL, but deterministic code decides whether it is allowed.

Required layers:

1. Provide only an allowlisted schema to the model.
2. Parse SQL into an AST with SQLGlot; do not rely on regex alone.
3. Accept exactly one `SELECT` statement.
4. Reject `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE`, `COPY`, `CALL`, and other mutating/admin operations.
5. Restrict tables, columns, functions, joins, and schemas to allowlists.
6. Add a maximum row limit and statement timeout.
7. run `EXPLAIN` and reject queries above a configured cost threshold.
8. Execute with a database user that has only `SELECT` permission on a sanitized view or read replica.
9. Log the proposed, validated, and executed query.
10. Require human approval for expensive or unusually broad analytics.

The read-only database role is the final boundary. Even a validator bug must not permit destructive execution.

### Feature F — Optional LoRA benchmark

Keep fine-tuning outside the serving dependency graph. Add a notebook or training script that tests one narrow question:

> Does a LoRA adapter improve route classification and structured incident-summary formatting compared with the same base model?

Use a small open model that fits the available Colab/local GPU, with PEFT/TRL or an equivalent library. Create train/validation/test splits, remove duplicates, freeze the test set, and compare:

- route classification accuracy/F1;
- structured-output validity;
- incident-summary rubric score;
- latency and memory use;
- common failure slices.

Do not train the model to memorize the document corpus. Changing facts belong in RAG. If LoRA does not beat the base model reliably, publish that result; the experiment is still credible engineering work.

## 6. Recommended architecture

```text
                         +-------------------+
                         | Streamlit Web UI  |
                         +---------+---------+
                                   |
                         +---------v---------+
                         | FastAPI API       |
                         | auth, validation  |
                         +---------+---------+
                                   |
                      +------------v-------------+
                      | LangGraph orchestrator   |
                      | route, tools, checkpoint |
                      +------+-------------+-----+
                             |             |
                  +----------v--+       +--v----------------+
                  | Document RAG |       | Safe SQL tool     |
                  | hybrid+rerank|       | AST+read-only DB  |
                  +-------+------+       +----------+--------+
                          |                         |
                  +-------v-------------------------v--------+
                  | PostgreSQL: pgvector + FTS + incidents  |
                  | cache, checkpoints, feedback, audit log  |
                  +---------------------+---------------------+
                                        |
                         +--------------v--------------+
                         | Offline ingestion + evals   |
                         | index, replay, reports       |
                         +-----------------------------+
```

Use PostgreSQL for vectors, full-text search, relational incidents, and initial cache storage. One database keeps the project deployable and understandable. Redis, a separate vector database, Kafka, Kubernetes, GraphRAG, and multiple agents are unnecessary for the first release.

## 7. Suggested technology stack

- **Language:** Python 3.12
- **API:** FastAPI and Pydantic
- **Workflow:** LangGraph
- **RAG utilities:** LangChain where useful, with your own typed service boundaries
- **Database:** PostgreSQL with `pgvector` and native full-text search
- **Hybrid fusion:** Reciprocal Rank Fusion implemented in application code or SQL
- **Reranker:** a small sentence-transformers cross-encoder
- **SQL validation:** SQLGlot
- **UI:** Streamlit for speed and clarity
- **Testing:** Pytest and HTTPX/Testcontainers if practical
- **Packaging:** `uv`
- **Deployment:** Docker Compose
- **CI:** GitHub Actions for lint, type checks, unit tests, security tests, and a small offline eval
- **Observability:** structured JSON logging plus OpenTelemetry/LangSmith if desired
- **Fine-tuning extension:** PEFT/TRL in a Colab-compatible notebook

Pin versions in the lockfile and keep model/provider names in configuration rather than application code.

## 8. Repository structure

```text
opslens/
├── README.md
├── LICENSE
├── .env.example
├── pyproject.toml
├── uv.lock
├── docker-compose.yml
├── Makefile
├── app/
│   ├── api/
│   │   ├── routes_chat.py
│   │   ├── routes_feedback.py
│   │   ├── routes_admin.py
│   │   └── schemas.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── ingestion/
│   │   ├── loaders.py
│   │   ├── chunking.py
│   │   └── indexer.py
│   ├── retrieval/
│   │   ├── dense.py
│   │   ├── sparse.py
│   │   ├── fusion.py
│   │   ├── reranker.py
│   │   └── citations.py
│   ├── agent/
│   │   ├── state.py
│   │   ├── graph.py
│   │   └── tools.py
│   ├── sql/
│   │   ├── generator.py
│   │   ├── validator.py
│   │   └── executor.py
│   ├── cache/
│   │   └── semantic_cache.py
│   ├── evals/
│   │   ├── metrics.py
│   │   ├── generate_candidates.py
│   │   └── runner.py
│   └── main.py
├── ui/
│   └── streamlit_app.py
├── data/
│   ├── sample_docs/
│   ├── seed_incidents.csv
│   └── evals/golden.jsonl
├── migrations/
├── scripts/
│   ├── seed_data.py
│   ├── ingest.py
│   └── replay_workload.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── evals/
├── notebooks/
│   └── lora_route_benchmark.ipynb
└── docs/
    ├── architecture.md
    ├── threat-model.md
    └── eval-report.md
```

## 9. API contract

Keep the public API small:

- `POST /v1/chat` — ask a question and return answer, route, citations, SQL summary if used, cache status, and trace ID.
- `POST /v1/feedback` — record thumbs up/down, reason, and optional correction.
- `POST /v1/reviews/{thread_id}` — approve or reject a paused request.
- `POST /v1/admin/ingest` — protected ingestion trigger; a CLI is sufficient for the MVP.
- `POST /v1/admin/evals/run` — protected offline evaluation trigger; a CLI is also acceptable.
- `GET /health` — process health.
- `GET /ready` — database/model dependency readiness.

Example response:

```json
{
  "answer": "The runbook recommends reducing retry concurrency...",
  "route": "documents",
  "citations": [
    {
      "source": "payments-timeout-runbook.md",
      "document_id": "doc_018",
      "chunk_id": "chunk_018_04",
      "section": "Mitigation",
      "quote": "Reduce retry concurrency before increasing the upstream timeout."
    }
  ],
  "cache_hit": false,
  "needs_review": false,
  "trace_id": "tr_..."
}
```

## 10. Build plan

## Milestone 1 — Skeleton and reproducible data (Week 1)

- create the repository, configuration, FastAPI service, Streamlit UI, and Docker Compose;
- add PostgreSQL, pgvector, migrations, health/readiness checks;
- generate deterministic synthetic documents and incidents;
- add CI, formatting, type checking, and first tests.

**Exit condition:** a reviewer can clone the repository, copy `.env.example`, run one documented command, and see the app.

## Milestone 2 — Baseline RAG with verified citations (Week 2)

- implement idempotent ingestion with stable IDs and content hashes;
- build dense top-k retrieval;
- add grounded structured generation and insufficient-evidence behavior;
- return citations from retrieved metadata and verify quoted text;
- create the first 30 reviewed evaluation questions.

**Exit condition:** every displayed citation opens the correct source/section, and retrieval Recall@5 is reported.

## Milestone 3 — Hybrid retrieval and reranking (Week 3)

- add PostgreSQL full-text search;
- fuse dense and sparse rankings with RRF;
- rerank the top candidates with a cross-encoder;
- compare dense, sparse, hybrid, and hybrid-plus-reranker on the same frozen set;
- publish metrics, latency, and failure examples.

**Exit condition:** the repository contains a reproducible benchmark table. Keep reranking only if the measured trade-off is worthwhile.

## Milestone 4 — Orchestration and safe SQL (Week 4)

- add the LangGraph route between documents, analytics, and both;
- implement typed tools and bounded routes;
- add session memory and PostgreSQL checkpointing;
- implement SQLGlot validation, allowlists, limits, `EXPLAIN`, timeout, and a read-only role;
- add a human-review interruption for ambiguous or costly analytics;
- create adversarial SQL tests.

**Exit condition:** destructive queries fail both application validation and database authorization tests.

## Milestone 5 — Caching and production telemetry (Week 5)

- add semantic cache eligibility rules, embeddings, thresholds, TTLs, and versioned invalidation;
- add structured logs, trace IDs, token/cost accounting, and latency metrics;
- implement retry/timeout/fallback behavior;
- replay a fixed workload with and without caching;
- report actual hit rate, quality checks, cost avoided, and latency saved.

**Exit condition:** no cache result crosses an access scope or survives a relevant index version change.

## Milestone 6 — Eval feedback loop and portfolio polish (Week 6)

- store feedback and privacy-safe traces;
- generate candidate eval cases from real app logs;
- add manual review before golden-set inclusion;
- run regression evaluation in CI on a small deterministic subset;
- write architecture, threat model, limitations, and evaluation report;
- add screenshots, a two-minute demo video, and deployment instructions.

**Exit condition:** a failed production-style query can become a reviewed test case that prevents the same regression.

## Milestone 7 — Optional LoRA study (Week 7+)

- define the narrow routing/formatting hypothesis;
- create and audit dataset splits;
- benchmark the base model;
- train the adapter;
- run the unchanged holdout evaluation;
- document whether it helped enough to justify deployment.

**Exit condition:** a reproducible base-versus-LoRA table exists. The main application still runs without the adapter.

## 11. Evaluation plan

### Retrieval metrics

- Recall@5 and Recall@10
- MRR
- nDCG@5
- source/filter correctness

### Answer and citation metrics

- faithfulness to retrieved evidence
- answer relevance and completeness
- citation precision
- exact quote verification rate
- correct insufficient-evidence decisions

### SQL metrics

- executable-query accuracy on allowed questions
- answer accuracy against known database results
- destructive-query block rate
- false rejection rate for safe queries
- timeout/cost-limit enforcement

### Operations metrics

- p50/p95 latency by route
- error, retry, and fallback rates
- input/output tokens and estimated cost
- semantic cache hit rate and reviewed false-hit rate
- human-review frequency and resolution

### Suggested benchmark table

Do not fill this table with invented values:

| Configuration | Recall@5 | MRR | Citation precision | p95 latency | Mean cost/query |
|---|---:|---:|---:|---:|---:|
| Dense baseline | measured | measured | measured | measured | measured |
| Hybrid RRF | measured | measured | measured | measured | measured |
| Hybrid + reranker | measured | measured | measured | measured | measured |
| Final + semantic cache replay | measured | measured | measured | measured | measured |

## 12. Minimum test suite

### Unit tests

- chunk IDs and metadata remain stable;
- RRF produces the expected ordering;
- citation excerpts exist in the referenced chunk;
- cache keys include access scope and index version;
- cache threshold and TTL behavior;
- route schemas and maximum retry count;
- SQL AST allowlist/denylist.

### Integration tests

- ingest -> retrieve -> rerank -> cited answer;
- update/delete a document -> correct invalidation;
- analytics question -> validated SQL -> correct result;
- checkpoint -> human approval -> resume;
- feedback -> candidate eval -> manual approval -> golden JSONL.

### Security tests

- user and retrieved-document prompt injection;
- unauthorized metadata/tenant filters;
- SQL comments, nested statements, CTE tricks, forbidden functions, and time-consuming queries;
- PII/secrets absent from logs and cache;
- direct database mutation attempted with the runtime role.

### Regression tests

- frozen retrieval cases;
- known unsupported questions;
- difficult acronyms and exact identifiers;
- multi-turn references;
- safe and unsafe SQL cases.

## 13. Definition of done

The project is portfolio-ready when:

- `docker compose up` starts a seeded demo;
- setup contains no committed secrets;
- ingestion is repeatable and idempotent;
- hybrid retrieval and reranking are benchmarked against a dense baseline;
- citations contain stable IDs and verified source excerpts;
- unsupported questions fail safely;
- only two typed tools exist and all graph loops are bounded;
- SQL is parsed and executed with a read-only role;
- the human-review pause/resume path is demonstrated;
- semantic-cache correctness and actual savings are measured;
- production-style logs can produce human-reviewed evaluation cases;
- tests and a small regression eval run in CI;
- the README includes architecture, demo, metrics, security, limitations, and trade-offs;
- a two-minute video shows one document question, one analytics question, one blocked destructive query, and one cache hit.

## 14. What deliberately stays out of scope

- multiple autonomous agents;
- Kubernetes and microservices;
- a separate graph database or GraphRAG;
- multimodal document understanding;
- write-capable database tools;
- enterprise authentication and real multi-tenancy;
- a separate vector database and Redis in the MVP;
- continuous online fine-tuning.

Mention these as future work only when you can explain the failure mode that would justify each one.

## 15. README and demo checklist

Your public `README.md` should lead with the outcome, then include:

1. one-sentence problem and target user;
2. screenshot/GIF and two-minute demo link;
3. architecture diagram;
4. feature list with clear safety boundaries;
5. quick start with seeded data;
6. evaluation methodology and measured comparison table;
7. cache experiment results;
8. SQL threat model and defense layers;
9. test/CI status;
10. limitations and future improvements.

### Two-minute demo script

1. Ask a runbook question and open its exact citation.
2. Ask an incident-count question and show the generated, validated read-only SQL.
3. enter “DROP TABLE incidents” and show deterministic rejection plus database read-only protection.
4. repeat a semantically equivalent safe document question and show a cache hit.
5. submit negative feedback and show how it enters the candidate evaluation review queue.

## 16. CV bullet templates

Replace every bracket with measured evidence:

- Built a production-style internal operations copilot using FastAPI, LangGraph, PostgreSQL/pgvector, hybrid RRF retrieval, and cross-encoder reranking, improving Recall@5 from **[baseline]** to **[final]** on **[N]** reviewed queries.
- Implemented source-grounded answers with stable chunk citations and verified excerpts, achieving **[citation precision]** citation precision and **[faithfulness result]** on a frozen regression set.
- Designed a version-aware semantic cache that achieved a **[hit rate]** hit rate and reduced replay-workload LLM cost by **[measured percentage]** without crossing access or index boundaries.
- Secured text-to-SQL with AST validation, schema/function allowlists, query-cost limits, timeouts, and a read-only PostgreSQL role; blocked **[N/N]** destructive/adversarial test cases.
- Built a human-reviewed evaluation pipeline from privacy-scrubbed application logs and integrated **[N]** retrieval, safety, and regression checks into GitHub Actions.

Never claim “50% cost reduction” unless the recorded experiment produced that result.

## 17. Interview story

Be ready to explain the project in this order:

1. **Problem:** engineers waste time searching scattered runbooks and incident data.
2. **Baseline:** dense top-k RAG worked for semantic queries but missed exact codes and produced noisy rankings.
3. **Improvement:** hybrid RRF improved recall, reranking improved final ordering, and verified citations made answers auditable.
4. **Architecture choice:** one bounded graph and two tools were sufficient; a multi-agent system would add unnecessary latency and failure modes.
5. **Security:** model instructions are not a boundary, so SQL is validated deterministically and executed with a read-only role.
6. **Operations:** versioned semantic caching, telemetry, and regression evals manage cost and quality.
7. **Evidence:** show the benchmark table, failure examples, tests, and honest limitations.

That narrative is more convincing than a long feature list because it demonstrates engineering judgment.
