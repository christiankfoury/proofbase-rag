# Phase 53 Live Query Regression v2

Generated at: 2026-08-26T07:12:57.006565+00:00

## Candidate

- Run ID: `phase53-live-query-regression-v2`
- Questions: `130`
- Benchmark version: `1.1`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `5`
- Prompt version: `v8`
- Multi-doc mode: `auto`
- Excluded document prefixes: `UPLOAD-`
- Estimated chat cost: `0.054799`

## Metrics

| Metric | Value |
|---|---:|
| answer_accuracy | `0.906` |
| citation_accuracy | `0.906` |
| faithfulness | `0.901` |
| hallucination_rate | `0.027` |
| response_type_accuracy | `0.869` |
| refusal_accuracy | `0.95` |
| not_found_accuracy | `0.95` |
| clarification_accuracy | `1.0` |
| failed_question_count | `15` |
| submetric_issue_count | `43` |
| actionable_submetric_issue_count | `15` |
| diagnostic_submetric_note_count | `28` |
| estimated_cost | `0.054799` |

## Failed Questions

- Failed count: `15`
- Failed IDs: `FACT-012, MULTI-004, MULTI-009, PERM-003, MISS-010, MULTI-011, MULTI-014, MULTI-017, MULTI-018, MULTI-019, MULTI-020, ADV-003, ADV-004, ADV-005, CONF-004`
- Failure buckets: `{"answer_not_generated": 5, "incomplete_answer": 1, "missed_refusal": 1, "not_found_failure": 1, "unsupported_answer": 2, "wrong_citation": 5}`
- Submetric issue count: `43`
- Actionable submetric issue count: `15`
- Diagnostic submetric note count: `28`
- Submetric issue IDs: `FACT-012, MULTI-004, MULTI-009, PERM-003, MISS-010, AMB-001, AMB-004, AMB-005, MEM-001, MEM-002, MEM-003, MEM-004, MEM-005, MEM-006, MEM-007, MEM-008, MEM-009, MEM-010, MULTI-011, MULTI-014, MULTI-017, MULTI-018, MULTI-019, MULTI-020, MEM-011, MEM-012, MEM-013, MEM-014, MEM-015, MEM-016, MEM-017, MEM-018, MEM-019, MEM-020, AMB-006, AMB-007, AMB-008, AMB-009, AMB-010, ADV-003, ADV-004, ADV-005, CONF-004`
- Submetric issue breakdown: `{"actionable": {"count": 15, "ids": ["ADV-003", "ADV-004", "ADV-005", "CONF-004", "FACT-012", "MISS-010", "MULTI-004", "MULTI-009", "MULTI-011", "MULTI-014", "MULTI-017", "MULTI-018", "MULTI-019", "MULTI-020", "PERM-003"]}, "clarification_source_coverage_diagnostic": {"count": 8, "ids": ["AMB-001", "AMB-004", "AMB-005", "AMB-006", "AMB-007", "AMB-008", "AMB-009", "AMB-010"]}, "memory_response_type_diagnostic": {"count": 20, "ids": ["MEM-001", "MEM-002", "MEM-003", "MEM-004", "MEM-005", "MEM-006", "MEM-007", "MEM-008", "MEM-009", "MEM-010", "MEM-011", "MEM-012", "MEM-013", "MEM-014", "MEM-015", "MEM-016", "MEM-017", "MEM-018", "MEM-019", "MEM-020"]}}`

## Notes

- This runner calls `POST /query` instead of the prompt-experiment retrieval/generation helper.
- Permission filtering happens inside the normal API retrieval path before generation.
- Uploaded-document fixtures are excluded from benchmark retrieval before generation.
- Memory benchmark rows are represented as local eval sessions with their previous turns inserted before the live query.
- Memory `answer_with_memory` response-type half-credit is retained for historical comparability but reported as a diagnostic note when answer and citation behavior are otherwise correct.
- Correct clarification responses with incomplete source coverage are reported as diagnostic notes instead of answer/citation failures.
- Benchmark expected answers, expected behavior, and expected sources were not changed.
