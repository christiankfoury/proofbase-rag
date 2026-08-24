# Phase 49 Fresh Holdout Human Adjudication

## Review Record

- Run: `phase49-independent-holdout-v3`.
- Reviewed at: `2026-08-24T00:43:44Z`.
- Automated result: `22/30`; this remains immutable and official.
- Coverage: all `8/8` automated failures and the lexicographically first `3/22` automated passes (`13.6%` of passes).
- Method: manual comparison of persisted answers, citations, retrieval evidence, scores, sealed expectations, and exact corpus quotes. No model judge, OpenAI call, case rerun, runtime change, or result rewrite was used.

## Failure Adjudication

| Case | Classification | Human finding |
| --- | --- | --- |
| `P49-H3-006` | Product | The answer incorrectly treats USD 8,000 as above USD 10,000 and omits most vendor-intake fields. Both expected sources were retrieved, but the Finance threshold was applied incorrectly. The heuristic hallucination flag missed this contradiction. |
| `P49-H3-007` | Product | Discovery and generic-BI positioning are correct, but `SALES-002` is absent and the response omits the specific bans on unsupported integrations, exact roadmap dates, and customer-specific contract commitments. |
| `P49-H3-008` | Evaluator-only | The answer correctly says vacation starts after 30 days and covers onboarding. The forbidden matcher falsely matches the opposite first-day statement. |
| `P49-H3-009` | Evaluator-only | The answer correctly requires peer/IT Admin review and Engineering Manager approval, a specific rollback plan, and the admin safeguards. The matcher falsely flags IT Admin-only approval. |
| `P49-H3-013` | Mixed | The required same-country review and manager considerations are correct but lexically under-credited. The answer also speculates that a within-Canada change will likely receive cross-border tax/employment/security review, which its cited cross-border passage does not establish. |
| `P49-H3-021` | Evaluator-only | The answer exactly states monthly production review and quarterly business-application review. The matcher loses subject association and falsely flags quarterly production review. |
| `P49-H3-027` | Product | Safe but behavior-incorrect: no restricted evidence leaks, but `not_found` is returned instead of the expected `refuse_no_access`. |
| `P49-H3-029` | Evaluator-only | The response correctly states USD 1,000, pre-communication Manager approval, and obsolete USD 2,500 guidance. Negation and ordering trigger false forbidden matches. |

Counts: `4` evaluator-only, `3` product, `1` mixed, and `0` benchmark defects.

## Pass Sample

| Case | Human finding |
| --- | --- |
| `P49-H3-001` | Correct answer and required `HR-004` support. An extra verified-backfill `HR-002` vacation citation is irrelevant, so citation review is partial despite a substantively correct pass. |
| `P49-H3-002` | Confirmed correct answer, behavior, and `IT-002` citation. |
| `P49-H3-003` | Confirmed correct answer, behavior, and `SALES-002` citation. |

## Interpretation

All four automated hallucination flags are evaluator false positives, but that does not justify a zero-hallucination claim: `P49-H3-006` contains an unflagged factual threshold error. The automated `0.133` heuristic rate remains official because post-run adjudication does not rewrite the evaluator. No human-adjusted pass rate is published.

The future Phase 49 product backlog is `P49-H3-006`, `P49-H3-007`, `P49-H3-013`, and `P49-H3-027`. No remediation belongs in Phase 49. The official `22/30` misses the `27/30` target, so Phase 49 provides valid fresh evidence but no improvement claim.
