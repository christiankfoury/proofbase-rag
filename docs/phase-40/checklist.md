# Phase 40 Checklist

## Goal

Start the local uploaded-document workflow from upload to review, approve/index, and scoped asking.

## Completed In This Slice

- [x] Added `POST /projects/{project_id}/departments/{department_id}/documents/{document_id}/approve-index`.
- [x] Required project editor access before approval/indexing.
- [x] Indexed only the current pending-review or failed document version.
- [x] Created chunks and embeddings only after explicit approval.
- [x] Marked document versions and ingestion jobs as `indexed` or `failed`.
- [x] Added App-side approve/index action for pending or failed uploaded documents.
- [x] Added scoped chat link from indexed department documents.
- [x] Added `/chat?project=...&department=...` scope initialization.
- [x] Added mocked local tests for successful indexing and embedding failure handling.

## Pending

- [ ] Run a live local Postgres upload -> approve/index check.
- [ ] Run a scoped question against an approved uploaded document with OpenAI embeddings available.
- [ ] Add richer retry/status UX if live testing uncovers long-running indexing needs.
- [ ] Consider editable Markdown review in a later phase; this slice approves extracted Markdown as-is.

## Notes

- Uploaded documents remain unsearchable before approval because retrieval only uses `indexed` current versions.
- The endpoint uses the existing retrieval safety boundary: project, department, current-version, and role filters still apply before generation.
- Live OpenAI-backed verification was skipped by instruction.
