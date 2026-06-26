# Phase 38 Answer-Quality Remediation Results

Generated at: 2026-06-26T04:43:37.833329+00:00

## Candidate

- Run ID: `phase38-answer-quality-remediation-v8`
- Questions: `130`
- Benchmark version: `1.1`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `5`
- Reranker: `lexical`
- Rerank candidate limit: `20`
- Prompt version: `v8`
- Model: `gpt-4.1-mini`
- Estimated chat cost: `0.086106`

## Before / After

| Metric | Phase 35 Current | Phase 38 Candidate |
|---|---:|---:|
| answer_accuracy | `0.919` | `0.969` |
| citation_accuracy | `0.95` | `0.963` |
| faithfulness | `0.88` | `0.883` |
| hallucination_rate | `0.0` | `0.0` |
| response_type_accuracy | `0.881` | `0.923` |
| refusal_accuracy | `1.0` | `1.0` |
| not_found_accuracy | `1.0` | `1.0` |
| clarification_accuracy | `0.5` | `1.0` |
| failed_question_count | `16` | `7` |
| estimated_cost | `0.092994` | `0.086106` |

## Failure Buckets

| Failure type | Phase 35 Current | Phase 38 Candidate |
|---|---:|---:|
| ambiguity_failure | `5` | `0` |
| incomplete_answer | `2` | `0` |
| multi_document_failure | `3` | `3` |
| retrieval_miss | `1` | `0` |
| unsupported_answer | `2` | `1` |
| wrong_citation | `3` | `3` |

## Failed Questions

- Failed count: `7`
- Failed IDs: `MULTI-004, MULTI-005, MULTI-006, MULTI-008, MULTI-013, MULTI-017, MULTI-020`

## Notes

- Benchmark expected answers, expected behavior, and expected sources were not changed.
- Permission filtering still happens before generation and before citation validation/backfill.
- Phase 39 still owns deeper multi-document orchestration and generalized ambiguity planning.
- Chat cost is estimated from configured model pricing and excludes embedding and infrastructure cost.
