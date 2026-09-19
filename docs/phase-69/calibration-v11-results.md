# Evaluator v11 result

Readiness **failed**: 20/24 exact development challenges and 3/3 exact reviewer
probes. Independent review finds no false overall pass/fail, but two expected
failures become unresolved. Remaining causes are context-free claim resolution,
a reviewer confusing missing cited support with its failure label, reconstructed
nonverbatim claim spans, and reviewer confusion over derived response behavior.
See [independent review](calibration-v11-agent-review.md), which also checks
forbidden-assertion judgments outside the eight-label comparison.

All 75 calls, source snapshots and ledger are frozen. Incremental estimated cost
USD 0.238710; cumulative USD 2.13692667 of approved USD 5. Remaining USD 2.86307333.
Replay: `python scripts/report_quality_calibration_v11.py`. Earlier calibration
reports remain unchanged. No application or confirmation calls occurred.

V12 is prepared with context-only reference resolution, exact span instructions
and the full GPT-5.4 model. Its conservative bound exceeds remaining headroom.
The requested USD 10 cumulative ceiling is pending; code/ledger still enforce
USD 5. See [prepared v12](evaluator-v12.md). No new validated application score.
