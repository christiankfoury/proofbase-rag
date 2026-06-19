# Phase 19 Checklist

## App Surface

- [x] Add `/projects` as a first-class App route.
- [x] Add `/projects/[projectId]` for project detail links.
- [x] Add a project left panel with active workspace selection.
- [x] Support project create, edit, and archive from the App UI.
- [x] Show seeded `Northstar Analytics` workspace backed by the existing synthetic corpus.
- [x] Show project document count, chunk count, derived department count, quality status, and recent project audit events.
- [x] Keep retrieval behavior unchanged until the project-scoped RAG phase.

## Backend And Data Model

- [x] Add Postgres-backed `projects` table.
- [x] Link existing `documents` rows to the seeded Northstar project.
- [x] Add project CRUD API endpoints.
- [x] Prefer soft archive over hard delete.
- [x] Add audit events for project create, update, and archive.
- [x] Include project schema in readiness and setup verification.

## Dev/Admin Surface

- [x] Keep existing Dev/Admin routes stable.
- [x] Preserve global evaluation outputs and metrics.
- [x] Make project quality status honest: global benchmark measured, project-scoped evaluation pending.

## Documentation

- [x] Add Phase 19 design notes.
- [x] Add Phase 19 verification notes.
- [x] Update README App routes and limitations.
- [x] Update interactive demo and screenshots guidance.

## Verification

- [x] Run `python -m compileall apps scripts`.
- [x] Run API import smoke check.
- [x] Run `docker compose config`.
- [x] Run `npm run build` for the web app using ignored alternate dist dir because the existing `.next\trace` artifact is permission-blocked.
- [ ] Run live CRUD against Postgres after starting the Docker stack.

