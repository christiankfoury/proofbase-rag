# Phase 48 Checklist

## Remediation freeze

- [x] Classify all 16 historical failures by root cause.
- [x] Add general evaluator semantics and local regression tests.
- [x] Add intent-slot clarification, correction-aware memory, source coverage, and generic restricted-intent remediation.
- [x] Run the complete 70-case development suite.
- [x] Run benchmark 1.1, permission, memory, and local regression checks.
- [x] Record hashes and commit/review/push the runtime/evaluator freeze (`7bbb8b4`).

## Fresh holdout

- [x] Author 30 new cases in isolation after the freeze.
- [x] Independently validate source truth, permissions, ambiguity labels, novelty, and schema.
- [x] Hash and commit the approved holdout before execution (`d134ce3`).
- [x] Verify the clean-tree/protected-path preflight.
- [x] Execute every case exactly once within the approved budget. Cases 1-29 ran in the sealed process; the untouched fixture ran once in bounded recovery after the harness interruption.
- [x] Adjudicate every failure and a fixed pass sample, with indeterminate labels where answer payloads were not retained.
- [x] Publish the observed `19/30` result and unavailable aggregate metrics without altering the Phase 47 evidence.
- [ ] Commit, review, push, and close the progress tracker.
