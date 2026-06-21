# Phase 33 Verification

Generated at: 2026-06-21T01:21:57.263664+00:00

## Completed Checks

- `python scripts/test_phase33_reranker.py`
- `python scripts/analyze_phase33_precision.py`
- `python scripts/run_phase33_precision_candidate.py --dry-run`
- `python scripts/export_dashboard_data.py`
- `python scripts/validate_benchmark.py`
- `python -m compileall apps scripts`
- `cd apps/web; $env:NEXT_DIST_DIR='.next-codex-build'; npm run build`

## Diagnostic Result

- Best no-network top-k replay preserving recall and MRR gates: top-3 with Precision@k `0.700`.
- Top-k-only replay does not meet the Phase 33 Precision@k target of `0.75` while preserving recall and MRR.
- Saved top-5 lexical rerank replay is included as a deterministic candidate check, but it cannot inspect chunks outside the saved top-5 pool.
- Dashboard export now includes a `phase33_precision_readiness` block and the Dev/Admin overview shows the candidate as diagnostic readiness evidence, not a publishable improvement.
- Local reranker regression checks confirm the reranker only sees permission-filtered chunks in the test fixture.
- OpenAI-backed live retrieval reruns were skipped because external API use was not approved for this continuation.
- Permission safety was not re-run in this diagnostic-only step.
