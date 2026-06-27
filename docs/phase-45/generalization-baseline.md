# Phase 45 Generalization Baseline

Status: live baseline not captured.

Phase 45 added the baseline runner and a 20-probe suite, but did not produce live metrics because OpenAI credentials are unavailable to the verification process.

## Dry-Run Summary

Command:

```powershell
python scripts/run_generalization_eval.py --dry-run
```

Result:

- Run ID: `phase45-generalization-baseline`
- Probe count: `20`
- External AI required: `true`
- Planned detail artifact: `data/evaluation/generalization-probes/phase45-generalization-baseline.json`
- Planned eval-run artifact: `data/evaluation/eval-runs/phase45-generalization-baseline.json`
- Planned report: `docs/phase-45/generalization-baseline.md`

## Probe Coverage

- Follow-up memory references such as `that policy`, `same department`, `what about contractors?`, and `which one applies to me?`
- Ambiguity probes for project, department, role, topic, and document references.
- Permission-sensitive memory probes where prior turns mention restricted topics but current-role retrieval must still enforce access.
- Multi-document and document-reference probes using normal user phrasing.

## Metrics Prepared

- Behavior accuracy.
- Memory rewrite quality.
- Clarification behavior.
- Answer/citation quality.
- Permission safety.
- Memory-as-evidence violation rate.
- Token and estimated cost totals when live responses are available.

## Live Baseline Blocker

Command attempted:

```powershell
python scripts/run_generalization_eval.py --allow-external-ai
```

Result:

```text
OPENAI_API_KEY or OPENAI_API_KEY_FILE is required for the live Phase 45 baseline.
```

No live OpenAI-backed generalization metrics are claimed in this phase state. The runner is ready to produce the baseline once credentials are available.
