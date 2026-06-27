# Phase 45 Checklist

Goal: establish a generalization probe suite for memory and ambiguity behavior outside benchmark v1.1.

## Scope

- [x] Add `scripts/run_generalization_eval.py`.
- [x] Define 20 realistic probes covering follow-ups, ambiguous references, role applicability, document references, permission-sensitive memory, and multi-document phrasing.
- [x] Keep the first runner as a baseline harness with no prompt, retrieval, chunking, or benchmark expectation changes.
- [x] Add dry-run output that lists probe count, categories, output artifacts, and external AI requirement.
- [x] Add approval gating for live OpenAI-backed execution.
- [x] Separate metrics for behavior, memory rewrite quality, clarification behavior, answer/citation quality, permission safety, and memory-as-evidence violations.
- [x] Prepare JSON, eval-run, and Markdown report outputs for live baseline execution.

## Blocked Baseline

- [ ] Live baseline captured.
- [ ] `data/evaluation/generalization-probes/phase45-generalization-baseline.json` written.
- [ ] `data/evaluation/eval-runs/phase45-generalization-baseline.json` written.
- [ ] Live result metrics summarized in `docs/phase-45/generalization-baseline.md`.

The live baseline is blocked because the local verification process does not have `OPENAI_API_KEY` or `OPENAI_API_KEY_FILE`.

## Out Of Scope

- Fixing generalization failures before the baseline is captured.
- Folding probe results into benchmark v1.1.
- Changing benchmark expectations.
