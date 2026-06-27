# Phase 39 Live Query Answer-Quality Results

Generated at: 2026-06-27T00:24:11.185842+00:00

## Candidate

- Run ID: `phase39-live-query-answer-quality-v8`
- Questions: `130`
- Benchmark version: `1.1`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `5`
- Prompt version: `v8`
- Multi-doc mode: `auto`
- Estimated chat cost: `0.086915`

## Metrics

| Metric | Value |
|---|---:|
| answer_accuracy | `0.981` |
| citation_accuracy | `0.981` |
| faithfulness | `0.882` |
| hallucination_rate | `0.0` |
| response_type_accuracy | `0.923` |
| refusal_accuracy | `1.0` |
| not_found_accuracy | `1.0` |
| clarification_accuracy | `1.0` |
| failed_question_count | `4` |
| estimated_cost | `0.086915` |

## Failed Questions

- Failed count: `4`
- Failed IDs: `MULTI-004, MULTI-006, MULTI-017, MULTI-020`
- Failure buckets: `{"incomplete_answer": 1, "wrong_citation": 3}`

## Notes

- This runner calls `POST /query` instead of the prompt-experiment retrieval/generation helper.
- Permission filtering happens inside the normal API retrieval path before generation.
- Memory benchmark rows are represented as local eval sessions with their previous turns inserted before the live query.
- Benchmark expected answers, expected behavior, and expected sources were not changed.
