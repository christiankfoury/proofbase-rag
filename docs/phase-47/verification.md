# Phase 47 Verification

Status: development and runtime-freeze verification in progress. Holdout verification will be appended after the independent dataset is committed and run once.

## Local Checks

- Passed: `python scripts/test_phase47_independent_generalization.py`
- Passed: `python scripts/validate_independent_generalization_suite.py --split development`
- Passed: `python scripts/run_independent_generalization_eval.py --split development --dry-run`
- Passed: `python scripts/export_dashboard_data.py`
- Passed: `python scripts/validate_independent_generalization_suite.py --split development --json`
- Passed: `python scripts/validate_benchmark.py`
- Passed: `python -m compileall apps/api/app scripts`
- Passed with the known local Docker credential warning: `docker compose config --quiet`
- Passed after sandbox escalation was required for Node to resolve the user-profile path: `cd apps/web; $env:NEXT_DIST_DIR='.next-codex-build'; $env:NEXT_TELEMETRY_DISABLED='1'; npm run build`
- Passed: final development suite SHA-256 matches the live raw-result provenance.
- Passed: `git diff --check` before staging.
- Pending immediately before commit: explicit staging audit and commit review.

## Approved Development Checks

- Development run `phase47-independent-development`: 70 cases, 64 passed, 6 retained failures, behavior accuracy `0.986`, expected-source recall `1.000`, required-fact completeness `0.881`, citation document accuracy `0.979`, heuristic hallucination rate `0.000`, estimated cost `$0.053961`.
- Hard gates: permission leakage `0.000`, unauthorized chunks reaching generation `0.000`, and memory-as-evidence violations `0.000`.
- Stability diagnostic: 20 cases × 3 passes, pass consistency `1.000`, response-type consistency `1.000`, source consistency `0.900`, citation consistency `0.900`, estimated cost `$0.051048`.
- Benchmark `1.1` regression `phase39-live-query-answer-quality-v8`: 130/130 passed, answer accuracy `1.000`, citation accuracy `1.000`, hallucination rate `0.000`, estimated cost `$0.078338`.
- Permission regression `phase47-permission-evaluation`: 20 restricted and 20 authorized retrieval checks; leakage, restricted citations, unauthorized exposure, and unauthorized generation all `0.000`; blocked-answer and authorized-retrieval accuracy both `1.000`.

## Corrections Before Freeze

- The permission evaluator's default historical report path was used once during diagnostics; the Phase 33 file was restored byte-for-byte and the final Phase 47 run used explicit Phase 47 output paths.
- A reporting-only zero-value bug initially marked a `0.000` hallucination rate as failing its `<=0.050` gate. The gate expression and generated gate flag were corrected without changing case responses or metric values.
- The final development run was repeated after stability metadata was locked so its recorded suite hash matches the final development dataset. No holdout existed or was inspected during these corrections.

## External-Call Notes

The approved key was reused without printing or persisting it. Platform telemetry was disabled for the evaluation commands because the optional local telemetry receiver was unavailable. OpenAI answer and embedding calls remained enabled. The `/query` payload exposes estimated cost but not token counts, so Phase 47 artifacts record token totals as unavailable/zero rather than inventing them.

## Runtime Freeze And Holdout Authoring

- Frozen runtime commit: `50e149c771d02a4d4b3942de904e8d396a8818dc`, reviewed and pushed to `origin/main` before holdout authoring.
- The author changed only `holdout-v1.json`, did not call OpenAI, and did not inspect Phase 47 result artifacts.
- An isolated reviewer corrected dataset/source-truth defects only, then approved all 30 cases as `isolated-phase47-holdout-reviewer` at `2026-08-23T18:45:21Z`.
- Passed: `python scripts/validate_independent_generalization_suite.py --split holdout`
- Passed: `python scripts/validate_independent_generalization_suite.py --split holdout --json`
- Passed: `python scripts/run_independent_generalization_eval.py --split holdout --dry-run`
- Passed: `python scripts/freeze_phase47_holdout.py`
- Holdout SHA-256: `10d93cfb229813499721a973ceadabd9045c47b2e5eee29e4dca0ee01b1afb4f`.
- Passed: no changes under `apps/api/app` or `data/synthetic-documents` relative to the frozen runtime commit.
- Pending: clean evaluation-only commit, one-time live holdout execution, human adjudication, dashboard export, and final verification.
