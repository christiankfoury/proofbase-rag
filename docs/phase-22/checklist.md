# Phase 22 Checklist

## App Surface

- [x] Enable PDF upload from a department workspace.
- [x] Extract PDF text into reviewable Markdown.
- [x] Save uploaded PDFs as pending-review documents.
- [x] Show uploaded documents in the existing department document library.
- [x] Keep App copy clear that pending-review uploads are not indexed for retrieval.

## Backend And Data Model

- [x] Add deterministic PDF text extraction with `pypdf`.
- [x] Store raw uploaded PDF files under configurable local storage.
- [x] Add upload storage config and ignore local uploads in git.
- [x] Create `documents`, `document_versions`, and `ingestion_jobs` records for pending-review uploads.
- [x] Add `pending_review` to the ingestion job state machine.
- [x] Avoid chunking and embedding uploads during extraction review.

## Verification

- [x] Run targeted Python compile checks.
- [x] Run API import smoke check.
- [x] Run PDF extractor import check.
- [x] Extract text from a generated sample PDF.
- [x] Run web production build with `NEXT_DIST_DIR=.next-codex-build`.
- [x] Run `docker compose config --quiet`.
- [ ] Run live multipart upload against Postgres after applying schema.

## Remaining Work

- Human approval and indexing of reviewed Markdown remain future work.
- DOCX extraction is not implemented.
- OCR and layout/table reconstruction are not implemented.
- Project- and department-scoped retrieval is deferred to Phase 23.
