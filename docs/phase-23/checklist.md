# Phase 23 Checklist

## App Surface

- [x] Add project scope selection to the live assistant.
- [x] Add optional department narrowing for project questions.
- [x] Show the effective scope in the answer inspection panel.
- [x] Show project and department context on retrieved chunks.
- [x] Preserve Dev/Admin query surfaces as global evaluation tools when no scope is supplied.

## Backend And Retrieval

- [x] Extend query requests and responses with `project_id` and `department_id`.
- [x] Validate project and department scope before retrieval.
- [x] Apply strict project and department filters in vector retrieval.
- [x] Apply strict project and department filters in keyword retrieval.
- [x] Apply the same scope through hybrid and multi-document retrieval.
- [x] Preserve role-based permission filtering before generation.
- [x] Add scope fields to request observability logs.

## Verification

- [x] Run targeted Python compile checks.
- [x] Run API import smoke check.
- [x] Run web production build with `NEXT_DIST_DIR=.next-codex-build`.
- [x] Run `docker compose config --quiet`.
- [ ] Run live scoped query comparison against Postgres.
- [ ] Re-run OpenAI-backed permission and answer evaluations.

## Remaining Work

- Project-scoped benchmark runs are still future work.
- Uploaded PDF documents remain `pending_review` and are not indexed for retrieval.
- Department scope is strict, not a ranking boost.
- Production authentication and project membership remain future phases.
