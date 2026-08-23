# Phase 47 Checklist

Goal: produce independently authored, frozen generalization evidence without tuning the runtime against the holdout.

## Development And Freeze

- [x] Add a versioned Phase 47 schema and a validator with human-readable and JSON output.
- [x] Author and validate the 70-case development split with the locked category distribution.
- [x] Add the reusable development/holdout runner, approval and budget gates, provenance, raw results, normalized eval runs, failure matrices, and Markdown reports.
- [x] Add disposable upload/project-isolation fixtures with exact cleanup.
- [x] Run the 70-case development evaluation and retain all failures.
- [x] Run the three-pass, 20-case stability slice.
- [x] Run the 130-question answer-quality and focused permission regressions.
- [x] Add separate Dev/Admin independent-evaluation reporting.
- [ ] Commit and record the frozen runtime configuration.

## Independent Holdout

- [ ] Author the 30-case holdout only after the runtime freeze.
- [ ] Validate source truth and review metadata with an isolated reviewer.
- [ ] Freeze and commit the approved holdout SHA-256 without protected runtime or corpus changes.
- [ ] Run the complete holdout exactly once from a clean evaluation commit.
- [ ] Human-review every automated failure and at least 10% of automated passes.

## Reporting And Handoff

- [ ] Export development and holdout evidence separately to the dashboard.
- [ ] Publish holdout results, adjudication, verification, bounded README/demo claims, and algorithm-review updates.
- [ ] Complete commit review, code review, push, and final clean-status confirmation while excluding the request log.

## Non-Goals

- Runtime tuning against holdout questions or failures.
- Changes to benchmark `1.1` expectations or Phase 45/46 probes.
- Blending holdout scores into the historical regression scorecard.
- Treating conversation memory as evidence.
