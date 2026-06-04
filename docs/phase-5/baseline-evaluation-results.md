# Baseline Evaluation Results

Generated at: 2026-06-04T01:43:38.797139+00:00

## Run Summary

- Questions: 60
- Retrieval mode: vector_only
- Chunking strategy: section_based
- Top K: 5
- Any-source retrieval hit: 1.000
- All-sources retrieval hit: 0.975
- Expected-source recall: 0.988
- MRR: 0.980
- Citation source match: 0.525
- Behavior match: 0.600

Answer accuracy, faithfulness, and hallucination rate are pending because they require human review or an evaluation judge.

## Question Results

| Question ID | Type | Expected Behavior | Generated Behavior | Any Source | All Sources | Source Recall | MRR | Citation Match |
|---|---|---|---|---:|---:|---:|---:|---:|
| FACT-001 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-002 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| FACT-003 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-004 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-005 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-006 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| FACT-007 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-008 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-009 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-010 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| FACT-011 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-012 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-013 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| FACT-014 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-015 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-016 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-017 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-018 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-019 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| FACT-020 | simple_factual | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| MULTI-001 | multi_document | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MULTI-002 | multi_document | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MULTI-003 | multi_document | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MULTI-004 | multi_document | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MULTI-005 | multi_document | answer | answer | 1.0 | 0.0 | 0.5 | 1.0 | 0.0 |
| MULTI-006 | multi_document | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MULTI-007 | multi_document | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MULTI-008 | multi_document | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MULTI-009 | multi_document | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MULTI-010 | multi_document | answer | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| PERM-001 | permission_restricted | refuse_no_access | say_not_found | None | None | None | None | None |
| PERM-002 | permission_restricted | refuse_no_access | say_not_found | None | None | None | None | None |
| PERM-003 | permission_restricted | refuse_no_access | answer | None | None | None | None | None |
| PERM-004 | permission_restricted | refuse_no_access | say_not_found | None | None | None | None | None |
| PERM-005 | permission_restricted | refuse_no_access | say_not_found | None | None | None | None | None |
| PERM-006 | permission_restricted | refuse_no_access | say_not_found | None | None | None | None | None |
| PERM-007 | permission_restricted | refuse_no_access | say_not_found | None | None | None | None | None |
| PERM-008 | permission_restricted | refuse_no_access | say_not_found | None | None | None | None | None |
| PERM-009 | permission_restricted | refuse_no_access | say_not_found | None | None | None | None | None |
| PERM-010 | permission_restricted | refuse_no_access | answer | None | None | None | None | None |
| MISS-001 | missing_information | say_not_found | answer | None | None | None | None | None |
| MISS-002 | missing_information | say_not_found | say_not_found | None | None | None | None | None |
| MISS-003 | missing_information | say_not_found | say_not_found | None | None | None | None | None |
| MISS-004 | missing_information | say_not_found | answer | None | None | None | None | None |
| MISS-005 | missing_information | say_not_found | answer | None | None | None | None | None |
| MISS-006 | missing_information | say_not_found | say_not_found | None | None | None | None | None |
| MISS-007 | missing_information | say_not_found | say_not_found | None | None | None | None | None |
| MISS-008 | missing_information | say_not_found | answer | None | None | None | None | None |
| MISS-009 | missing_information | say_not_found | answer | None | None | None | None | None |
| MISS-010 | missing_information | say_not_found | answer | None | None | None | None | None |
| AMB-001 | ambiguous | ask_clarifying_question | say_not_found | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| AMB-002 | ambiguous | ask_clarifying_question | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| AMB-003 | ambiguous | ask_clarifying_question | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| AMB-004 | ambiguous | ask_clarifying_question | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| AMB-005 | ambiguous | ask_clarifying_question | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| MEM-001 | conversation_memory | answer_with_memory | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| MEM-002 | conversation_memory | answer_with_memory | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| MEM-003 | conversation_memory | answer_with_memory | answer | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| MEM-004 | conversation_memory | answer_with_memory | say_not_found | 1.0 | 1.0 | 1.0 | 0.2 | 0.0 |
| MEM-005 | conversation_memory | answer_with_memory | answer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
