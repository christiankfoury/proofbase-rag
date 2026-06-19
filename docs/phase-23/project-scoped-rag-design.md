# Phase 23 Project-Scoped RAG Design

## Goal

Phase 23 makes the assistant behave like a project workspace product: a user can ask within a selected project, optionally narrow to a department, and inspect evidence that came from that scope after role filtering.

## Scope Semantics

- Project scope is strict when `project_id` is supplied.
- Department scope is strict when `department_id` is supplied.
- Department scope requires project scope.
- Requests with no scope preserve the existing global retrieval path for Dev/Admin pages and historical benchmark tooling.
- Role filtering still happens before chunks reach answer generation.

This keeps the App side product-like without invalidating existing global evaluation outputs.

## Backend Flow

`POST /query` now accepts:

- `project_id`
- `department_id`

The API validates UUID shape, confirms the project exists, and confirms the department belongs to the project when department scope is supplied. The resulting `RetrievalConfig` carries scope into:

- vector retrieval
- keyword retrieval
- hybrid retrieval
- multi-document subquery retrieval

Vector and keyword SQL both filter active indexed documents by `documents.project_id` and `documents.department_id` before ranking and before permission-filtered allowed rows are returned.

## Response And Observability

Responses include:

- `scope.project_id`
- `scope.department_id`
- `project_id` and `department_id` on each retrieved chunk payload

Request observability logs include the same scope fields so scoped App activity can be separated from global Dev/Admin activity.

## Frontend Flow

The `/chat` page loads durable projects, defaults to the seeded Northstar workspace when present, and lets the user select:

- project
- all departments in that project
- one department in that project

The answer panel shows whether the result was global, project-scoped, or department-scoped. Retrieved context cards show the source chunk's project and department IDs for auditability.

## Limitations

- The UI shows IDs rather than friendly department names in retrieved chunk payloads because retrieval currently returns normalized document metadata, not joined project labels.
- Project-scoped evaluation sets have not been generated yet.
- No production auth or project membership enforcement exists; demo role selection remains the only user control.
- Uploaded PDFs are still excluded until review approval and indexing are implemented.
