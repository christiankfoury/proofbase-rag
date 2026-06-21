# Phase 38 Verification

## Completed Checks

| Check | Result |
| --- | --- |
| `python scripts/build_phase38_failure_matrix.py --source-ref HEAD` | Passed. Wrote the pre-remediation 16-case matrix to `data/evaluation/phase38-failure-matrix.json` and `docs/phase-38/failure-matrix.md`. |
| `python scripts/run_phase38_answer_quality_candidate.py --dry-run` | Passed. Confirmed run config and output paths. |
| `python scripts/run_phase38_answer_quality_candidate.py` | Passed guarded no-approval check; refused external AI without `--allow-external-ai`. |
| `python scripts/test_phase38_answer_quality_controls.py` | Passed. |
| `python scripts/test_phase35_citation_controls.py` | Passed. |
| `python scripts/test_phase34_grounding_controls.py` | Passed. |
| `python scripts/run_phase38_answer_quality_candidate.py --allow-external-ai --budget-usd 0.20` | Passed. Final promoted run: `phase38-answer-quality-remediation-v8`. |
| `python scripts/run_permission_eval.py --phase phase-38 --run-id phase38-permission-evaluation --run-name phase38-vector-lexical-rerank-top5-permission-eval --retrieval-mode vector_lexical_rerank --top-k 5 --rerank-candidate-limit 20 --allow-external-embeddings --report-path docs\phase-38\permission-safety-results.md --detail-path data\evaluation\phase38-permission-evaluation.json --eval-run-path data\evaluation\eval-runs\phase38-permission-evaluation.json` | Passed. |
| `python scripts/export_dashboard_data.py` | Passed. Dashboard now exports 6 current failed questions. |
| `python scripts/validate_benchmark.py` | Passed. |
| `python -m compileall apps scripts` | Passed. |
| `docker compose config --quiet` | Passed with the known local Windows Docker config access warning. |
| `git diff --check` | Passed with line-ending warnings only. |
| `cd apps/web; $env:NEXT_DIST_DIR='.next-codex-build'; npm run build` | Passed after sandboxed Node hit the known Windows profile `EPERM` issue and the build was rerun elevated. |

## Final Answer-Quality Run

- Run ID: `phase38-answer-quality-remediation-v8`
- Benchmark version: `1.1`
- Sample size: `130`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `5`
- Reranker: `lexical`
- Rerank candidate limit: `20`
- Prompt version: `v8`
- Model: `gpt-4.1-mini`
- Estimated chat cost: `$0.085360`

| Metric | Phase 35 Current | Phase 38 Final |
| --- | ---: | ---: |
| Answer accuracy | `0.919` | `0.975` |
| Citation accuracy | `0.950` | `0.969` |
| Faithfulness | `0.880` | `0.884` |
| Hallucination rate | `0.000` | `0.000` |
| Response type accuracy | `0.881` | `0.923` |
| Refusal accuracy | `1.000` | `1.000` |
| Not-found accuracy | `1.000` | `1.000` |
| Clarification accuracy | `0.500` | `1.000` |
| Failed questions | `16` | `6` |

## Permission Gate

- Run ID: `phase38-permission-evaluation`
- Restricted benchmark questions: `20`
- Permission leakage rate: `0.000`
- Blocked-answer accuracy: `1.000`
- Unauthorized chunk exposure rate: `0.000`
- Restricted citation leakage rate: `0.000`
- Unauthorized chunks reached generation rate: `0.000`
- Authorized retrieval accuracy: `1.000`
- Authorized answer accuracy: `pending` by default to avoid extra chat-completion cost.

## Notes

- The OpenAI-backed runs used the existing `.env` key after `Settings.openai_api_key` was fixed to accept `OPENAI_API_KEY`.
- Benchmark expected answers, expected behavior, and expected sources were not changed.
- Final unresolved cases remain visible in `data/evaluation/failed-questions/failed-questions.json` and the Dev/Admin failed-question page.
