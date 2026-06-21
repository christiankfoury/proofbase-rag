# Phase 34 Answer Grounding Results

Generated at: 2026-06-21T03:31:24.438832+00:00

## Candidate

- Run ID: `phase34-answer-grounding-v6`
- Questions: `130`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `3`
- Reranker: `lexical`
- Rerank candidate limit: `20`
- Prompt version: `v6`
- Model: `gpt-4.1-mini`

## Before / After

| Metric | Phase 32 Baseline | Phase 34 Candidate |
|---|---:|---:|
| answer_accuracy | `0.85` | `0.887` |
| citation_accuracy | `0.844` | `0.887` |
| faithfulness | `0.8` | `0.896` |
| hallucination_rate | `0.205` | `0.024` |
| response_type_accuracy | `0.758` | `0.865` |
| refusal_accuracy | `0.55` | `1.0` |
| not_found_accuracy | `0.95` | `1.0` |
| clarification_accuracy | `0.5` | `0.5` |
| failed_question_count | `43` | `24` |
| estimated_cost | `0.097194` | `0.075913` |

## Failed Questions

- Failed count: `24`
- Failed IDs: `FACT-012, MULTI-001, MULTI-003, MULTI-004, MULTI-005, MULTI-006, MULTI-008, MULTI-010, MEM-004, MULTI-011, MULTI-013, MULTI-014, MULTI-017, MULTI-019, MULTI-020, AMB-006, AMB-007, AMB-008, AMB-009, AMB-010, ADV-001, ADV-003, ADV-004, ADV-005`

## Notes

- This run uses external embeddings and chat completions.
- Chat cost is estimated from configured model pricing and excludes embedding and infrastructure cost.
- Permission filtering still happens before generation through the retrieval layer.
- The target is hallucination rate <= `0.08` without answer-accuracy regression.
