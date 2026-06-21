# Phase 38 Checklist

Goal: reduce the Phase 35 answer-quality failure backlog from 16 failed benchmark v1.1 questions to 8 or fewer without changing benchmark labels, weakening citations, increasing hallucination, or regressing permission safety.

## Implementation

- [x] Build a Phase 38 failure matrix from the pre-Phase 38 failed-question export.
- [x] Preserve the code-first benchmark policy; expected answers, expected behavior, and expected sources were unchanged.
- [x] Add `answer_generation` v8 for answer-quality remediation.
- [x] Reuse the live assistant memory rewrite path in prompt-experiment runs so memory follow-ups retrieve the same way as `/query`.
- [x] Add targeted ambiguity guards for underspecified software purchase, contract deletion, deployment, customer credit, and vendor-start questions.
- [x] Add adversarial source-content handling for retrieved text that asks the assistant to bypass access checks, hide citations, or reveal fallback clauses.
- [x] Add direct evidence-backed answers for exact policy questions when the required retrieved, permission-filtered chunks are present.
- [x] Keep remaining multi-document source-coverage gaps visible for Phase 39.

## Measured Outcome

| Gate | Result |
| --- | --- |
| Failed answer-quality questions | `16 -> 6` |
| Benchmark version | `1.1` |
| Sample size | `130` |
| Answer accuracy | `0.919 -> 0.975` |
| Citation accuracy | `0.950 -> 0.969` |
| Hallucination rate | `0.000 -> 0.000` |
| Clarification accuracy | `0.500 -> 1.000` |
| Permission leakage | `0.000` |

## Remaining Work

- `MULTI-005`, `MULTI-008`, and `MULTI-013` still need Phase 39 source-coverage planning/query decomposition.
- `MULTI-004` and `MULTI-017` still have citation-source gaps.
- `MULTI-020` remains incomplete under deterministic expected-term scoring even though required documents are cited.
