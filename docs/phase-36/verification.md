# Phase 36 Verification

## Live Evaluation Runs

| Check | Result |
| --- | --- |
| `python scripts\run_permission_eval.py --phase phase-36 --retrieval-mode vector_lexical_rerank --top-k 5 --rerank-candidate-limit 20 --allow-external-embeddings` | Passed. 20 restricted questions, leakage `0.000`, blocked-answer accuracy `1.000`, unauthorized chunk exposure `0.000`, authorized retrieval accuracy `1.000`. |
| `python scripts\run_memory_eval.py --phase phase-36 --retrieval-mode vector_lexical_rerank --top-k 5 --rerank-candidate-limit 20 --prompt-version v7 --allow-external-ai --budget-usd 2` | Passed. 20 memory questions, answer accuracy `1.000`, citation accuracy `1.000`, follow-up detection `1.000`, query rewrite quality `1.000`, memory permission leakage `0.000`, estimated cost `$0.019946`. |
| `python scripts\run_phase36_memory_permission_boundary.py --allow-external-ai --budget-usd 2` | Passed. 5 boundary probes, memory permission leakage `0.000`, unauthorized chunk exposure `0.000`, restricted citation leakage `0.000`, blocked-answer accuracy `1.000`. |
| `python scripts\export_dashboard_data.py` | Passed. Dashboard export includes 21 runs and Phase 36 eval-run artifacts. |

## Guard Checks

| Check | Result |
| --- | --- |
| `python scripts\run_permission_eval.py --phase phase-36 --retrieval-mode vector_lexical_rerank --top-k 5 --rerank-candidate-limit 20` | Passed guard behavior. Exited before external embedding work and required explicit approval. |
| `python scripts\run_memory_eval.py --phase phase-36 --retrieval-mode vector_lexical_rerank --top-k 5 --rerank-candidate-limit 20 --prompt-version v7` | Passed guard behavior. Exited before external AI work and required explicit approval. |
| `python scripts\run_phase36_memory_permission_boundary.py` | Passed guard behavior. Exited before external AI work and required explicit approval. |

## Static Checks

| Check | Result |
| --- | --- |
| `python scripts\run_permission_eval.py --phase phase-36 --retrieval-mode vector_lexical_rerank --top-k 5 --rerank-candidate-limit 20 --dry-run` | Passed. |
| `python scripts\run_memory_eval.py --phase phase-36 --retrieval-mode vector_lexical_rerank --top-k 5 --rerank-candidate-limit 20 --prompt-version v7 --dry-run` | Passed. |
| `python scripts\run_phase36_memory_permission_boundary.py --dry-run` | Passed. |
| `python -m py_compile scripts\run_permission_eval.py scripts\run_memory_eval.py scripts\run_phase36_memory_permission_boundary.py scripts\export_dashboard_data.py apps\api\app\memory\query_rewriter.py apps\api\app\memory\context_builder.py` | Passed. |
| `python scripts\validate_benchmark.py` | Passed. Benchmark v1.1 contains 130 questions and the expected category counts, including 20 permission and 20 memory questions. |
| `python -m compileall apps scripts` | Passed. |
| `docker compose config --quiet` | Passed with local Windows Docker config access warnings. |
| `cd apps\web; $env:NEXT_DIST_DIR='.next-codex-build'; npm run build` | Passed. |
| `git diff --check` | Passed with line-ending warnings only. |

## Outputs

- `docs/phase-36/permission-safety-results.md`
- `docs/phase-36/memory-evaluation-results.md`
- `docs/phase-36/memory-permission-boundary-results.md`
- `docs/phase-36/failed-memory-question-analysis.md`
- `data/evaluation/phase36-permission-evaluation.json`
- `data/evaluation/phase36-memory-evaluation.json`
- `data/evaluation/phase36-memory-permission-boundary.json`
- `data/evaluation/eval-runs/phase36-permission-evaluation.json`
- `data/evaluation/eval-runs/phase36-memory-evaluation.json`
- `data/evaluation/eval-runs/phase36-memory-permission-boundary.json`
