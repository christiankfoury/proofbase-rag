# Phase 48 Checklist

## Remediation freeze

- [x] Classify all 16 historical failures by root cause.
- [x] Add general evaluator semantics and local regression tests.
- [x] Add intent-slot clarification, correction-aware memory, source coverage, and generic restricted-intent remediation.
- [x] Run the complete 70-case development suite.
- [x] Run benchmark 1.1, permission, memory, and local regression checks.
- [ ] Record hashes and commit/review/push the runtime/evaluator freeze. Hashes are recorded; commit/review/push pending.

## Fresh holdout

- [ ] Author 30 new cases in isolation after the freeze.
- [ ] Independently validate source truth, permissions, ambiguity labels, novelty, and schema.
- [ ] Hash and commit the approved holdout before execution.
- [ ] Verify the clean-tree/protected-path preflight.
- [ ] Execute all 30 cases exactly once within the approved budget.
- [ ] Adjudicate every failure and a fixed pass sample.
- [ ] Publish results without altering the Phase 47 evidence.
- [ ] Commit, review, push, and close the progress tracker.
