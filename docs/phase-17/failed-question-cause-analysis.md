# Phase 17 Failed-Question Cause Analysis

Generated at: 2026-06-09T23:30:44.709375+00:00

## Summary

- Failed questions analyzed: 13
- Largest bucket: Answer support issue
- Target question IDs: MULTI-003, MULTI-007, MULTI-010, MEM-003

## Bucket Counts

| Cause Bucket | Count | Question IDs |
|---|---:|---|
| Answer support issue | 4 | MULTI-003, MULTI-007, MULTI-010, MEM-003 |
| Citation mismatch | 3 | MULTI-004, MULTI-006, MULTI-008 |
| Confidence threshold downgrade | 3 | FACT-012, MULTI-001, MEM-004 |
| Answer completeness | 2 | FACT-008, FACT-010 |
| Multi-document synthesis issue | 1 | MULTI-005 |

## Detailed Failures

| Question ID | Type | Cause | Expected Sources | Citations | Retrieved Documents | Recommended Fix |
|---|---|---|---|---|---|---|
| FACT-008 | simple_factual | Answer completeness | HR-003 | HR-003 | HR-003, IT-001, HR-002 | Improve answer completeness scoring or prompt the model to include all required expected-answer facts. |
| FACT-010 | simple_factual | Answer completeness | HR-004 | HR-004 | HR-004, HR-002 | Improve answer completeness scoring or prompt the model to include all required expected-answer facts. |
| FACT-012 | simple_factual | Confidence threshold downgrade | IT-001 | - | IT-001, IT-003, IT-002 | Adjust confidence thresholds or prompting so answerable questions do not downgrade to not-found when supporting sources were retrieved. |
| MULTI-001 | multi_document | Confidence threshold downgrade | HR-003, IT-002 | - | HR-003, IT-002 | Adjust confidence thresholds or prompting so answerable questions do not downgrade to not-found when supporting sources were retrieved. |
| MULTI-003 | multi_document | Answer support issue | HR-001, HR-002 | HR-002, HR-001 | HR-002, HR-001 | Tighten answer prompt and lower confidence when citation validation is weak. |
| MULTI-004 | multi_document | Citation mismatch | SALES-002, SALES-003 | SALES-003 | SALES-003, SALES-001, SALES-002 | Improve citation formatting and require the model to cite the exact supporting chunk. |
| MULTI-005 | multi_document | Multi-document synthesis issue | SALES-001, SALES-002 | SALES-001 | SALES-001, SALES-003 | Add query decomposition or multi-document retrieval logic. |
| MULTI-006 | multi_document | Citation mismatch | MGR-001, MGR-002 | - | MGR-002, MGR-001 | Improve citation formatting and require the model to cite the exact supporting chunk. |
| MULTI-007 | multi_document | Answer support issue | HR-003, IT-002 | IT-002, HR-003 | HR-003, IT-002, HR-001 | Tighten answer prompt and lower confidence when citation validation is weak. |
| MULTI-008 | multi_document | Citation mismatch | HR-001, HR-004 | HR-004 | HR-004, HR-002, HR-001 | Improve citation formatting and require the model to cite the exact supporting chunk. |
| MULTI-010 | multi_document | Answer support issue | HR-003, HR-ADMIN-001 | HR-ADMIN-001, HR-003 | HR-ADMIN-001, HR-003, IT-002 | Tighten answer prompt and lower confidence when citation validation is weak. |
| MEM-003 | conversation_memory | Answer support issue | IT-002 | IT-002, IT-003 | IT-002, HR-003, IT-001, IT-003 | Tighten answer prompt and lower confidence when citation validation is weak. |
| MEM-004 | conversation_memory | Confidence threshold downgrade | SALES-002 | - | SALES-001, SALES-002 | Adjust confidence thresholds or prompting so answerable questions do not downgrade to not-found when supporting sources were retrieved. |

## V5 Evaluation Results

| Run | Questions | Failed | Answer Accuracy | Citation Accuracy | Hallucination Rate | Response Type Accuracy | Est. Cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| v5 failed subset | 13 | 9 | 0.654 | 0.615 | 0.4 | 0.731 | 0.013502 |
| v5 full benchmark | 60 | 8 | 0.871 | 0.857 | 0.094 | 0.917 | 0.032533 |

- Target bucket changed from 4 to 1 on the full v5 run.
- Full v5 remaining failed IDs: FACT-012, MULTI-001, MULTI-003, MULTI-004, MULTI-005, MULTI-006, MULTI-008, MEM-004

## First Fix Target

The first implementation target is the largest measured bucket. For this run, that means reducing unsupported-answer cases by making the prompt omit weakly supported claims, cite only directly supporting chunks, and prefer partial answers when only part of the expected answer is supported.

## Regression Gate

- Run a focused prompt experiment against these failed IDs before a full benchmark.
- Promote the prompt only if the target bucket decreases without increasing permission leakage, not-found failures, or hallucination rate.
