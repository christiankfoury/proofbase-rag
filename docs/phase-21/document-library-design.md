# Phase 21 Document Library Design

## Goal

Phase 21 turns department workspaces into real document workspaces without adding file parsing complexity yet. The App side can now show which indexed source documents belong to a department, what version is active, how indexing finished, and what Markdown text is available for retrieval.

## Product Behavior

Department pages now include:

- document list scoped to the selected department
- status badge from the current document version
- chunk count and sensitivity
- access roles attached to each document
- active version metadata
- source path and content hash
- extracted Markdown preview
- disabled upload controls with Phase 22 copy

This gives recruiters and engineering reviewers a product-shaped document management surface while avoiding a false claim that upload extraction is implemented.

## Data Model

`ingestion_jobs` stores durable ingestion state for future uploads:

- project and department
- linked document and document version
- source file name and type
- status and stage
- status detail
- content hash
- started, completed, failed timestamps
- error message and metadata

Seeded Markdown ingestion now upserts one indexed ingestion job per current document version. Existing `document_versions.ingestion_status` remains the source of truth for whether a version is indexed.

## API

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/projects/{project_id}/documents` | List project documents, optionally filtered by `department_id`. |
| `GET` | `/projects/{project_id}/departments/{department_id}/documents` | List documents linked to one department. |

Both endpoints are read-only in this phase. They do not change retrieval, chunking, embeddings, or answer generation.

## Permission Boundary

Phase 21 exposes document metadata to the App workspace but does not add a new end-user authorization layer. Retrieval permissions are unchanged: role filtering still happens before generation in the existing retrieval path.

The document library shows `access_roles`, `sensitivity`, and `restricted` status so permission posture is visible before Phase 23 adds project/department retrieval filters.

## Deferred Work

- Parse new uploaded files.
- Store raw uploaded files.
- Normalize PDFs or DOCX files into Markdown.
- Require human review before indexing.
- Scope `/chat` retrieval by project or department.
