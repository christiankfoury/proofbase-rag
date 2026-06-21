# Phase 33 Verification

Generated at: 2026-06-21T01:18:21.341757+00:00

## Completed Checks

- `python scripts/test_phase33_reranker.py`
- `python scripts/analyze_phase33_precision.py`
- `python scripts/run_phase33_precision_candidate.py --dry-run`

## Diagnostic Result

- Best no-network top-k replay preserving recall and MRR gates: top-3 with Precision@k `0.700`.
- Top-k-only replay does not meet the Phase 33 Precision@k target of `0.75` while preserving recall and MRR.
- Saved top-5 lexical rerank replay is included as a deterministic candidate check, but it cannot inspect chunks outside the saved top-5 pool.
- OpenAI-backed live retrieval reruns were skipped because external API use was not approved for this continuation.
- Permission safety was not re-run in this diagnostic-only step.
