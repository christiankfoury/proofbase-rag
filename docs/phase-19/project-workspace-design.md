# Phase 19 Project Workspace Design

## Goal

Phase 19 turns projects into first-class knowledge workspaces. This gives the App side a real product surface before later phases add editable departments, document upload, extraction, and project-scoped retrieval.

## Product Behavior

The App side now includes:

- `/projects`: project list and workspace management.
- `/projects/[projectId]`: direct link to a selected project workspace.
- Project create, edit, and archive controls.
- Left project panel with counts for departments, documents, and indexed chunks.
- Project Home showing coverage, quality status, settings, and recent project audit events.

The seeded project is `Northstar Analytics`. It is backed by the existing synthetic corpus and is marked as seeded data in the UI.

## Data Model

`projects` is a durable Postgres table with:

- `id`
- `name`
- `description`
- `status`
- `default_retrieval_profile`
- `seeded_data_key`
- `quality_status`
- `quality_summary`
- timestamps and `archived_at`

`documents.project_id` links documents to a project. The schema migration assigns current documents to the seeded Northstar project. Retrieval still ignores this column in Phase 19.

## API

New endpoints:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/projects` | List active projects, with counts. |
| `POST` | `/projects` | Create a project. |
| `GET` | `/projects/{project_id}` | Load project detail with derived departments and recent project audit events. |
| `PATCH` | `/projects/{project_id}` | Update project metadata. |
| `DELETE` | `/projects/{project_id}` | Soft archive a project. |

Project mutations write audit events:

- `project_created`
- `project_updated`
- `project_archived`

## Retrieval And Evaluation Boundary

This phase does not change `/query`, retrieval SQL, generation prompts, citation validation, permission filtering, or benchmark scoring. Project and department filters are intentionally deferred to Phase 23.

The Northstar quality status references existing global evaluation outputs. New projects show `Project evaluation pending` and do not claim indexed documents or project-specific benchmark results.

## Limitations

- Department rows are derived from current document metadata; department CRUD starts in Phase 20.
- Upload and extraction are not implemented.
- Project-scoped retrieval is not enforced yet.
- Project-scoped evaluation sets are not implemented.
- Live CRUD verification requires a running Postgres-backed API.

