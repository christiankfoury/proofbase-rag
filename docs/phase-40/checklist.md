# Phase 40 Checklist

## Goal

Complete the local uploaded-document workflow from upload to review, approve/index, and scoped asking.

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
- [x] Ran live local upload -> approve/index -> scoped ask with OpenAI embeddings and chat completion.
- [x] Verified the uploaded document was not searchable before approval, then was indexed, retrieved, and cited after approval.

## Pending

- [ ] Consider editable Markdown review in a later phase; this slice approves extracted Markdown as-is.

## Notes

- Uploaded documents remain unsearchable before approval because retrieval only uses `indexed` current versions.
- The endpoint uses the existing retrieval safety boundary: project, department, current-version, and role filters still apply before generation.
- Live OpenAI-backed verification passed after explicit approval.
