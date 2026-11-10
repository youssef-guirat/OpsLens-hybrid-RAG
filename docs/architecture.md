# OpsLens Architecture

## Scope

OpsLens v0.1 proves one vertical slice: an operations question is matched to evidence by two different retrieval methods, reranked, answered, and returned with inspectable citations.

## Offline path

```text
allowlisted Markdown
  -> parse metadata/frontmatter
  -> remove Hugo shortcodes/comments
  -> split by headings
  -> bounded overlapping word windows
  -> stable document/chunk IDs
  -> normalized sentence embeddings
  -> versioned JSON index
```

The JSON index is deliberately transparent for a portfolio MVP. It makes chunks, metadata, and vectors easy to inspect. It is not intended for large or concurrent production workloads; PostgreSQL/pgvector is the planned durable replacement.

## Online path

```text
question
  +-> BM25 -> sparse ranking -----+
  +-> embedding -> dense ranking -+-> Reciprocal Rank Fusion
                                      -> cross-encoder reranker
                                      -> top evidence
                                      -> answerer
                                      -> citation verifier
```

BM25 is strong for exact service names, alert identifiers, and error codes. Dense retrieval improves recall for paraphrases. RRF combines their ranks without normalizing incompatible raw scores. The cross-encoder makes a more expensive query/passage relevance decision only for the small fused candidate set.

## Citation design

The model sees numbered evidence blocks. It may reference `[1]`, `[2]`, and so on, but it cannot define source metadata. The API maps valid numbers back to stored chunks and returns exact substrings as quotes. Unknown citation numbers are discarded. If generated text contains no valid citation, the service attaches the highest-ranked source and makes that fallback visible in behavior tests.

This proves provenance, not perfect claim-level entailment. A future version should verify each sentence against cited evidence and abstain below a calibrated threshold.

## Trust boundaries

- Retrieved text is untrusted data, not instructions.
- Provider keys enter only through environment variables.
- Open documents come from a hard-coded allowlist, not arbitrary user URLs.
- The MVP accepts local administrator-controlled Markdown only.
- There are no write-capable tools or database credentials.
- Logs must not contain secrets or private documents.

## Failure behavior

- Missing index: startup fails with a command explaining how to build it.
- Empty corpus: index build fails explicitly.
- Provider key absent: deterministic extractive mode remains available.
- Provider call fails: API returns a generic server error and logs the exception locally.
- Open-document URL fails: importer records the failure and continues; it fails only if nothing downloads.

## Scaling path

The next production step is not more agents. It is durable storage, document authorization filters, incremental index versioning, observability, semantic cache correctness, and a larger reviewed evaluation set.

