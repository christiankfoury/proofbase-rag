# Phase 52 Request Assessment Answer-Quality Regression

Generated at: 2026-08-26T05:11:47.403841+00:00

## Candidate

- Run ID: `phase52-request-assessment-regression`
- Questions: `130`
- Benchmark version: `1.1`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `5`
- Prompt version: `v8`
- Multi-doc mode: `auto`
- Excluded document prefixes: `UPLOAD-`
- Estimated chat cost: `0.065742`

## Metrics

| Metric | Value |
|---|---:|
| answer_accuracy | `0.9` |
| citation_accuracy | `0.9` |
| faithfulness | `0.891` |
| hallucination_rate | `0.0` |
| response_type_accuracy | `0.804` |
| refusal_accuracy | `0.9` |
| not_found_accuracy | `0.7` |
| clarification_accuracy | `1.0` |
| failed_question_count | `16` |
| submetric_issue_count | `43` |
| actionable_submetric_issue_count | `16` |
| diagnostic_submetric_note_count | `27` |
| estimated_cost | `0.065742` |

## Failed Questions

- Failed count: `16`
- Failed IDs: `MULTI-002, MULTI-004, MULTI-010, MISS-005, MISS-008, MISS-010, MULTI-020, PERM-011, PERM-016, MISS-013, MISS-015, MISS-019, MEM-015, ADV-001, ADV-003, CONF-004`
- Failure buckets: `{"missed_refusal": 2, "multi_document_failure": 4, "not_found_failure": 6, "retrieval_miss": 4}`
- Submetric issue count: `43`
- Actionable submetric issue count: `16`
- Diagnostic submetric note count: `27`
- Submetric issue IDs: `MULTI-002, MULTI-004, MULTI-010, MISS-005, MISS-008, MISS-010, AMB-001, AMB-004, AMB-005, MEM-001, MEM-002, MEM-003, MEM-004, MEM-005, MEM-006, MEM-007, MEM-008, MEM-009, MEM-010, MULTI-020, PERM-011, PERM-016, MISS-013, MISS-015, MISS-019, MEM-011, MEM-012, MEM-013, MEM-014, MEM-015, MEM-016, MEM-017, MEM-018, MEM-019, MEM-020, AMB-006, AMB-007, AMB-008, AMB-009, AMB-010, ADV-001, ADV-003, CONF-004`
- Submetric issue breakdown: `{"actionable": {"count": 16, "ids": ["ADV-001", "ADV-003", "CONF-004", "MEM-015", "MISS-005", "MISS-008", "MISS-010", "MISS-013", "MISS-015", "MISS-019", "MULTI-002", "MULTI-004", "MULTI-010", "MULTI-020", "PERM-011", "PERM-016"]}, "clarification_source_coverage_diagnostic": {"count": 8, "ids": ["AMB-001", "AMB-004", "AMB-005", "AMB-006", "AMB-007", "AMB-008", "AMB-009", "AMB-010"]}, "memory_response_type_diagnostic": {"count": 19, "ids": ["MEM-001", "MEM-002", "MEM-003", "MEM-004", "MEM-005", "MEM-006", "MEM-007", "MEM-008", "MEM-009", "MEM-010", "MEM-011", "MEM-012", "MEM-013", "MEM-014", "MEM-016", "MEM-017", "MEM-018", "MEM-019", "MEM-020"]}}`

## Notes

- This runner calls `POST /query` instead of the prompt-experiment retrieval/generation helper.
- Permission filtering happens inside the normal API retrieval path before generation.
- Uploaded-document fixtures are excluded from benchmark retrieval before generation.
- Memory benchmark rows are represented as local eval sessions with their previous turns inserted before the live query.
- Memory `answer_with_memory` response-type half-credit is retained for historical comparability but reported as a diagnostic note when answer and citation behavior are otherwise correct.
- Correct clarification responses with incomplete source coverage are reported as diagnostic notes instead of answer/citation failures.
- Benchmark expected answers, expected behavior, and expected sources were not changed.
