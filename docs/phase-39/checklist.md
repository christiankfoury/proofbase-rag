# Phase 39 Checklist

## Goal

Complete multi-document and ambiguity orchestration work without weakening permission filtering or changing benchmark expectations.

## Completed In This Slice

- [x] Added deterministic multi-document source planning for recognizable cross-domain questions.
- [x] Preserved existing permission-filtered retrieval under every planned subquery.
- [x] Changed multi-document merge behavior to keep the best chunk from each planned target source before score-based fill.
- [x] Added local tests for the remaining Phase 38 multi-document failure shapes.
- [x] Kept prompt text, benchmark expectations, and expected sources unchanged.
- [x] Added a guarded full answer-quality evaluator that exercises live `POST /query` orchestration.
- [x] Expanded deterministic multi-document detection for support/engineering incidents, API/data-governance questions, and software/vendor approval overlap.
- [x] Tightened targeted source-planner subqueries for the remaining measured multi-document source shapes.

## Verification Completed

- [x] Run `scripts/run_multi_doc_eval.py --allow-external-ai` after explicit approval.
- [x] Run the current answer-quality candidate with explicit approval to measure before/after impact.
- [x] Run permission evaluation with explicit approval for embeddings.
- [x] Update dashboard exports after approved live evaluation artifacts exist.
- [x] Add or update a full answer-quality evaluator that exercises the live multi-document orchestration path.
- [x] Run `scripts/run_phase39_live_query_answer_quality.py --allow-external-ai --budget-usd 2` after explicit approval.
- [x] Export dashboard data after the approved live `/query` answer-quality artifact exists.

## Remaining Follow-Up

- [ ] Investigate the remaining 4 answer-quality failures (`MULTI-004`, `MULTI-006`, `MULTI-017`, `MULTI-020`) without lowering citation standards or changing benchmark expectations casually.

## Notes

- The approved live `/query` answer-quality run over benchmark v1.1 reports answer accuracy `0.981`, citation accuracy `0.981`, hallucination rate `0.000`, clarification accuracy `1.000`, and `4` failed questions.
- Permission leakage remains `0.000`; unauthorized chunks reaching generation remains `0.000`.
- The remaining failures are kept visible instead of being hidden by weaker citation rules or benchmark edits.
