# Phase 34 Verification

Generated at: 2026-06-21T03:32:18.823850+00:00

## Completed Checks

- `python scripts/test_phase34_grounding_controls.py`
- `python scripts/run_phase34_abstention_candidate.py --dry-run`
- `python scripts/run_phase34_abstention_candidate.py` guarded no-approval check
- `python scripts/run_phase34_abstention_candidate.py --allow-external-ai --budget-usd 2`
- `python scripts/run_permission_eval.py --retrieval-mode vector_lexical_rerank --top-k 3 --rerank-candidate-limit 20 --allow-external-embeddings --report-path docs/phase-34/permission-safety-results.md --run-name phase34-vector-lexical-rerank-permission-eval`
- `python scripts/export_dashboard_data.py`
- `python scripts/test_phase33_permission_eval_config.py`
- `python scripts/validate_benchmark.py`
- `python -m py_compile apps/api/app/citations/citation_validator.py apps/api/app/generation/answer_generator.py apps/api/app/experiments/config.py apps/api/app/experiments/runner.py scripts/run_phase34_abstention_candidate.py scripts/test_phase34_grounding_controls.py scripts/run_permission_eval.py`
- `python -m compileall apps scripts`
- `git diff --check`
- `cd apps/web; $env:NEXT_DIST_DIR='.next-codex-build'; npm run build`

## Measured Result

- Baseline run: `phase32-expanded-answer-generation-v5`
- Candidate run: `phase34-answer-grounding-v6`
- Benchmark version: `1.1`
- Questions: `130`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `3`
- Reranker: `lexical`
- Rerank candidate limit: `20`
- Prompt version: `v6`
- Model: `gpt-4.1-mini`
- Estimated chat cost: `$0.075913`

## Before / After

| Metric | Phase 32 Baseline | Phase 34 Candidate |
|---|---:|---:|
| Answer accuracy | `0.850` | `0.887` |
| Citation accuracy | `0.844` | `0.887` |
| Faithfulness | `0.800` | `0.896` |
| Hallucination rate | `0.205` | `0.024` |
| Response type accuracy | `0.758` | `0.865` |
| Refusal accuracy | `0.550` | `1.000` |
| Not-found accuracy | `0.950` | `1.000` |
| Clarification accuracy | `0.500` | `0.500` |
| Failed questions | `43` | `24` |

## Permission Gate

- Restricted benchmark questions tested: `20`
- Permission leakage rate: `0.000`
- Blocked-answer accuracy: `1.000`
- Unauthorized chunk exposure rate: `0.000`
- Restricted citation leakage rate: `0.000`
- Unauthorized chunks reached generation rate: `0.000`
- Authorized retrieval accuracy: `1.000`
- Authorized answer accuracy remains `pending` by default to avoid extra chat-completion cost.

## Notes

- The live answer-quality run used external OpenAI embeddings and chat completions after explicit approval for this synthetic portfolio project.
- The target hallucination rate `<= 0.08` was met.
- Answer accuracy did not regress.
- Permission filtering still occurs before generation.
- Remaining failures are concentrated in multi-document completeness/citation coverage, ambiguous-question handling, and adversarial prompt-injection answer completeness.
