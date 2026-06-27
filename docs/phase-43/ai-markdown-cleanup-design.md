# AI Markdown Cleanup Design

Phase 43 keeps deterministic PDF extraction as the source of truth for uploaded documents. Upload still stores the raw PDF locally, extracts Markdown with `pypdf`, and creates a `pending_review` document version with zero chunks and zero embeddings.

AI cleanup is optional and editor-triggered:

1. An editor opens a pending-review or failed uploaded document.
2. The editor clicks `Clean up Markdown`.
3. The API validates project editor access, department ownership, document ownership, and ingestion status before calling OpenAI.
4. OpenAI receives the current extracted Markdown and is instructed to only clean formatting, spacing, headings, bullets, and obvious extraction artifacts.
5. The API rejects empty or unsafe cleanup output.
6. The cleaned Markdown is returned into the review editor.
7. Cleanup metadata is stored on the active document version under `metadata.ai_cleanup`.
8. No chunks or embeddings are created until the editor clicks `Approve and index`.

The stored cleanup metadata includes model, token usage, estimated cost when pricing is available, source hash, cleaned hash, cleanup timestamp, requester, and a `draft_returned_not_indexed` status. Phase 43 intentionally does not persist the cleaned Markdown as a replacement for `extracted_text`; the reviewed editor content becomes durable only through the existing approve/index path.

If OpenAI is unavailable, the editor can continue using deterministic Markdown review and approval. This preserves the Phase 40 local upload workflow and keeps AI cleanup as a polish aid rather than a required ingestion dependency.
