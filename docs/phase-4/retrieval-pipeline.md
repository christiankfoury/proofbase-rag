# Retrieval Pipeline Design

## Purpose

The retrieval pipeline finds relevant, permission-safe chunks for a user question. It must support vector search, keyword search, hybrid retrieval, optional reranking, freshness filtering, and run logging.

Critical rule: unauthorized chunks must never be passed to answer generation.

## Inputs

- `user_id`
- user roles
- question
- optional chat session context
- retrieval mode
- `top_k`
- document filters
- freshness filters
- chunking strategy

## Retrieval Modes

### `vector_only`

Processing:

1. Embed the query.
2. Resolve permitted document IDs for user roles.
3. Search pgvector embeddings for permitted chunks only.
4. Rank by vector similarity.
5. Return top-k chunks.

Metrics:

- embedding latency
- vector search latency
- vector score
- top_k
- eligible chunks

### `keyword_only`

Processing:

1. Convert query to PostgreSQL full-text search query.
2. Resolve permitted document IDs for user roles.
3. Search chunk `tsvector` for permitted chunks only.
4. Rank by keyword score.
5. Return top-k chunks.

Metrics:

- keyword search latency
- keyword score
- top_k
- eligible chunks

### `hybrid`

Processing:

1. Run vector search on permitted chunks.
2. Run keyword search on permitted chunks.
3. Normalize vector and keyword scores.
4. Merge and deduplicate chunks.
5. Rank by weighted hybrid score.
6. Return top-k chunks.

Metrics:

- vector score
- keyword score
- hybrid score
- merge count
- deduped count
- latency

### `hybrid_rerank`

Processing:

1. Run hybrid search.
2. Select top candidate chunks.
3. Rerank with a reranker model or LLM judge later.
4. Return top-k chunks.

Metrics:

- hybrid metrics
- rerank latency
- rerank score
- final rank

## Freshness Filtering

Use document version metadata:

- only retrieve chunks from current indexed document versions by default
- support optional `effective_date` filters
- exclude archived and failed document versions

## Retrieval Run Logging

Create a `retrieval_runs` record for each retrieval attempt:

- query
- rewritten query if any
- retrieval mode
- top_k
- filters applied
- latency
- user
- session/message references

Create `retrieved_chunks` rows for each returned chunk:

- chunk ID
- rank
- vector score
- keyword score
- hybrid score
- rerank score
- `was_allowed`

`was_allowed` should always be true for normal retrieval results. If false ever appears, treat it as a security defect.

## Output Shape

```json
{
  "retrieval_run_id": "uuid",
  "mode": "vector_only",
  "top_k": 5,
  "chunks": [
    {
      "chunk_id": "uuid",
      "document_id": "HR-002",
      "document_title": "PTO and Leave Policy",
      "section_heading": "Vacation Entitlement",
      "content": "Full-time employees receive 20 paid vacation days...",
      "rank": 1,
      "scores": {
        "vector": 0.84,
        "keyword": null,
        "hybrid": null,
        "rerank": null
      }
    }
  ]
}
```

Use real scores only after implementation. Do not invent performance numbers in documentation or demo claims.
