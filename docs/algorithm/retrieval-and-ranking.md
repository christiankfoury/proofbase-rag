# Retrieval And Ranking

Retrieval is the part of the system that decides which document chunks are available as evidence. This is the most important step for answer quality because the model can only answer well if the right chunks are present.

## Stored Retrieval Data

Markdown ingestion creates:

| Table concept | Purpose |
| --- | --- |
| `documents` | Document metadata, project, department, access roles, sensitivity, and status. |
| `document_versions` | Extracted text, version metadata, and ingestion status. |
| `chunks` | Section-based or fixed-size chunks with text and full-text `tsv`. |
| `chunk_embeddings` | OpenAI embeddings for vector search. |

The seeded corpus is ingested by `scripts/ingest_markdown.py`. It loads Markdown frontmatter, chunks sections, embeds chunk text, and writes chunks plus embeddings to Postgres.

Uploaded PDFs currently stop at pending review. `create_pending_review_document` stores extracted Markdown with `ingestion_status = 'pending_review'` and explicitly does not create chunks or embeddings. This means uploaded PDFs are not searchable yet.

## Chunking

The main chunking strategy is `section_based` in `apps/api/app/ingestion/chunker.py`.

| Strategy | Behavior |
| --- | --- |
| `section_based` | Splits a Markdown document by `##` headings. Each section becomes a chunk. |
| `fixed_size` | Splits section text into word windows with overlap. Used in earlier retrieval experiments. |

Section-based chunking is easier to cite because citations map to human-readable section headings.

## Vector Retrieval

Implemented in `apps/api/app/retrieval/vector_retriever.py`.

Flow:

1. Embed the question with `text-embedding-3-small`.
2. Search `chunk_embeddings` by cosine distance using pgvector.
3. Join to active documents and indexed document versions.
4. Apply project and department filters when present.
5. Apply role filtering with `d.access_roles && %s`.
6. Return `RetrievedChunk` objects with vector similarity score.

The retriever also runs a candidate query without the role filter for audit counts. Those candidate rows are used to log how many inaccessible chunks were blocked, but only the allowed query creates chunks for generation.

## Keyword Retrieval

Implemented in `apps/api/app/retrieval/keyword_retriever.py`.

Flow:

1. Normalize the question into search terms.
2. Build a PostgreSQL `websearch_to_tsquery`.
3. Search chunk full-text `tsv`.
4. Rank by `ts_rank_cd`.
5. Apply the same status, scope, and role filters as vector retrieval.

Keyword retrieval is useful when exact terms or IDs matter. It can miss semantic matches if the wording differs too much.

## Hybrid Retrieval

Implemented in `apps/api/app/retrieval/hybrid_retriever.py`.

Flow:

1. Run vector retrieval with a larger candidate count.
2. Run keyword retrieval with a larger candidate count.
3. Normalize each set of scores to `0.0` to `1.0`.
4. Merge duplicate chunks by `chunk_id`.
5. Compute `hybrid_score = vector_weight * vector_score + keyword_weight * keyword_score`.
6. Sort by hybrid score and return the requested top-k.

Hybrid retrieval still uses permission-filtered vector and keyword results. It does not merge in inaccessible chunks. The component permission audit events are labeled with `parent_retrieval_mode=hybrid` and `hybrid_component` metadata so the Dev/Admin audit view can distinguish one hybrid retrieval from unrelated vector and keyword requests.

## Vector Plus Lexical Rerank

The current measured retrieval reference is `vector_lexical_rerank`.

Implementation:

- `apps/api/app/retrieval/retriever.py` maps this mode to vector retrieval with `reranker="lexical"`.
- `apps/api/app/retrieval/vector_retriever.py` retrieves a larger allowed candidate set.
- `apps/api/app/retrieval/reranker.py` combines vector score with lexical overlap.

The reranker gives higher weight to:

- matching document ID terms
- matching title terms
- matching section heading terms
- matching chunk content terms
- chunks from the same lead document

This improved Precision@k in the Phase 33 live run:

| Run | Sample | Precision@k | Expected-source recall | MRR |
| --- | ---: | ---: | ---: | ---: |
| `phase32-expanded-retrieval` | 130 | `0.616` | `0.978` | `0.954` |
| `phase33-vector-lexical-rerank-top3` | 130 | `0.778` | `0.950` | `0.965` |

The tradeoff is visible: precision improved, MRR improved, and recall stayed at the target gate, but all-sources hit dropped for some multi-document questions.

## Top-K

`top_k` controls how many chunks are returned to generation.

Smaller top-k:

- reduces noise
- can improve precision
- may omit a needed secondary document

Larger top-k:

- improves odds of source coverage
- increases prompt size and cost
- can make citation selection harder

This matters for multi-document questions because the answer may need chunks from two or more documents.

## Source Coverage

The evaluation layer measures several retrieval concepts:

| Metric | Meaning |
| --- | --- |
| Any-source hit | At least one expected source document appeared. |
| All-sources hit | Every expected source document appeared. |
| Expected-source recall | Fraction of expected source documents retrieved. |
| Precision@k | Fraction of top-k chunks whose document is expected. |
| MRR | Reciprocal rank of the first expected source. |

These metrics judge document-level coverage, not whether the exact sentence was retrieved.

## Known Tradeoffs

| Design choice | Benefit | Limitation |
| --- | --- | --- |
| Section chunks | Human-readable citations and fewer arbitrary splits. | A long section can contain mixed topics. |
| Role filter in SQL | Strong pre-generation permission boundary. | Requires document metadata to be correct. |
| Lexical rerank | Better Precision@k and section/title matching. | Does not plan for all documents needed by a multi-part question. |
| Strict department filter | Clear project/department isolation. | A user may miss relevant cross-department evidence unless asking at project scope. |
| Heuristic multi-doc detection | Cheap and understandable. | It can miss multi-document questions with new wording. |
