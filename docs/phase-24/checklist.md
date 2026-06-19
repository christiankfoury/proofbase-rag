# Phase 24 Checklist

## Dev/Admin Surface

- [x] Rename the retrieval playground experience to Algorithm Quality Lab.
- [x] Add named retrieval profiles with profile intent and historical benchmark evidence.
- [x] Compare live profile behavior on one shared question.
- [x] Show retrieved-source coverage and citation-source coverage against reviewer-entered expected documents.
- [x] Keep known failures visible during profile review.
- [x] Add review-note capture for candidate, rejected, and review-only decisions.

## Backend

- [x] Add an audit-backed algorithm review endpoint.
- [x] Store review metadata as an `algorithm_profile_reviewed` audit event when audit storage is available.
- [x] Avoid automatic promotion or benchmark mutation from a single live query.

## Verification

- [x] Run targeted API compile check.
- [x] Run API import smoke check.
- [x] Run web production build with `NEXT_DIST_DIR=.next-codex-build`.
- [x] Run `docker compose config --quiet`.
- [ ] Run a live review-note POST against Postgres.
- [ ] Run full retrieval or answer-quality benchmark comparisons.

## Remaining Work

- Project-scoped evaluation set execution remains future work.
- Review notes are audit events, not durable profile promotion records.
- Full benchmark promotion still requires running evaluation scripts.
- Reranking was not added in this phase.
