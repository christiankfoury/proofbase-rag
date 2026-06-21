# Phase 36 Checklist

## Goal

Make permission and memory claims credible with larger suites, exact sample sizes, and a focused check that conversation memory cannot bypass role-based retrieval boundaries.

## Product Surface

- Dev/Admin permission safety now prefers the Phase 36 20-question permission run.
- Dev/Admin memory evaluation now prefers the Phase 36 20-question memory run.
- Dashboard exports include Phase 36 permission, memory, and memory-permission boundary runs.
- Dashboard benchmark context now reports exact current suite sizes from the benchmark corpus.

## Engineering Changes

- Expanded the memory evaluator into a reusable Phase 36 runner with run IDs, JSON detail output, dashboard eval-run output, dry-run support, prompt version selection, and OpenAI budget guards.
- Expanded the permission evaluator with Phase 36 outputs, dry-run support, dashboard eval-run output, and exact suite metadata.
- Added a focused memory-permission boundary runner covering five follow-up probes where previous conversation context refers to restricted documents.
- Added deterministic memory topic extraction, follow-up detection, and query rewrite rules for the expanded memory benchmark cases.
- Kept memory as query context only; retrieved documents remain the source of truth and are still permission-filtered before generation.

## Acceptance Criteria

| Requirement | Status | Evidence |
| --- | --- | --- |
| Permission tests contain 20-30 questions | Complete | `phase36-permission-evaluation` ran 20 restricted questions. |
| Memory tests contain 20-30 questions | Complete | `phase36-memory-evaluation` ran 20 memory questions. |
| Permission leakage rate is 0.000 | Complete | Permission run reported `permission_leakage_rate = 0.000`. |
| Memory answer accuracy is at least 0.90 | Complete | Memory run reported `memory_answer_accuracy = 1.000`. |
| Memory never bypasses permissions | Complete | Memory boundary run reported `memory_permission_leakage = 0.000` across 5 probes. |
| Expanded suites appear with exact sample size | Complete | Dashboard eval-run artifacts include sample sizes for all three Phase 36 runs. |
| Failures are visible in Dev/Admin | Complete | Phase 36 failed counts are exported through dashboard data; both main Phase 36 suites reported 0 failed questions. |

## Known Limitations

- Permission authorized answer accuracy remains `pending` by default to avoid extra chat-completion cost. The Phase 36 permission run validates unauthorized blocking and authorized retrieval access.
- The memory-permission boundary suite is intentionally small and focused. It complements, rather than replaces, the main 20-question memory and 20-question permission suites.
- These runs use the synthetic portfolio corpus and demo roles; they do not claim production auth or real enterprise connectors.
