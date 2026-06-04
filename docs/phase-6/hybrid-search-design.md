# Hybrid Search Design

## Summary

Hybrid retrieval combines semantic vector search with PostgreSQL full-text keyword search. The implementation is intentionally simple and explainable so benchmark changes can be attributed to retrieval behavior, not hidden reranking.

## Keyword Search

Keyword search uses the existing generated `chunks.tsv` column:

```sql
websearch_to_tsquery('english', question)
```

Results are ranked with `ts_rank_cd`. Permission filtering, document status filtering, ingestion status filtering, and chunking strategy filtering happen inside the SQL query.

## Hybrid Candidate Collection

Hybrid search retrieves a wider candidate set from both retrievers:

```text
candidate_k = max(top_k * 4, 20)
```

This gives each retriever enough room to contribute before the final merge.

## Score Merging

For each candidate set:

1. Normalize vector scores to `0.0` through `1.0`.
2. Normalize keyword scores to `0.0` through `1.0`.
3. Merge candidates by `chunk_id`.
4. Compute:

```text
hybrid_score = vector_weight * normalized_vector_score + keyword_weight * normalized_keyword_score
```

Default weights:

```text
vector_weight = 0.5
keyword_weight = 0.5
```

## Retrieval Source

Each returned chunk records where it came from:

- `vector`
- `keyword`
- `both`

This makes retrieval behavior easier to debug in benchmark traces.

## Deferred

The following are intentionally deferred:

- Cross-encoder reranking.
- LLM reranking.
- Azure AI Search.
- Semantic chunking.
- Query rewriting.

These should be considered only after the vector, keyword, and hybrid baseline comparison is measured.
