# Phase 45 Verification

Generated during Phase 45 implementation.

## Local Checks

- Passed: `python scripts/run_generalization_eval.py --dry-run`
- Passed approval guard: `python scripts/run_generalization_eval.py`
- Passed: `python -m compileall apps/api/app scripts`
- Passed: `python scripts/validate_benchmark.py`
- Passed with known local Docker config warning: `docker compose config --quiet`

## Approved Live Check

- Passed: `python scripts/run_generalization_eval.py --allow-external-ai`
  - Run ID: `phase45-generalization-baseline`
  - Probe suite: `generalization-probes-v0`
  - Sample size: `20`
  - Failed probes: `12`
  - Behavior accuracy: `0.500`
  - Memory rewrite quality: `0.667`
  - Clarification behavior: `0.000`
  - Answer/citation quality: `0.583`
  - Permission safety: `1.000`
  - Memory-as-evidence violation rate: `0.000`
  - Estimated chat cost: `$0.023205`
- Passed: `python scripts/run_permission_eval.py --phase phase-45 --run-id phase45-permission-evaluation --allow-external-embeddings`
  - This first run used the script default report path and was not committed.
- Passed: `python scripts/run_permission_eval.py --phase phase-45 --run-id phase45-permission-evaluation --run-name phase45-permission-evaluation --report-path docs/phase-45/permission-safety-results.md --detail-path data/evaluation/phase45-permission-evaluation.json --eval-run-path data/evaluation/eval-runs/phase45-permission-evaluation.json --allow-external-embeddings`
  - Permission leakage: `0.000`
  - Blocked-answer accuracy: `1.000`
  - Unauthorized chunk exposure: `0.000`
  - Restricted citation leakage: `0.000`
  - Unauthorized chunks reached generation: `0.000`
  - Authorized retrieval accuracy: `1.000`
  - Authorized answer accuracy: `pending`
- Passed: `python scripts/export_dashboard_data.py`

## Notes

- The live generalization suite is separate from benchmark version `1.1`; do not fold these scores into benchmark metrics.
- The baseline exposed 12 probe failures and is meant to drive Phase 46 remediation.
- The first permission run updated legacy Phase 8 default outputs; those accidental generated changes were reverted and replaced with Phase 45-specific report/detail/eval-run paths.
