# Evaluator v8 calibration

Frozen development attempt `calibration-v8-01` matches 17/24 independently
authored challenge judgments and detects the required disputes in 3/3 planted
reviewer probes, but only 1/3 probes has the exact dispute set (three false
disputes across the other two). Readiness remains **failed**; this is not application accuracy.

Seven disagreements remain, including generic refusal incorrectly labeled an
access refusal, speech-act records violating their status contract, reviewer
confusion between attempted-answer form and the rubric's completeness-dependent
response-behavior dimension, and failure to distinguish not-found from access
denial. Expected judgments and source material were not changed.

All 75 calls, requests, responses, source snapshots and ledger are preserved.
Incremental estimated cost: USD 0.188102. Conservative cumulative spend:
USD 1.53666792 of the approved USD 5; remaining USD 3.46333208. No application,
embedding or new holdout calls occurred. No human adjudication is claimed.

Offline reproduction: `python scripts/report_quality_calibration_v8.py`.
The frozen v7 report continues to reproduce independently. See the
[independent agent inspection](calibration-v8-agent-review.md).

Next: separately versioned evaluator repair and a full conservative preflight.
Application remediation and untouched holdout remain gated on evaluator reliability.

Verification: 11 contract/replay tests passed, both frozen reports replay, and
`git diff --check` passed. Self-review found no runtime or historical-evidence
changes; grading defects above deliberately keep readiness false.
