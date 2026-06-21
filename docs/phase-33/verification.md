# Phase 33 Verification

Generated at: 2026-06-21T01:46:17.936920+00:00

## Completed Checks

- `python scripts/test_phase33_reranker.py`
- `python scripts/analyze_phase33_precision.py`
- `python scripts/run_phase33_precision_candidate.py --dry-run`
- `python scripts/run_phase33_no_egress_candidates.py`
- `python scripts/export_dashboard_data.py`
- `python scripts/validate_benchmark.py`
- `python -m compileall apps scripts`
- `cd apps/web; $env:NEXT_DIST_DIR='.next-codex-build'; npm run build`

## Diagnostic Result

- Best no-network top-k replay preserving recall and MRR gates: top-3 with Precision@k `0.700`.
- Top-k-only replay does not meet the Phase 33 Precision@k target of `0.75` while preserving recall and MRR.
- Saved top-5 lexical rerank replay with same-document boost reaches top-3 Precision@k `0.774` while preserving recall and MRR gates, but it cannot inspect chunks outside the saved top-5 pool.
- No-egress keyword-only top-k sweep was run locally against Postgres full-text retrieval. No candidate satisfies all Phase 33 retrieval gates: top-1 reaches Precision@k `0.878` but recall is `0.765`; top-4 preserves recall at `0.961` but Precision@k is `0.561` and MRR is `0.921`.
- No-egress keyword-only retrieval-boundary checks showed unauthorized chunk exposure `0.000` and unauthorized chunks reached generation `0.000` for the restricted benchmark questions.
- Local reranker regression checks confirm the reranker only sees permission-filtered chunks in the test fixture.
- OpenAI-backed live retrieval rerun was attempted, but approval was rejected because it would send benchmark question text to the external embeddings API. It still requires explicit user approval after the data-egress risk is understood.
- Full permission safety with answer/refusal and citation checks was not re-run because the existing script can call answer generation; the no-egress permission result above is retrieval-boundary-only.
