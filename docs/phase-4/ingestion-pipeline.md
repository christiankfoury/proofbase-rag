# Ingestion Pipeline Design

## Purpose

The ingestion pipeline converts raw company documents into normalized, searchable, permission-aware chunks with embeddings and full-text indexes.

Phase 5 should implement Markdown ingestion only, using `data/synthetic-documents/`. The design leaves room for PDF, DOCX, PPTX, CSV, XLSX, HTML, and wiki pages later.

## Supported Source Types

| Source Type | Phase | Notes |
|---|---|---|
| Markdown | Phase 5 | First supported format; parse frontmatter and headings |
| PDF | Later | Requires text extraction and page metadata |
| DOCX | Later | Requires paragraph/heading extraction |
| PPTX | Later | Requires slide extraction |
| CSV/XLSX | Later | Requires table-aware extraction |
| HTML/wiki | Later | Requires DOM/heading normalization |

## Ingestion Statuses

- `uploaded`
- `extracting`
- `chunking`
- `embedding`
- `indexed`
- `failed`
- `archived`

## Pipeline Steps

1. Admin uploads file through API.
2. Backend stores raw file in Azure Blob Storage.
3. Backend creates `documents` and `document_versions` records.
4. File type is detected.
5. Text is extracted.
6. Markdown metadata header is parsed in Phase 5.
7. Document structure is normalized into sections and headings.
8. Permissions are applied from metadata or admin input.
9. Chunks are created using the selected chunking strategy.
10. Embeddings are generated through OpenAI.
11. Chunks and embeddings are stored in PostgreSQL/pgvector.
12. Full-text search `tsvector` is generated for each chunk.
13. Document version is marked `indexed`.
14. Ingestion events, latency, failures, and actor are logged.

## Failure Handling

When ingestion fails:

- Set `document_versions.ingestion_status = 'failed'`.
- Store `failure_reason`.
- Keep raw blob for retry.
- Do not expose failed versions in retrieval.
- Allow an admin to retry after metadata or file correction.
- Write an audit log for failed ingestion if the document is restricted.

## Phase 5 Markdown Rules

Markdown ingestion should:

- Read YAML-style frontmatter.
- Extract `document_id`, `title`, `department`, `category`, `access_roles`, `restricted`, `version`, `effective_date`, `owner`, `review_cycle`, and `summary`.
- Split body by headings.
- Preserve section heading for citations.
- Create one or more chunks per section.
- Store document permissions based on `access_roles`.

## Document and Chunk Models

Document metadata example:

```json
{
  "external_document_id": "HR-002",
  "title": "PTO and Leave Policy",
  "department": "People Operations",
  "category": "HR Public",
  "source_type": "markdown",
  "version": "1.0",
  "effective_date": "2026-01-15",
  "owner": "People Operations",
  "access_roles": ["Employee", "Sales Representative", "Manager", "HR Admin", "IT Admin"],
  "restricted": false
}
```

Section example:

```json
{
  "document_id": "HR-002",
  "document_version_id": "uuid",
  "section_heading": "Vacation Entitlement",
  "section_index": 1,
  "text": "Full-time employees receive 20 paid vacation days per calendar year."
}
```

Chunk example:

```json
{
  "chunk_id": "uuid",
  "document_id": "HR-002",
  "document_version_id": "uuid",
  "section_heading": "Vacation Entitlement",
  "chunk_index": 0,
  "content": "Full-time employees receive 20 paid vacation days per calendar year...",
  "chunking_strategy": "section_based",
  "token_count": 96,
  "citation_metadata": {
    "document_title": "PTO and Leave Policy",
    "section_heading": "Vacation Entitlement",
    "page_number": null,
    "line_start": null,
    "line_end": null
  }
}
```

Citation example:

```json
{
  "document_id": "HR-002",
  "document_title": "PTO and Leave Policy",
  "section_heading": "Vacation Entitlement",
  "chunk_id": "uuid",
  "quote": "Full-time employees receive 20 paid vacation days per calendar year.",
  "confidence_score": 0.0,
  "validation_status": "pending"
}
```

## Chunking Strategies

Record `chunking_strategy` on every chunk.

| Strategy | How It Works | Pros | Cons | Metrics |
|---|---|---|---|---|
| `fixed_size` | Split by token count with overlap | Simple and predictable | Can split policy sections badly | Retrieval hit rate, citation accuracy |
| `section_based` | Split by Markdown headings | Strong citations and policy alignment | Uneven chunk sizes | Citation accuracy, answer faithfulness |
| `semantic` | Split by meaning/topic | Better coherence | More complexity and harder reproducibility | Precision@k, answer accuracy |
| `small_chunks` | Short token windows | Precise retrieval | May miss context | Precision@k, answer completeness |
| `large_chunks` | Larger token windows | More context | More noise and cost | Recall@k, latency, cost per answer |

Phase 5 default: `section_based`.
