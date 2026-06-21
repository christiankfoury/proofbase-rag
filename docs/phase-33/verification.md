# Phase 33 Verification

Generated at: 2026-06-21T02:47:01.241748+00:00

## Completed Checks

- `python scripts/test_phase33_reranker.py`
- `python scripts/test_phase33_precision_candidate_config.py`
- `python scripts/test_phase33_permission_eval_config.py`
- `python scripts/test_phase33_restricted_policy.py`
- `python scripts/run_phase33_precision_candidate.py` guarded no-approval check
- `python scripts/run_permission_eval.py --retrieval-mode vector_lexical_rerank --top-k 3 --rerank-candidate-limit 20` guarded no-approval check
- `python scripts/run_permission_eval.py --help`
- `python scripts/analyze_phase33_precision.py`
- `python scripts/run_phase33_precision_candidate.py --dry-run`
- `python scripts/run_phase33_precision_candidate.py --top-k 3 --candidate-limit 20 --allow-external-embeddings`
- `python scripts/run_permission_eval.py --retrieval-mode vector_lexical_rerank --top-k 3 --rerank-candidate-limit 20 --allow-external-embeddings`
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
- The precision and permission candidate commands now require `--allow-external-embeddings` before any live `vector_lexical_rerank` run can send benchmark question text to the embeddings API.
- The permission evaluator supports the `vector_lexical_rerank` candidate command with top-k `3` and rerank candidate limit `20`.
- After explicit approval, the live `vector_lexical_rerank` top-k `3` candidate over benchmark v1.1 produced Precision@k `0.778`, expected-source recall `0.950`, MRR `0.965`, and 7 failed source-coverage questions, passing the Phase 33 retrieval gates.
- Matching live permission safety over 20 restricted questions produced permission leakage `0.000`, blocked-answer accuracy `1.000`, unauthorized chunk exposure `0.000`, restricted citation leakage `0.000`, unauthorized chunks reached generation `0.000`, and authorized retrieval accuracy `1.000`.
- Authorized answer accuracy remains `pending` by default to avoid extra chat-completion cost; source access for authorized roles was measured and passed.
