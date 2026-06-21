# Phase 37 Verification

## Checks

| Check | Result |
| --- | --- |
| `python scripts\export_dashboard_data.py` | Passed. Wrote dashboard summary, regression scorecard, eval-run artifacts, and failed-question export. |

## Scorecard Snapshot

| Metric | Baseline | Current | Delta | Status |
| --- | ---: | ---: | ---: | --- |
| Source Recall | 0.978 | 0.950 | -0.028 | Pass |
| Precision@k | 0.616 | 0.778 | +0.162 | Pass |
| MRR / First Source Rank | 0.954 | 0.965 | +0.011 | Pass |
| Answer Accuracy | 0.850 | 0.919 | +0.069 | Pass |
| Citation Accuracy | 0.844 | 0.950 | +0.106 | Pass |
| Hallucination Rate | 0.205 | 0.000 | -0.205 | Pass |
| Permission Leakage Rate | 0.000 | 0.000 | 0.000 | Pass |
| Memory Answer Accuracy | 1.000 | 1.000 | 0.000 | Pass |

## Final Verification

| Check | Result |
| --- | --- |
| `python scripts\validate_benchmark.py` | Passed. Benchmark v1.1 has 130 declared questions and expected category counts. |
| `python -m compileall apps scripts` | Passed. |
| `docker compose config --quiet` | Passed with local Windows Docker config access warnings. |
| `git diff --check` | Passed with line-ending warnings only. |
| `cd apps\web; $env:NEXT_DIST_DIR='.next-codex-build'; npm run build` | Passed. |
