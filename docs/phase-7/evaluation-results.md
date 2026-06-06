# Phase 7 Evaluation Results

Generated at: 2026-06-05T01:50:38.484296+00:00

## Run Summary

- Questions: 60
- Retrieval mode: vector_only
- Chunking strategy: section_based
- Top K: 5
- Any-source hit: 1.000
- All-sources hit: 0.975
- Precision@k: 0.650
- MRR: 0.980
- Answer accuracy: 0.829
- Citation accuracy: 0.857
- Faithfulness/support score: 0.790
- Hallucination rate: 0.156
- Response type accuracy: 0.917
- Refusal accuracy: 1.000
- Not-found accuracy: 1.000
- Clarification accuracy: 1.000
- Average final confidence: 0.705
- Input tokens: 30593
- Output tokens: 10108
- Estimated cost: 0.028410

## Question Results

| Question ID | Expected | Actual | Answer Acc | Citation Acc | Faithfulness | Hallucination | Final Confidence |
|---|---|---|---:|---:|---:|---:|---:|
| FACT-001 | answer | answer | 1.0 | 1.0 | 0.955 | 0.0 | 0.915 |
| FACT-002 | answer | answer | 1.0 | 1.0 | 0.963 | 0.0 | 0.919 |
| FACT-003 | answer | answer | 1.0 | 1.0 | 0.915 | 0.0 | 0.88 |
| FACT-004 | answer | answer | 1.0 | 1.0 | 0.955 | 0.0 | 0.892 |
| FACT-005 | answer | answer | 1.0 | 1.0 | 0.902 | 0.0 | 0.825 |
| FACT-006 | answer | answer | 1.0 | 1.0 | 0.936 | 0.0 | 0.856 |
| FACT-007 | answer | answer | 1.0 | 1.0 | 0.777 | 0.0 | 0.773 |
| FACT-008 | answer | answer | 0.5 | 1.0 | 0.863 | 0.0 | 0.807 |
| FACT-009 | answer | answer | 1.0 | 1.0 | 0.86 | 0.0 | 0.793 |
| FACT-010 | answer | answer | 0.5 | 1.0 | 0.793 | 0.0 | 0.781 |
| FACT-011 | answer | answer | 1.0 | 1.0 | 0.94 | 0.0 | 0.876 |
| FACT-012 | answer | not_found | 0.0 | 0.0 | None | None | 0.727 |
| FACT-013 | answer | answer | 1.0 | 1.0 | 0.873 | 0.0 | 0.853 |
| FACT-014 | answer | answer | 1.0 | 1.0 | 0.863 | 0.0 | 0.827 |
| FACT-015 | answer | answer | 1.0 | 1.0 | 0.955 | 0.0 | 0.904 |
| FACT-016 | answer | answer | 1.0 | 1.0 | 0.961 | 0.0 | 0.904 |
| FACT-017 | answer | answer | 1.0 | 1.0 | 0.911 | 0.0 | 0.869 |
| FACT-018 | answer | answer | 1.0 | 1.0 | 0.785 | 0.0 | 0.771 |
| FACT-019 | answer | answer | 1.0 | 1.0 | 0.95 | 0.0 | 0.894 |
| FACT-020 | answer | answer | 1.0 | 1.0 | 0.868 | 0.0 | 0.791 |
| MULTI-001 | answer | not_found | 0.0 | 0.0 | None | None | 0.712 |
| MULTI-002 | answer | partial_answer | 1.0 | 1.0 | 0.616 | 0.0 | 0.651 |
| MULTI-003 | answer | partial_answer | 1.0 | 1.0 | 0.548 | 1.0 | 0.561 |
| MULTI-004 | answer | partial_answer | 1.0 | 0.5 | 0.573 | 0.0 | 0.623 |
| MULTI-005 | answer | partial_answer | 0.0 | 0.5 | 0.602 | 0.0 | 0.63 |
| MULTI-006 | answer | partial_answer | 1.0 | 0.5 | 0.589 | 0.0 | 0.629 |
| MULTI-007 | answer | partial_answer | 0.5 | 1.0 | 0.554 | 1.0 | 0.592 |
| MULTI-008 | answer | partial_answer | 0.5 | 0.5 | 0.525 | 1.0 | 0.506 |
| MULTI-009 | answer | partial_answer | 1.0 | 1.0 | 0.578 | 0.0 | 0.63 |
| MULTI-010 | answer | partial_answer | 1.0 | 1.0 | 0.55 | 1.0 | 0.555 |
| PERM-001 | refuse_no_access | refuse_no_access | None | None | None | None | 0.568 |
| PERM-002 | refuse_no_access | refuse_no_access | None | None | None | None | 0.595 |
| PERM-003 | refuse_no_access | refuse_no_access | None | None | None | None | 0.66 |
| PERM-004 | refuse_no_access | refuse_no_access | None | None | None | None | 0.574 |
| PERM-005 | refuse_no_access | refuse_no_access | None | None | None | None | 0.636 |
| PERM-006 | refuse_no_access | refuse_no_access | None | None | None | None | 0.645 |
| PERM-007 | refuse_no_access | refuse_no_access | None | None | None | None | 0.599 |
| PERM-008 | refuse_no_access | refuse_no_access | None | None | None | None | 0.59 |
| PERM-009 | refuse_no_access | refuse_no_access | None | None | None | None | 0.59 |
| PERM-010 | refuse_no_access | refuse_no_access | None | None | None | None | 0.651 |
| MISS-001 | say_not_found | not_found | None | None | None | None | 0.716 |
| MISS-002 | say_not_found | not_found | None | None | None | None | 0.568 |
| MISS-003 | say_not_found | not_found | None | None | None | None | 0.619 |
| MISS-004 | say_not_found | not_found | None | None | None | None | 0.692 |
| MISS-005 | say_not_found | not_found | None | None | None | None | 0.636 |
| MISS-006 | say_not_found | not_found | None | None | None | None | 0.594 |
| MISS-007 | say_not_found | not_found | None | None | None | None | 0.617 |
| MISS-008 | say_not_found | not_found | None | None | None | None | 0.649 |
| MISS-009 | say_not_found | not_found | None | None | None | None | 0.662 |
| MISS-010 | say_not_found | not_found | None | None | None | None | 0.643 |
| AMB-001 | ask_clarifying_question | clarify | None | None | None | None | 0.611 |
| AMB-002 | ask_clarifying_question | clarify | None | None | None | None | 0.703 |
| AMB-003 | ask_clarifying_question | clarify | None | None | None | None | 0.684 |
| AMB-004 | ask_clarifying_question | clarify | None | None | None | None | 0.605 |
| AMB-005 | ask_clarifying_question | clarify | None | None | None | None | 0.622 |
| MEM-001 | answer_with_memory | answer | 1.0 | 1.0 | 0.794 | 0.0 | 0.748 |
| MEM-002 | answer_with_memory | answer | 1.0 | 1.0 | 0.869 | 0.0 | 0.829 |
| MEM-003 | answer_with_memory | partial_answer | 1.0 | 1.0 | 0.688 | 1.0 | 0.684 |
| MEM-004 | answer_with_memory | not_found | 0.0 | 0.0 | None | None | 0.627 |
| MEM-005 | answer_with_memory | answer | 1.0 | 1.0 | 0.754 | 0.0 | 0.71 |

## Notes

- Answer accuracy uses deterministic expected-answer term overlap and should be treated as a baseline signal, not a human-grade semantic judge.
- Citation accuracy checks whether citations point to expected source documents.
- Faithfulness is the heuristic citation confidence score.
- Estimated cost uses configured chat model pricing and excludes embedding/ingestion cost.
