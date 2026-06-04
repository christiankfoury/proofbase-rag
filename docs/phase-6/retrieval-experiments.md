# Phase 6 Retrieval Experiments

## Goal

Phase 6 compares retrieval strategies against the existing 60-question benchmark. The goal is to measure whether keyword or hybrid retrieval improves over the Phase 5 vector-only baseline.

This phase remains retrieval-focused. It does not add Azure AI Search, reranking, advanced auth, a frontend dashboard, LangGraph orchestration, or semantic chunking.

## Retrieval Modes

| Mode | Description | Purpose |
|---|---|---|
| `vector_only` | Embeds the query and ranks chunks by pgvector cosine similarity. | Phase 5 baseline and semantic matching. |
| `keyword_only` | Uses PostgreSQL full-text search over `chunks.tsv`. | Exact policy-term and acronym matching. |
| `hybrid` | Merges vector and keyword candidates with weighted normalized scores. | Tests whether semantic and lexical retrieval together improve benchmark coverage. |

## Chunking Strategies

| Strategy | Description | Default Settings |
|---|---|---|
| `section_based` | Keeps Markdown `##` sections as chunks. | Phase 5 default. |
| `fixed_size` | Splits section text into overlapping word windows. | 180 words, 40-word overlap. |

Both strategies preserve document ID, title, source path, section heading, access roles, chunk index, chunking strategy, and source text.

## Configurations

Phase 6 tests:

- `vector-section`
- `keyword-section`
- `hybrid-section-0.5`
- `vector-fixed-size`
- `hybrid-fixed-size-0.5`

Hybrid runs use:

```json
{
  "retrieval_mode": "hybrid",
  "vector_weight": 0.5,
  "keyword_weight": 0.5,
  "top_k": 5
}
```

## Metrics

| Metric | Meaning |
|---|---|
| Any-source hit | At least one expected source document appears in top-k. |
| All-sources hit | Every expected source document appears in top-k. |
| Expected-source recall | Fraction of expected source documents retrieved. |
| Precision@k | Retrieved chunks from expected source documents divided by k. |
| MRR | Reciprocal rank of the first expected source document. |
| Average latency | Mean retrieval/evaluation latency per question. |

Permission-restricted and missing-information questions are excluded from retrieval averages because they do not have an expected retrievable source for the requesting role.

## Commands

Apply schema and ingest section-based chunks:

```powershell
python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based
```

Ingest fixed-size chunks:

```powershell
python scripts/ingest_markdown.py --chunking-strategy fixed_size --chunk-size 180 --chunk-overlap 40
```

Run retrieval experiments:

```powershell
python scripts/run_retrieval_experiments.py
```

Results are written to `docs/phase-6/evaluation-results.md`.
