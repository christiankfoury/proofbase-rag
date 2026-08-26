# Phase 52 Request Assessment Final Subset

Generated at: 2026-08-26T05:27:02.251040+00:00

## Candidate

- Run ID: `phase52-request-assessment-final-subset`
- Questions: `2`
- Benchmark version: `1.1`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `5`
- Prompt version: `v8`
- Multi-doc mode: `auto`
- Excluded document prefixes: `UPLOAD-`
- Estimated chat cost: `0.0`

## Metrics

| Metric | Value |
|---|---:|
| answer_accuracy | `None` |
| citation_accuracy | `None` |
| faithfulness | `None` |
| hallucination_rate | `None` |
| response_type_accuracy | `1.0` |
| refusal_accuracy | `None` |
| not_found_accuracy | `1.0` |
| clarification_accuracy | `None` |
| failed_question_count | `0` |
| submetric_issue_count | `0` |
| actionable_submetric_issue_count | `0` |
| diagnostic_submetric_note_count | `0` |
| estimated_cost | `0.0` |

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
- Uploaded-document fixtures are excluded from benchmark retrieval before generation.
- Memory benchmark rows are represented as local eval sessions with their previous turns inserted before the live query.
- Memory `answer_with_memory` response-type half-credit is retained for historical comparability but reported as a diagnostic note when answer and citation behavior are otherwise correct.
- Correct clarification responses with incomplete source coverage are reported as diagnostic notes instead of answer/citation failures.
- Benchmark expected answers, expected behavior, and expected sources were not changed.
