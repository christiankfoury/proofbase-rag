# Phase 35 Citation Alignment Results

Generated at: 2026-06-21T04:23:26.821467+00:00

## Candidate

- Run ID: `phase35-citation-alignment-v7`
- Questions: `130`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `5`
- Reranker: `lexical`
- Rerank candidate limit: `20`
- Prompt version: `v7`
- Model: `gpt-4.1-mini`

## Before / After

| Metric | Phase 34 Baseline | Phase 35 Candidate |
|---|---:|---:|
| answer_accuracy | `0.887` | `0.919` |
| citation_accuracy | `0.887` | `0.95` |
| faithfulness | `0.896` | `0.88` |
| hallucination_rate | `0.024` | `0.0` |
| response_type_accuracy | `0.865` | `0.881` |
| refusal_accuracy | `1.0` | `1.0` |
| not_found_accuracy | `1.0` | `1.0` |
| clarification_accuracy | `0.5` | `0.5` |
| failed_question_count | `24` | `16` |
| estimated_cost | `0.075913` | `0.092994` |

## Citation Failure Categories

| Category | Phase 34 Baseline | Phase 35 Candidate |
|---|---:|---:|
| wrong_document_cited | `3` | `1` |
| right_document_wrong_chunk | `8` | `6` |
| citation_missing | `15` | `7` |
| citation_attached_to_unsupported_claim | `5` | `1` |
| citation_from_restricted_source | `0` | `0` |

## Failed Questions

- Failed count: `16`
- Failed IDs: `MULTI-004, MULTI-005, MULTI-007, MULTI-008, MEM-004, MULTI-013, MULTI-014, MULTI-017, MULTI-020, AMB-006, AMB-007, AMB-008, AMB-009, AMB-010, ADV-001, ADV-005`

## Notes

- This run uses external embeddings and chat completions.
- Chat cost is estimated from configured model pricing and excludes embedding and infrastructure cost.
- Permission filtering still happens before generation through the retrieval layer.
- The Phase 35 gate is citation accuracy >= `0.92`, hallucination not above Phase 34, and permission leakage `0.000` on the matching safety run.
