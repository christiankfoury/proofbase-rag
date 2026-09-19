# Evaluator v9 result

Readiness **failed**: 19/24 exact development challenge judgments and 3/3 exact
reviewer probes. No expectation changed. Independent review confirms no false
passes but a pure access refusal is falsely failed, modality contradiction becomes
unresolved, and the reviewer still disputes several correctly unresolved factual
judgments even when this leaves the reduced label unchanged. See
[independent inspection](calibration-v9-agent-review.md).

All 75 calls, raw responses, requests, source snapshots and ledger are frozen.
Incremental estimated cost USD 0.124989; cumulative USD 1.66165692 of USD 5.
Remaining USD 3.33834308. Mixed-model costs replay with per-row pricing:
`python scripts/report_quality_calibration_v9.py`. Historical v7/v8 replay unchanged.

Next candidate uses a concise unified rubric and more reasoning effort. A new
separate-context confirmation suite is being authored without access to current
or previous prompts, answers or failure reports. It remains unexecuted.
Application remediation and runtime holdout remain gated. No accuracy or human
adjudication claim. Verification: six frozen replay tests pass.
