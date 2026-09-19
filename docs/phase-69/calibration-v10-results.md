# Evaluator v10 result

Readiness **failed**: 17/24 exact development challenges and 3/3 exact reviewer
probes. The factual-only rubric over-excluded imperative policy statements.
Additional defects include generic second-person paraphrase treated as uncertain,
wrong-topic answer form, and mixed-request relevance. No expectation was changed.
See [independent source inspection](calibration-v10-agent-review.md).

All 75 calls, source snapshots and ledger are frozen. Incremental estimated
cost USD 0.23655975; cumulative USD 1.89821667 of USD 5, remaining USD 3.10178333.
Offline replay: `python scripts/report_quality_calibration_v10.py`. V7-v9 replay
unchanged. No application calls, holdout execution or human adjudication.

The 16-case separate-context confirmation was independently approved and remains
unexecuted. It cannot proceed while development calibration has disagreements.
Next version clarifies normative policy claims, generic policy paraphrases, partial
responsive coverage and mixed-request relevance. Original rubric stays fixed.

Verification: 70 historical regression tests, saved current/fresh/reanalysis
reports and benchmark validation pass unchanged. Seven calibration replay tests
pass, preserving failed status and exact costs.
