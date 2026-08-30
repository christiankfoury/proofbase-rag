# Phase 28 Checklist

Goal: make Dev/Admin evaluation metrics transparent enough for product and technical review without changing retrieval, prompt, or scoring behavior.

## Implemented

- Added benchmark context to the dashboard export:
  - benchmark version
  - source corpus path
  - 65-question source corpus size
  - corpus category breakdown
  - current 60/10/5 dashboard suite sizes
- Added per-run dashboard metadata:
  - `sample_size`
  - `passed_count`
  - `failed_count`
  - `benchmark_version`
  - `run_timestamp`
  - `category_breakdown` where run rows or suite definitions make it available
- Exposed benchmark context through Dev/Admin evaluation API responses.
- Added metric-source context to the Dev/Admin overview headline cards.
- Added a Dev/Admin metric-context table with run IDs, sample sizes, pass/fail counts, benchmark version, and timestamps.
- Added corpus and current-answer-run category breakdowns to the Dev/Admin overview.
- Expanded the run comparison table with run ID, timestamp, sample, passed, and failed columns.
- Updated README and demo copy so metrics no longer imply one common 60-question sample.

## Not Implemented

- No benchmark schema validation script; Phase 29 owns `scripts/validate_benchmark.py`.
- No retrieval, prompting, scoring, or benchmark content changes.
- No new metric improvements or target claims.
- No new OpenAI-backed evaluation run.

## Technical Review Note

Use `/dev-admin` to show that each headline number cites its source run and sample size. Use `/dev-admin/runs` to show detailed run provenance and subset warnings before discussing score quality.
