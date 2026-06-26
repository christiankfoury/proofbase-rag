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

- [ ] Run `scripts/run_multi_doc_eval.py --allow-external-ai` only after explicit approval.
- [ ] Run the current answer-quality candidate with explicit approval to measure before/after impact.
- [ ] Run permission evaluation with explicit approval for embeddings.
- [ ] Update dashboard exports only after approved live evaluation artifacts exist.

## Notes

- This slice starts Phase 39 but does not close it because the required OpenAI-backed evaluation runs were skipped by instruction.
- Ambiguity behavior remains the Phase 38 deterministic guard path; this slice focused on source coverage planning for the remaining multi-document failures.
