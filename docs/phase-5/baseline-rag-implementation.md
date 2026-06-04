# Phase 5 Baseline RAG Implementation

## What This Phase Implements

Phase 5 creates the first working backend baseline for the Enterprise Knowledge Agent.

Implemented capabilities:

- FastAPI backend scaffold.
- PostgreSQL + pgvector Docker Compose setup.
- Baseline SQL schema.
- Markdown ingestion from `data/synthetic-documents/`.
- Section-based chunking.
- OpenAI embedding generation.
- pgvector storage.
- Vector-only retrieval.
- Basic answer generation with citations.
- Minimal `/health` and `/query` endpoints.
- Simple benchmark runner using `data/evaluation/benchmark-questions.json`.
- Baseline evaluation report output.
- Honest retrieval metrics that separate any-source hit, all-sources hit, expected-source recall, and MRR.
- Chunk-level benchmark trace storage with retrieved chunk IDs, document IDs, sections, ranks, and scores.

## Intentionally Excluded

- Hybrid retrieval.
- PostgreSQL full-text keyword retrieval.
- Reranking.
- Azure Blob Storage.
- Advanced auth.
- Full frontend dashboard.
- LangGraph/LangChain orchestration.
- Prompt experiment UI.
- Full Phase 4 database schema.

## System Flow

1. `scripts/ingest_markdown.py` loads synthetic Markdown documents.
2. Frontmatter metadata is parsed.
3. Documents are split into `##` section-based chunks.
4. OpenAI embeddings are generated for each chunk.
5. Documents, versions, chunks, and embeddings are stored in PostgreSQL.
6. `/query` embeds the user question.
7. Vector search retrieves top-k chunks filtered by `user_role`.
8. OpenAI chat generation answers only from retrieved context.
9. Citations include document ID, document title, section heading, and chunk ID.
10. Benchmark citation scoring uses only citations explicitly produced by the model, not fallback citations.

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create `.env` from `.env.example` and add `OPENAI_API_KEY`.

Start PostgreSQL:

```powershell
docker compose up -d
```

Apply schema and ingest documents:

```powershell
python scripts/ingest_markdown.py --apply-schema
```

Expected result:

- 14 documents ingested.
- Section-based chunks created.
- Embeddings stored.
- Failures should be 0.

## Run API

```powershell
uvicorn apps.api.app.main:app --reload
```

Test question:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/query -ContentType "application/json" -Body '{"question":"How many vacation days do full-time employees receive?","user_role":"Employee","top_k":5}'
```

Expected:

- Answer cites `HR-002`.
- Citation section is `Vacation Entitlement`.

## Run Benchmark

```powershell
python scripts/run_baseline_eval.py --retrieval-only
python scripts/run_baseline_eval.py
```

Expected:

- Loads 60 questions.
- Runs vector-only retrieval.
- In retrieval-only mode, outputs retrieval hit rate and MRR without running chat completions.
- In full mode, outputs any-source retrieval hit, all-sources retrieval hit, expected-source recall, MRR, citation source match, and behavior match.
- Updates `docs/phase-5/baseline-evaluation-results.md`.
- Marks answer accuracy, faithfulness, and hallucination metrics as pending.

Retrieval-only mode skips answer generation. Citation source match and behavior match are pending in that mode because no answer is generated. Permission-restricted and missing-information questions are excluded from retrieval hit and MRR averages because the correct behavior is not to retrieve restricted or nonexistent source documents.

Metric notes:

- **Any-source retrieval hit** checks whether at least one expected source document appears in the retrieved chunks.
- **All-sources retrieval hit** checks whether every expected source document appears in the retrieved chunks. This is the stricter metric for multi-document questions.
- **Expected-source recall** measures the fraction of expected source documents retrieved.
- **MRR** measures the rank of the first expected source document and does not prove multi-document completeness by itself.
- **Citation source match** is based only on citations explicitly emitted by the model. API fallback citations are marked separately and are not counted as citation-quality evidence.

## Known Limitations

- Vector-only retrieval.
- No keyword or hybrid search.
- No reranking.
- No Azure Blob Storage.
- No advanced auth.
- Role filtering uses document metadata rather than real user-role tables.
- Citation validation is basic source matching, not full claim validation.
- Citation scoring verifies source-document overlap, not full quote-level claim support.
- Answer quality metrics require manual review or an evaluation judge.
- No frontend dashboard.
- No LangGraph.
- No prompt experiment UI.

## Phase 6 Recommendation

Phase 6 should be **Improved Retrieval and Evaluation Comparison**.

Build next:

- PostgreSQL full-text keyword retrieval.
- Hybrid retrieval combining vector and keyword scores.
- Better benchmark reporting.
- Prompt version comparison.
- Basic citation validation improvements.
- Evaluation comparison report: baseline vector-only vs improved hybrid.
- Optional minimal frontend evaluation dashboard after metrics exist.
