# Phase 38 Answer-Quality Remediation Results

Generated at: 2026-06-21T18:41:42.141510+00:00

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
- Estimated chat cost: `0.08536`

## Before / After

| Metric | Phase 35 Current | Phase 38 Candidate |
|---|---:|---:|
| answer_accuracy | `0.919` | `0.975` |
| citation_accuracy | `0.95` | `0.969` |
| faithfulness | `0.88` | `0.884` |
| hallucination_rate | `0.0` | `0.0` |
| response_type_accuracy | `0.881` | `0.923` |
| refusal_accuracy | `1.0` | `1.0` |
| not_found_accuracy | `1.0` | `1.0` |
| clarification_accuracy | `0.5` | `1.0` |
| failed_question_count | `16` | `6` |
| estimated_cost | `0.092994` | `0.08536` |

## Failure Buckets

| Failure type | Phase 35 Current | Phase 38 Candidate |
|---|---:|---:|
| ambiguity_failure | `5` | `0` |
| incomplete_answer | `2` | `1` |
| multi_document_failure | `3` | `3` |
| retrieval_miss | `1` | `0` |
| unsupported_answer | `2` | `0` |
| wrong_citation | `3` | `2` |

## Failed Questions

- Failed count: `6`
- Failed IDs: `MULTI-004, MULTI-005, MULTI-008, MULTI-013, MULTI-017, MULTI-020`

## Notes

- Benchmark expected answers, expected behavior, and expected sources were not changed.
- Permission filtering still happens before generation and before citation validation/backfill.
- Phase 39 still owns deeper multi-document orchestration and generalized ambiguity planning.
- Chat cost is estimated from configured model pricing and excludes embedding and infrastructure cost.
