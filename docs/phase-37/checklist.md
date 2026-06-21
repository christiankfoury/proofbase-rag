# Phase 37 Checklist

## Goal

Publish the final baseline-vs-current portfolio story with measured run IDs, metric deltas, exact sample sizes, benchmark version, category breakdown, failed questions, failure reasons, supported claims, and limitations.

## Product Surface

- Dev/Admin overview now renders a dedicated Regression Scorecard section.
- The scorecard shows baseline and current values, run IDs, sample sizes, benchmark versions, metric deltas, targets, and pass/fail status.
- The scorecard shows supported portfolio claims and current failure reason counts beside the metric table.
- Existing Benchmark And Suites and Failed Questions surfaces remain visible for deeper inspection.

## Data Artifacts

- `data/evaluation/regression-scorecard.json`
- `data/evaluation/dashboard-summary.json`
- `docs/phase-37/regression-scorecard.md`

## Acceptance Criteria

| Requirement | Status | Evidence |
| --- | --- | --- |
| Dashboard shows baseline run | Complete | Scorecard rows include baseline run IDs. |
| Dashboard shows latest run | Complete | Scorecard rows include current run IDs. |
| Dashboard shows metric deltas | Complete | Scorecard rows include numeric deltas. |
| Dashboard shows benchmark version | Complete | Scorecard rows include benchmark version per run and benchmark v1.1 summary context. |
| Dashboard shows sample sizes | Complete | Scorecard rows include `n=` for baseline and current runs. |
| Dashboard shows category breakdown | Complete | Benchmark And Suites panel shows benchmark category counts; scorecard JSON includes the same breakdown. |
| Dashboard shows failed questions | Complete | Current failure count and failed-question IDs are exported; Failed Questions remains linked in Dev/Admin. |
| Dashboard shows failure reasons | Complete | Scorecard displays failure reason counts for the current answer run. |
| Claims point to supporting run IDs | Complete | Scorecard uses Phase 32, 33, 35, and 36 measured run IDs. |

## Known Limitations

- Phase 37 does not run new OpenAI-backed evaluations. It publishes a scorecard over already measured Phase 32-36 runs.
- Source recall is at the Phase 33 gate of `0.950`, while Precision@k improved from `0.616` to `0.778`.
- Permission and memory comparisons include coverage expansion from smaller legacy suites to larger Phase 36 suites.
- The current answer run still has 16 failed questions.
