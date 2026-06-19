# Phase 20 Checklist

## App Surface

- [x] Add department create controls inside project workspaces.
- [x] Show departments as cards with icon labels, color, description, document count, chunk count, and access defaults.
- [x] Add `/projects/[projectId]/departments/[departmentId]` department detail pages.
- [x] Support department edit and archive from the detail page.
- [x] Keep App copy honest that department-scoped retrieval is not implemented yet.

## Backend And Data Model

- [x] Add Postgres-backed `project_departments` table.
- [x] Add `documents.department_id` for durable document-to-department mapping.
- [x] Seed Northstar departments from corpus categories: People Operations, HR Admin, IT and Security, IT Admin, Sales, and Management.
- [x] Add department CRUD API endpoints under project routes.
- [x] Audit department create, update, and archive events.
- [x] Use archive semantics rather than hard delete.

## Verification

- [x] Run targeted Python compile checks.
- [x] Run API import smoke check.
- [x] Run web production build with `NEXT_DIST_DIR=.next-codex-build`.
- [ ] Run live department CRUD against Postgres after starting the Docker stack.

## Remaining Work

- Department-scoped assistant behavior is deferred to Phase 23.
- Document library and upload surfaces start in Phase 21.
- Department icons are fixed text icon keys rendered as compact labels because the app does not currently include an icon library.
