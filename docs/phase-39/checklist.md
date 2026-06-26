# Phase 39 Checklist

## Goal

Start multi-document and ambiguity orchestration work without weakening permission filtering or changing benchmark expectations.

## Completed In This Slice

- [x] Added deterministic multi-document source planning for recognizable cross-domain questions.
- [x] Preserved existing permission-filtered retrieval under every planned subquery.
- [x] Changed multi-document merge behavior to keep the best chunk from each planned target source before score-based fill.
- [x] Added local tests for the remaining Phase 38 multi-document failure shapes.
- [x] Kept prompt text, benchmark expectations, and expected sources unchanged.

## Pending

- [x] Run `scripts/run_multi_doc_eval.py --allow-external-ai` after explicit approval.
- [x] Run the current answer-quality candidate with explicit approval to measure before/after impact.
- [x] Run permission evaluation with explicit approval for embeddings.
- [x] Update dashboard exports after approved live evaluation artifacts exist.
- [ ] Add or update a full answer-quality evaluator that exercises the live multi-document orchestration path.

## Notes

- This slice does not close Phase 39 because the dedicated multi-doc evaluation improved, but the full answer-quality candidate still uses the single-retrieval prompt-experiment path and reports `7` failures.
- Ambiguity behavior remains the Phase 38 deterministic guard path; this slice focused on source coverage planning for the remaining multi-document failures.
