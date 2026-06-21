# Phase 35 Verification

Generated at: 2026-06-21T04:20:00+00:00

## Completed Checks

- `python scripts/test_phase35_citation_controls.py`
- `python scripts/analyze_phase35_citation_failures.py`
- `python scripts/run_phase35_citation_candidate.py --dry-run`
- `python scripts/run_phase35_citation_candidate.py` guarded no-approval check
- `python scripts/run_phase35_citation_candidate.py --allow-external-ai --budget-usd 2`
- `python scripts/run_permission_eval.py --retrieval-mode vector_lexical_rerank --top-k 5 --rerank-candidate-limit 20 --allow-external-embeddings --report-path docs/phase-35/permission-safety-results.md --run-name phase35-vector-lexical-rerank-top5-permission-eval`
- `python scripts/analyze_phase35_citation_failures.py --run-path data/evaluation/expanded-baseline/phase35-citation-alignment-v7.json --output-json data/evaluation/phase35-citation-failures-current.json --report-path docs/phase-35/citation-failure-analysis-current.md`
- `python scripts/export_dashboard_data.py`
- `python -m compileall apps/api/app/citations apps/api/app/evaluation apps/api/app/generation scripts/run_phase35_citation_candidate.py scripts/analyze_phase35_citation_failures.py scripts/test_phase35_citation_controls.py`
- `python scripts/validate_benchmark.py`
- `python -m compileall apps scripts`
- `docker compose config --quiet`
- `git diff --check`
- `cd apps/web; $env:NEXT_DIST_DIR='.next-codex-build'; npm run build`
- `python -m py_compile scripts/export_dashboard_data.py`

## Measured Result

- Baseline run: `phase34-answer-grounding-v6`
- Candidate run: `phase35-citation-alignment-v7`
- Benchmark version: `1.1`
- Questions: `130`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `5`
- Reranker: `lexical`
- Rerank candidate limit: `20`
- Prompt version: `v7`
- Model: `gpt-4.1-mini`
- Estimated chat cost: `$0.092994`

## Before / After

| Metric | Phase 34 Baseline | Phase 35 Candidate |
|---|---:|---:|
| Answer accuracy | `0.887` | `0.919` |
| Citation accuracy | `0.887` | `0.950` |
| Faithfulness | `0.896` | `0.880` |
| Hallucination rate | `0.024` | `0.000` |
| Response type accuracy | `0.865` | `0.881` |
| Refusal accuracy | `1.000` | `1.000` |
| Not-found accuracy | `1.000` | `1.000` |
| Clarification accuracy | `0.500` | `0.500` |
| Failed questions | `24` | `16` |

## Citation Failure Categories

| Category | Phase 34 Baseline | Phase 35 Candidate Failed Rows |
|---|---:|---:|
| Wrong document cited | `3` | `1` |
| Right document but wrong chunk | `8` | `6` |
| Citation missing | `15` | `7` |
| Citation attached to unsupported claim | `5` | `1` |
| Citation from restricted source | `0` | `0` |

The stricter all-row citation audit in `docs/phase-35/citation-failure-analysis-current.md` still flags extra or section-imprecise citations on rows that pass the benchmark citation-document metric. Those are kept visible as reviewer evidence, not counted as a benchmark failure unless expected-source coverage fails.

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
- The Phase 35 citation target `>= 0.92` and stretch target `>= 0.95` were met.
- Hallucination did not increase from Phase 34.
- Permission filtering still occurs before generation.
- Remaining failures are concentrated in multi-document completeness, ambiguous-question handling, and a few adversarial answer-completeness cases.
