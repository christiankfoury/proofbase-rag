# Phase 6 Evaluation Results

Generated at: 2026-06-04T02:11:44.834094+00:00

## Configurations Tested

| Run | Mode | Chunking | Top K | Vector Weight | Keyword Weight |
|---|---|---|---:|---:|---:|
| vector-section | vector_only | section_based | 5 | 0.5 | 0.5 |
| keyword-section | keyword_only | section_based | 5 | 0.5 | 0.5 |
| hybrid-section-0.5 | hybrid | section_based | 5 | 0.5 | 0.5 |
| vector-fixed-size | vector_only | fixed_size | 5 | 0.5 | 0.5 |
| hybrid-fixed-size-0.5 | hybrid | fixed_size | 5 | 0.5 | 0.5 |

## Retrieval Metrics

| Run | Any Source | All Sources | Source Recall | Precision@k | MRR | Avg Latency ms | Failed Questions |
|---|---:|---:|---:|---:|---:|---:|---|
| vector-section | 1.000 | 0.975 | 0.988 | 0.650 | 0.980 | 661.983 | MULTI-005 |
| keyword-section | 1.000 | 0.950 | 0.975 | 0.525 | 0.969 | 25.367 | MULTI-004, MULTI-008 |
| hybrid-section-0.5 | 1.000 | 0.975 | 0.988 | 0.620 | 0.981 | 696.650 | MULTI-005 |
| vector-fixed-size | 1.000 | 0.975 | 0.988 | 0.640 | 0.981 | 757.683 | MULTI-005 |
| hybrid-fixed-size-0.5 | 1.000 | 0.950 | 0.975 | 0.620 | 0.980 | 984.117 | MULTI-004, MULTI-005 |

## Hybrid vs Vector Baseline

- Baseline: `vector-section`
- Candidate: `hybrid-section-0.5`
- Improved questions: FACT-007, FACT-015, FACT-016, AMB-003, MEM-004
- Regressed questions: FACT-005, FACT-012, FACT-018, FACT-019, MULTI-003, MULTI-005, MULTI-006, AMB-002, MEM-002, MEM-005
- Unchanged answerable questions: 25

A question is considered improved when all-sources hit, source recall, MRR, or Precision@k improves in that order. It is considered regressed when the same ordered metric tuple gets worse.

## Pending Metrics

- Answer accuracy: pending human or judge evaluation.
- Faithfulness: pending human or judge evaluation.
- Hallucination rate: pending human or judge evaluation.
- Token usage and cost: pending model-call instrumentation.

## Notes

- These are retrieval-only runs to avoid unnecessary chat-completion cost.
- Permission-restricted and missing-information questions are excluded from retrieval averages because they have no expected retrievable source for the requesting role.
- Azure AI Search, reranking, and semantic chunking remain deferred.
