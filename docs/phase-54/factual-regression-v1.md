# Phase 39 Live Query Answer-Quality Results

Generated at: 2026-08-26T09:02:08.714021+00:00

## Candidate

- Run ID: `phase54-factual-regression-v1`
- Questions: `30`
- Benchmark version: `1.1`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `5`
- Prompt version: `v8`
- Multi-doc mode: `auto`
- Excluded document prefixes: `UPLOAD-`
- Estimated chat cost: `0.027739`

## Metrics

| Metric | Value |
|---|---:|
| answer_accuracy | `1.0` |
| citation_accuracy | `1.0` |
| faithfulness | `0.928` |
| hallucination_rate | `0.0` |
| response_type_accuracy | `1.0` |
| refusal_accuracy | `None` |
| not_found_accuracy | `None` |
| clarification_accuracy | `None` |
| failed_question_count | `0` |
| submetric_issue_count | `0` |
| actionable_submetric_issue_count | `0` |
| diagnostic_submetric_note_count | `0` |
| estimated_cost | `0.027739` |
| post_generation_validation_estimated_cost | `0.025444` |
| post_generation_validation_mean_latency_ms | `4118.033` |
| post_generation_validation_repair_count | `3` |
| post_generation_validation_downgrade_count | `0` |

## Failed Questions

- Failed count: `0`
- Failed IDs: `None`
- Failure buckets: `{}`
- Submetric issue count: `0`
- Actionable submetric issue count: `0`
- Diagnostic submetric note count: `0`
- Submetric issue IDs: `None`
- Submetric issue breakdown: `{"actionable": {"count": 0, "ids": []}, "clarification_source_coverage_diagnostic": {"count": 0, "ids": []}, "memory_response_type_diagnostic": {"count": 0, "ids": []}}`

## Notes

- This runner calls `POST /query` instead of the prompt-experiment retrieval/generation helper.
- Permission filtering happens inside the normal API retrieval path before generation.
- Evidence assessment runs after permission filtering and before generation; its cost and latency are recorded separately.
- Post-generation validation uses only the same authorized chunks, buffers streaming output, and permits at most one repair; its cost, latency, and outcomes are recorded separately.
- Uploaded-document fixtures are excluded from benchmark retrieval before generation.
- Memory benchmark rows are represented as local eval sessions with their previous turns inserted before the live query.
- Memory `answer_with_memory` response-type half-credit is retained for historical comparability but reported as a diagnostic note when answer and citation behavior are otherwise correct.
- Correct clarification responses with incomplete source coverage are reported as diagnostic notes instead of answer/citation failures.
- Benchmark expected answers, expected behavior, and expected sources were not changed.
