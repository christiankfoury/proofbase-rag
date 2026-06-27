# Phase 44 Checklist

Goal: make AI Markdown cleanup auditable and understandable without letting AI cleanup become an automatic correctness or indexing claim.

## Scope

- [x] Show cleanup metadata in the upload review panel.
- [x] Show a before/after style comparison between deterministic extraction and the current review editor.
- [x] Keep revert-to-extraction available and record the revert server-side.
- [x] Track whether the reviewer edited the AI cleanup draft before approve/index.
- [x] Add audit events for cleanup requested, cleanup succeeded, cleanup failed, reverted, and approved/indexed after cleanup.
- [x] Preserve approve/index as the only path that writes reviewed Markdown into indexed chunks.

## Out Of Scope

- Chunking strategy changes.
- AI summaries that remove details.
- Persistent content or secret cache.
- Production storage migration.

## Acceptance Notes

- Cleanup provenance is visible in the App-side document review surface.
- Editors keep final control over the Markdown that becomes searchable.
- The UI says cleanup is a draft, not validation.
