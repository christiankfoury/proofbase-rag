# Phase 22 PDF Extraction Design

## Goal

Phase 22 adds the first real file ingestion path: department users can upload a PDF, extract deterministic text to Markdown, and review the result in the document library before indexing.

## Product Decisions

- Supported file type: PDF only.
- Extraction method: deterministic `pypdf` text extraction.
- AI cleanup: not used.
- Raw file storage: local `data/uploads/` path, configurable with `UPLOAD_STORAGE_DIR`.
- Local upload limit: 10 MB per PDF.
- Retrieval impact: none until a later approval/indexing step creates chunks and embeddings.

These decisions keep the first upload path cheap, explainable, and honest. They also avoid introducing AI rewriting before there is a human review workflow.

## Ingestion State

Uploaded PDFs create:

- a `documents` row with `source_type = 'pdf'`
- a `document_versions` row with `ingestion_status = 'pending_review'`
- an `ingestion_jobs` row with `status = 'pending_review'` and `stage = 'review_pending'`
- extracted Markdown stored on the version
- raw file bytes stored locally outside git

No `chunks` or `chunk_embeddings` rows are created during upload. Existing retrievers already require `document_versions.ingestion_status = 'indexed'`, so pending-review uploads are not searchable.

## Extraction Metadata

The upload records:

- extractor name
- page count
- pages with extractable text
- extraction confidence
- warnings for pages with no extractable text
- review-required flag

The App surface shows the Markdown preview and status through the Phase 21 document library.

## Limitations

- Scanned PDFs need OCR, which is not included.
- Tables and layout are flattened by text extraction.
- DOCX extraction is deferred.
- Approval and indexing controls are deferred.
- Uploaded source files are local development artifacts, not Azure Blob objects.
