# Evaluation Cadence And Sealed-Suite Custody

## Deterministic cadence

Run `python scripts/run_phase63_deterministic_checks.py --runtime-commit <commit>` on every candidate change. The report stores status, duration, and an output fingerprint—not raw prompts, answers, sources, or secrets. This repository provides the enforcement command; a hosted branch-protection/CI required check is not connected and must not be claimed.

## Budgeted semantic cadence

- Development: weekly only when runtime, prompts, models, corpus, or evaluators changed.
- Release candidate: once after runtime freeze and before promotion.
- Require the existing explicit external-AI approval flag, maximum `$0.75` total budget, one attempt per case, recorded provider/model/prompt configuration, and stop-on-budget behavior.
- Cover ambiguity, direct/indirect/multilingual/obfuscated injection, poisoned sources and memory, role/scope escalation, citation suppression, cost abuse, and legitimate security-question false positives.

## Custody rules

- Phase 47-49 and Phase 55 suites are protected by their existing seals. Phase 63 may verify raw-byte hashes but does not execute or display their cases.
- Development cases are visible and may be iterated; they never support a fresh generalization claim.
- A future release suite must be newly authored after candidate freeze by a separate author/custodian, checked for overlap without exposing cases to implementers, sealed, and executed once under a journaled protocol.
- Any interrupted run remains an interruption. Do not reconstruct, combine, or selectively rerun missing cases.
- Automated artifacts remain immutable. Human adjudication is separate and never rewrites the original score.
