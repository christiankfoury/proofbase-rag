# Phase 46 Verification

## Local Checks

- Passed: `python scripts/test_phase46_generalization_remediation.py`
- Passed: `python scripts/test_phase39_multi_doc_orchestration.py`
- Passed: `python scripts/run_generalization_eval.py --dry-run`
- Passed: `python scripts/run_generalization_eval.py --dry-run --run-id phase46-generalization-remediation --run-name "Phase 46 Generalization Remediation" --phase phase-46 --detail-path data/evaluation/generalization-probes/phase46-generalization-remediation.json --eval-run-path data/evaluation/eval-runs/phase46-generalization-remediation.json --report-path docs/phase-46/remediation-results.md --report-title "Phase 46 Remediation Results" --remediation-run`
- Passed approval guard: `python scripts/run_generalization_eval.py --run-id phase46-generalization-remediation --run-name "Phase 46 Generalization Remediation" --phase phase-46 --detail-path data/evaluation/generalization-probes/phase46-generalization-remediation.json --eval-run-path data/evaluation/eval-runs/phase46-generalization-remediation.json --report-path docs/phase-46/remediation-results.md --report-title "Phase 46 Remediation Results" --remediation-run`
- Passed: `python -m compileall apps/api/app scripts`
- Passed: `python scripts/validate_benchmark.py`
- Passed with the known local Docker credential warning: `docker compose config --quiet`
- Passed: `git diff --check`
- Passed: `cd apps/web; $env:NEXT_DIST_DIR='.next-codex-build'; $env:NEXT_TELEMETRY_DISABLED='1'; npm run build`

## Approved Live Checks

- Passed: `python scripts/run_generalization_eval.py --allow-external-ai --run-id phase46-generalization-remediation --run-name "Phase 46 Generalization Remediation" --phase phase-46 --detail-path data/evaluation/generalization-probes/phase46-generalization-remediation.json --eval-run-path data/evaluation/eval-runs/phase46-generalization-remediation.json --report-path docs/phase-46/remediation-results.md --report-title "Phase 46 Remediation Results" --remediation-run`
  - Run ID: `phase46-generalization-remediation`
  - Probe count: `20`
  - Failed probes: `0`
  - Behavior accuracy: `1.000`
  - Memory rewrite quality: `0.800`
  - Clarification behavior: `1.000`
  - Answer/citation quality: `1.000`
  - Permission safety: `1.000`
  - Memory-as-evidence violation rate: `0.000`
  - Estimated chat cost: `$0.013838`
- Passed after one detected regression was fixed: `python scripts/run_phase39_live_query_answer_quality.py --allow-external-ai --budget-usd 2`
  - Run ID: `phase39-live-query-answer-quality-v8`
  - Benchmark version: `1.1`
  - Sample size: `130`
  - Failed questions: `0`
  - Answer accuracy: `1.000`
  - Citation accuracy: `1.000`
  - Hallucination rate: `0.000`
  - Clarification accuracy: `1.000`
  - Estimated cost: `$0.078679`
- Passed: `python scripts/run_permission_eval.py --phase phase-46 --run-id phase46-permission-evaluation --run-name phase46-permission-evaluation --report-path docs/phase-46/permission-safety-results.md --detail-path data/evaluation/phase46-permission-evaluation.json --eval-run-path data/evaluation/eval-runs/phase46-permission-evaluation.json --allow-external-embeddings`
  - Permission leakage: `0.000`
  - Blocked-answer accuracy: `1.000`
  - Unauthorized chunk exposure: `0.000`
  - Restricted citation leakage: `0.000`
  - Unauthorized chunks reached generation: `0.000`
  - Authorized retrieval accuracy: `1.000`
  - Authorized answer accuracy: `pending`
- Passed: `python scripts/export_dashboard_data.py`

## Notes

- The first Phase 46 generalization live run reached 4 failed probes before the probe department constants were corrected.
- The first Phase 39 regression rerun exposed `MULTI-008`; a direct retrieved-evidence answer was added and the rerun returned zero failed benchmark questions.
