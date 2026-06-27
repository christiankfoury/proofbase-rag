# Phase 43 Checklist

Goal: add an editor-triggered AI Markdown cleanup draft for uploaded documents without weakening deterministic extraction, human review, or approval-gated indexing.

## Scope

- [x] Add editor-only cleanup endpoint for pending-review or failed department documents.
- [x] Require project, department, and document ownership checks before cleanup.
- [x] Use the current extracted Markdown as the cleanup input.
- [x] Return cleaned Markdown to the editor and leave indexing unchanged until approve/index.
- [x] Store cleanup metadata on the document version without replacing `extracted_text`.
- [x] Add frontend cleanup, loading, error, and revert-to-extraction states.
- [x] Keep deterministic review/index path available when OpenAI cleanup is unavailable.

## Out Of Scope

- Automatic cleanup on upload.
- Indexing cleaned Markdown without editor approval.
- Cross-process cleanup cache.
- Azure Blob Storage or hosted storage migration.
- Diff view and richer cleanup audit display, which remain Phase 44 work.

## Acceptance Notes

- Cleanup is an explicit editor action in the Markdown review panel.
- Retrieved chunks are still created only by the existing approve/index endpoint.
- Existing retrieval filters continue to require `document_versions.ingestion_status = 'indexed'`, so pending cleanup drafts are not searchable.
