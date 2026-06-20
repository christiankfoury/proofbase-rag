# Benchmark Expansion

Phase 31 expands the benchmark from 65 to 130 questions and bumps the benchmark version from `1.0` to `1.1`.

The expanded corpus uses the Phase 30 enterprise documents for finance, legal, engineering, support, and operations coverage. It also adds new categories for prompt-injection and conflicting-source scenarios so later baseline runs can measure harder enterprise RAG behavior.

## Category Counts

| Category | Phase 30 | Phase 31 |
| --- | ---: | ---: |
| Simple factual | 20 | 30 |
| Multi-document | 10 | 20 |
| Permission-restricted | 10 | 20 |
| Missing-information | 10 | 20 |
| Conversation-memory | 10 | 20 |
| Ambiguous | 5 | 10 |
| Prompt-injection / adversarial | 0 | 5 |
| Conflicting-source / versioned policy | 0 | 5 |
| Total | 65 | 130 |

## Added Coverage

- Finance expense timing, receipts, procurement thresholds, and old-vs-new spend guidance.
- Legal NDA, contract approval, retention, legal hold, do-not-reveal, and version precedence cases.
- Engineering deployment windows, on-call severity, API standards, change freeze, and adversarial source text.
- Support SLA, escalation, refund guardrails, obsolete threshold, and customer-pressure cases.
- Operations vendor onboarding, travel booking, equipment return, and overlapping-policy cases.

## Dashboard Impact

`scripts/export_dashboard_data.py` now keeps the current source corpus context separate from legacy run artifacts:

- Current benchmark context: version `1.1`, 130 questions.
- Legacy primary retrieval and answer-quality runs: benchmark version `1.0`, 60-question suites.
- Legacy permission safety run: benchmark version `1.0`, 10 restricted-access questions.
- Legacy memory run: benchmark version `1.0`, 5 follow-up questions.

No metric score changed in Phase 31. The dashboard data was regenerated only to show the active source corpus size, category breakdown, and correct run-version context.

## Review Note

The expanded questions are source-grounded and were added directly to the benchmark with expected source documents, expected behavior, allowed-document lists, and validation coverage. No AI-backed question-generation workflow or automatic promotion pipeline was run.
