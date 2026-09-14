# Phase 65 — replacement current-runtime evaluation

Status: preparing a new freeze and new suite after the [interrupted first execution](interrupted-v1-results.md). No full-suite score is available yet.

The replacement keeps the same version-4 semantic rubric and unchanged RAG behavior. Only the isolated test process's conservative daily admission allowance increases from $5 to $10, enough for 60 query admissions and two indexing reservations. The application default stays at $5. The cumulative external API ledger still enforces $0.75 across calibration, the interrupted run, preflights and this replacement.

A visible preflight completed PDF upload, approval/indexing and an authorized cited answer before the new freeze. The runner now persists fixture stages and rejects an unindexed fixture instead of allowing a vacuous isolation pass. All 23 local tests pass. The interrupted experiment remains immutable and independently verifiable with `python scripts/report_fresh_eval.py --archive --check`.

A new context-isolated author and validator must prepare 60 new cases after the corrected freeze. This is agent authorship/validation, not human review. The final result will retain all failures and a named-human review packet. It cannot be compared as an improvement over a different historical suite or the incomplete prior run.
