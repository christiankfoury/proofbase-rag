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
- [x] Added admin-only evaluation document-prefix exclusions so live benchmark and permission eval runs exclude uploaded `UPLOAD-` fixtures before generation.
- [x] Fixed the remaining measured multi-document evidence-use misses without changing prompts, benchmark expectations, or permission rules.
- [x] Split answer/citation failed-question count from lower-level submetric issue count.

## Verification Completed

- [x] Run `scripts/run_multi_doc_eval.py --allow-external-ai` after explicit approval.
- [x] Run the current answer-quality candidate with explicit approval to measure before/after impact.
- [x] Run permission evaluation with explicit approval for embeddings.
- [x] Update dashboard exports after approved live evaluation artifacts exist.
- [x] Add or update a full answer-quality evaluator that exercises the live multi-document orchestration path.
- [x] Run `scripts/run_phase39_live_query_answer_quality.py --allow-external-ai --budget-usd 2` after explicit approval.
- [x] Export dashboard data after the approved live `/query` answer-quality artifact exists.

## Remaining Follow-Up

- [ ] Investigate the `21` submetric issues separately from answer/citation failure count: `20` memory rows receive half-credit on response-type behavior and `AMB-004` still has source-coverage below full credit while returning the correct clarification behavior.

## Notes

- The approved clean live `/query` answer-quality run over benchmark v1.1 reports answer accuracy `1.000`, citation accuracy `1.000`, hallucination rate `0.000`, clarification accuracy `1.000`, failed-question count `0`, and submetric issue count `21`.
- Permission leakage remains `0.000`; unauthorized chunks reaching generation remains `0.000`.
- Uploaded-document fixtures are excluded from benchmark/eval retrieval before generation; normal uploaded-document chat remains available outside eval runs.
