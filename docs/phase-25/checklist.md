# Phase 25 Checklist

## Dev/Admin Surface

- [x] Add human review controls to failed-question detail views.
- [x] Add human review controls to negative feedback items.
- [x] Support answer correctness labels using the existing `1.0`, `0.5`, `0.0` rubric.
- [x] Support citation correctness labels using the existing `1.0`, `0.5`, `0.0` rubric.
- [x] Allow feedback to become an evaluation candidate only after reviewer decision.
- [x] Keep review decisions separate from benchmark promotion.

## Backend And Data Model

- [x] Add `evaluation_reviews` persistence table.
- [x] Add API endpoints for saving and listing review decisions.
- [x] Store expected answer, expected sources, actual citations, retrieved chunks, reviewer labels, decision, and notes.
- [x] Audit saved review decisions.

## Verification

- [x] Run targeted Python compile checks.
- [x] Run API import smoke check.
- [x] Run web production build with `NEXT_DIST_DIR=.next-codex-build`.
- [x] Run `docker compose config --quiet`.
- [ ] Save a live review decision against Postgres.
- [ ] Re-run an evaluation using approved review candidates.

## Remaining Work

- Approved review candidates are not automatically appended to benchmark JSON.
- Project-level benchmark authoring is not complete.
- Review queues are seeded from current failed questions and negative feedback, not a dedicated assignment system.
