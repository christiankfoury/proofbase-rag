# Phase 53 Live Query Regression v5

Generated at: 2026-08-26T08:17:55.099865+00:00

## Candidate

- Run ID: `phase53-live-query-regression-v5`
- Questions: `130`
- Benchmark version: `1.1`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `5`
- Prompt version: `v8`
- Multi-doc mode: `auto`
- Excluded document prefixes: `UPLOAD-`
- Estimated chat cost: `0.066771`

## Metrics

| Metric | Value |
|---|---:|
| answer_accuracy | `1.0` |
| citation_accuracy | `1.0` |
| faithfulness | `0.887` |
| hallucination_rate | `0.0` |
| response_type_accuracy | `0.923` |
| refusal_accuracy | `1.0` |
| not_found_accuracy | `1.0` |
| clarification_accuracy | `1.0` |
| failed_question_count | `0` |
| submetric_issue_count | `28` |
| actionable_submetric_issue_count | `0` |
| diagnostic_submetric_note_count | `28` |
| estimated_cost | `0.066771` |

## Failed Questions

- Failed count: `0`
- Failed IDs: `None`
- Failure buckets: `{}`
- Submetric issue count: `28`
- Actionable submetric issue count: `0`
- Diagnostic submetric note count: `28`
- Submetric issue IDs: `AMB-001, AMB-004, AMB-005, MEM-001, MEM-002, MEM-003, MEM-004, MEM-005, MEM-006, MEM-007, MEM-008, MEM-009, MEM-010, MEM-011, MEM-012, MEM-013, MEM-014, MEM-015, MEM-016, MEM-017, MEM-018, MEM-019, MEM-020, AMB-006, AMB-007, AMB-008, AMB-009, AMB-010`
- Submetric issue breakdown: `{"actionable": {"count": 0, "ids": []}, "clarification_source_coverage_diagnostic": {"count": 8, "ids": ["AMB-001", "AMB-004", "AMB-005", "AMB-006", "AMB-007", "AMB-008", "AMB-009", "AMB-010"]}, "memory_response_type_diagnostic": {"count": 20, "ids": ["MEM-001", "MEM-002", "MEM-003", "MEM-004", "MEM-005", "MEM-006", "MEM-007", "MEM-008", "MEM-009", "MEM-010", "MEM-011", "MEM-012", "MEM-013", "MEM-014", "MEM-015", "MEM-016", "MEM-017", "MEM-018", "MEM-019", "MEM-020"]}}`

## Notes

- This runner calls `POST /query` instead of the prompt-experiment retrieval/generation helper.
- Permission filtering happens inside the normal API retrieval path before generation.
- Uploaded-document fixtures are excluded from benchmark retrieval before generation.
- Memory benchmark rows are represented as local eval sessions with their previous turns inserted before the live query.
- Memory `answer_with_memory` response-type half-credit is retained for historical comparability but reported as a diagnostic note when answer and citation behavior are otherwise correct.
- Correct clarification responses with incomplete source coverage are reported as diagnostic notes instead of answer/citation failures.
- Benchmark expected answers, expected behavior, and expected sources were not changed.
