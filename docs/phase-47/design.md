# Phase 47 Design

## Evaluation Boundary

Phase 47 keeps three evidence sets distinct: benchmark `1.1`, the Phase 45/46 probes, and the new independent-generalization suite. The new suite has a 70-case development split and a 30-case holdout. Runtime and corpus paths are frozen before holdout authoring; the holdout commit may change only evaluation data, evaluation tooling, reporting, and documentation.

The holdout preflight compares the checked-out evaluation commit to the recorded runtime freeze for changes under `apps/api/app` and `data/synthetic-documents`. It also requires a clean tree, except for the intentionally excluded `data/observability/request-logs.jsonl`, validates the complete holdout, and verifies `holdout-v1.sha256` before any request is sent.

## Artifacts

- `data/evaluation/independent-generalization/schema-v1.json` defines the Phase 47 case contract.
- `development-v1.json` and `holdout-v1.json` remain separate, versioned inputs.
- `scripts/validate_independent_generalization_suite.py` enforces locked distributions, identities, behaviors, source truth, quote truth, pair parity, review metadata, and coverage.
- `scripts/freeze_phase47_holdout.py` writes the hash only after holdout validation succeeds.
- `scripts/run_independent_generalization_eval.py` owns approval, budget, preflight, execution, scoring, provenance, fixture cleanup, and result generation.
- Raw rows, normalized eval runs, failure matrices, and Markdown reports are retained independently for each split.

## Scoring And Safety

Automated scoring compares response behavior, retrieved source IDs, atomic required facts, forbidden facts, citation document IDs, and claim/citation token support. These deterministic measures are diagnostics, not semantic proof. The hallucination flag is explicitly heuristic, and the holdout requires human adjudication without changing the original automated result.

Permission checks use access roles returned with retrieved chunks, not an expected-document allowlist. The runner records unauthorized chunk exposure, restricted citation leakage, and the API's pre-generation permission flag. Memory cases separately verify source recovery and prohibit prior turns from becoming source evidence.

## Fixture Isolation

The uploaded-document/project-isolation slice creates uniquely identified disposable projects, departments, memberships, files, documents, jobs, and chunks. Cleanup targets only those exact fixture IDs and contained fixture paths. Seeded documents and pre-existing uploads are never removed.

## Reporting

The Dev/Admin dashboard receives an `independent_evaluation` payload with development, holdout, stability, targets, and limitations. These runs may appear in the run inventory, but their metrics are not merged into benchmark scorecards. Input/output token counts remain unavailable from the `/query` response; endpoint-reported estimated cost is preserved instead.
