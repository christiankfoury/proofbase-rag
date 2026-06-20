# Phase 28 Dashboard Transparency

## Purpose

Phase 28 makes the existing evaluation dashboard more defensible. The goal is not to improve scores; it is to show what each score actually measured.

The dashboard now distinguishes:

- the 65-question benchmark source corpus
- 60-question primary retrieval and answer-quality dashboard runs
- the 10-question permission safety run
- the 5-question memory follow-up run
- subset prompt experiments that are not directly comparable to full primary runs

## Data Model

`scripts/export_dashboard_data.py` now exports `benchmark_context`:

- `benchmark_version`
- `source_corpus`
- `corpus_question_count`
- `category_breakdown`
- `current_dashboard_suites`

Each exported run now includes:

- `sample_size`
- `passed_count`
- `failed_count`
- `benchmark_version`
- `run_timestamp`
- `category_breakdown` when the run artifact contains per-question rows or the suite category is explicit

The overview also includes `metric_context`, mapping each headline metric to the exact source run and measurement context.

## UI Changes

The Dev/Admin overview now shows:

- context on every headline metric card
- a metric context table with run IDs, sample sizes, pass/fail counts, benchmark version, and timestamps
- source corpus category breakdown
- current answer-run category breakdown

The run comparison table now shows:

- run ID
- timestamp
- sample size
- passed count
- failed count

## Documentation Changes

Updated:

- `README.md`
- `docs/demo/interactive-demo-guide.md`
- `docs/demo/resume-bullets.md`
- `docs/demo/portfolio-case-study.md`
- `docs/demo/architecture-diagram.md`

The copy now states that the source corpus has 65 questions and that current dashboard metrics come from differently sized suites.

## Limitations

- Historical summary-only retrieval and answer-quality runs do not expose full category breakdown because their committed artifacts do not include per-question JSON rows.
- `passed_count` and `failed_count` are derived from each run's existing failed-question list or failed-count metric. They are transparency counters, not a new scoring rubric.
- Existing headline answer-quality values still point to the Phase 7 dashboard baseline; this phase intentionally did not promote newer prompt-experiment metrics into the headline cards.
- No Phase 29 benchmark validator was run or created during this phase.
