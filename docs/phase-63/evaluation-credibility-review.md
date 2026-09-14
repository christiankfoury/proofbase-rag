# Evaluation credibility follow-up — 2026-09-14

## Goal and scope

Address the portfolio review objection that perfect answer/citation scores are unconvincing without inspectable methodology. This is a focused reporting and reproducibility improvement after Phase 63, not a new runtime-remediation or production-integration phase.

The user confirmed that the project author authored and checked benchmark answers with AI assistance. Public docs now disclose this and distinguish isolated holdout authoring/validator roles from independent human assessment. No new external-review claim is made.

## Changes

- Added `docs/evaluation/` as the reviewer entry point: dataset card, implemented scoring formulas, null exclusions, failure taxonomy, review provenance, reproduction commands, and bounded portfolio wording.
- Replaced broad README/dashboard accuracy labels with expected-answer overlap, expected-document citation, and heuristic flag language. Highlighted the historical 22/30 automated holdout result and its missed gate.
- Corrected the denominator: Phase 50's answer and citation scores each cover 80 answerable cases out of 130; the run retains 26 diagnostic notes. Phase 49 citation score covers 19 answer-expected cases.
- Added a navigable Dev/Admin methodology page with report-derived historical results, category failures, source links, and an offline check command.
- Added a standard-library evidence reporter and CI drift check. It rescores saved regression answers/citations, reproduces score means and exclusions, checks permission-case coverage, and validates all 30 durable holdout records against their journal and final manifest. It aggregates stored holdout scores without executing cases or conducting new semantic review.
- Added seven offline tests covering exclusions/partial credit, missing/duplicate rows, altered answers/citations/summaries, corrupted records, and journal tampering.
- Marked the Phase 3 rubric as historical design intent and linked current methodology from algorithm/case-study docs. Repaired the tracker's stale last-completed-phase description to match Phase 63 evidence.

Backend/data impact: no runtime, retrieval, generation, permission, database-model, benchmark expectation, or sealed-suite changes. New `public-evidence.json` is a reporting artifact derived from committed historical results; original artifacts are unchanged.

## Verification

- `python -S scripts/build_evaluation_evidence.py --check`: passed with site packages disabled; no account, credentials, database, or external API needed.
- `python -m unittest scripts.test_evaluation_evidence`: 7/7 passed.
- `python scripts/validate_benchmark.py`: benchmark v1.1, 130 cases, valid source references and category counts.
- `python -m compileall -q apps scripts` with isolated bytecode cache: passed.
- Next.js production build using isolated `.next-evaluation-review`: passed, including TypeScript and static `/dev-admin/evaluation` generation. Initial sandbox attempt could not access the installed Node runtime; the elevated retry passed. Next's automatic configuration edits were restored afterward.
- Temporary production server: `/dev-admin/evaluation` returned HTTP 200 with the 73.3% historical rate, AI-assisted authorship disclosure, and offline command rendered. The temporary server was stopped.
- Local Markdown target checks and `git diff --check`: passed.
- `docker compose config --quiet`: passed; Docker printed a local config-file access warning. The web Dockerfile now explicitly copies the report required at build time. Container image rebuild was not run; host production build verified the changed frontend.
- `python scripts/scan_phase60_secrets.py`: passed, zero findings.
- OpenAI-backed evaluations, new holdout execution, and cloud provisioning: not run; no algorithm change or new performance claim. External model cost for this task: none.

## Review and remaining limitations

Review focuses on denominator drift, overstated independence, hash/row integrity, unrelated changes, and deployable report imports. The offline report cannot establish semantic correctness or independent authenticity. Regression history uses different prompts/retrieval/request paths, and holdouts use different suites. None is a fresh measurement of today's runtime. Benchmark labels and automated outcomes remain immutable within this task.

The pre-existing local change to `data/observability/request-logs.jsonl` is unrelated and must remain outside the commit. Production promotion stays at the existing external-integration and human-validation gate; there is no further approved phase in this task's queue.
