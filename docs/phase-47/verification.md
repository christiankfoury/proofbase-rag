# Phase 47 Verification

Status: the development, runtime freeze, one-time holdout, and adjudication evidence are complete. Final repository checks and commit review are recorded below.

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
- The runtime-freeze commit's explicit staging audit and post-commit review passed.

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
- Passed: clean evaluation-only holdout commit `d1ec135`, preflight-fix commit `58ed3fc`, one-time live holdout execution, human adjudication, and dashboard export.

The first live command attempt stopped in local preflight before creating the API test client or sending any OpenAI request. `git_output().strip()` removed the status column's leading space and made the ignored request-log path appear as `ata/observability/request-logs.jsonl`. The evaluation-only parser was changed to preserve leading porcelain columns, and a regression check now exercises the exact ignored-path condition. Because no case ran and no usable or partial result was produced, that attempt did not consume the one-time execution recorded below.

## One-Time Holdout

- Run ID: `phase47-independent-holdout`
- Evaluation commit: `58ed3fc68966b1fd93afc7105afcbf618bbd4aa5`
- Frozen runtime commit: `50e149c771d02a4d4b3942de904e8d396a8818dc`
- Preflight: clean after ignoring only `data/observability/request-logs.jsonl`; suite hash matched; protected runtime/corpus changes empty.
- Sample: 30 complete cases; partial execution flags were not used.
- Result: 14 passed, 16 failed; behavior `0.767`, source recall `0.947`, fact completeness `0.788`, citation accuracy `0.842`, heuristic hallucination `0.333`.
- Hard gates: unauthorized exposure `0.000`, restricted citation leakage `0.000`, unauthorized chunks reached generation `0.000`, memory-as-evidence violations `0.000`.
- Estimated OpenAI cost: `$0.032695`, within the `$2` command budget.
- The holdout was not rerun for quality outcomes and no runtime or expectation change followed it.

## Human Review

- Reviewed all 16 automated failures and 4 of 14 passes across four categories and roles.
- Classified 5 evaluator-only, 6 mixed product/evaluator, and 5 primarily product-gap failures.
- Confirmed no benchmark defect and no hard safety failure.
- Preserved the automated artifact and scores unchanged.

## Cost Scope

The retained development (`$0.053961`), stability (`$0.051048`), benchmark regression (`$0.078338`), and holdout (`$0.032695`) chat estimates total `$0.216042`. This is not a complete billing ledger for discarded development diagnostics, and the focused permission run's embedding usage remains unpriced.

## Final Repository Checks

- Passed: `python scripts/test_phase47_independent_generalization.py`
- Passed: `python scripts/validate_independent_generalization_suite.py --split all` (`100` cases, no errors or warnings)
- Passed: `python scripts/validate_independent_generalization_suite.py --split all --json`
- Passed: development and holdout dry-runs.
- Passed: `python scripts/validate_benchmark.py` (benchmark `1.1`, `130` cases)
- Passed: `python -m compileall apps/api/app scripts`
- Passed with the known Docker credential warning: `docker compose config --quiet`
- Passed: `python scripts/export_dashboard_data.py`; dashboard retains benchmark `1.1` scorecard provenance and exposes development/holdout under separate `independent_evaluation` fields.
- Passed: `cd apps/web; $env:NEXT_TELEMETRY_DISABLED='1'; npm run build`
- Passed: `git diff --check`
- Passed: no protected runtime or corpus change between frozen runtime `50e149c` and the holdout evaluation commits.
