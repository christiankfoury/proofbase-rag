# Phase 10 Evaluation Results Summary

Generated from: `data\evaluation\dashboard-summary.json`

## Overview

- Best retrieval run: vector-section
- Retrieval conclusion: Hybrid did not clearly outperform vector-only retrieval; vector-section remained best overall.

## Headline Metrics

| Metric | Value |
|---|---:|
| Retrieval Hit Rate | 0.975 |
| Precision At K | 0.650 |
| Mrr | 0.980 |
| Answer Accuracy | 0.829 |
| Citation Accuracy | 0.857 |
| Hallucination Rate | 0.156 |
| Permission Leakage Rate | 0.000 |
| Memory Accuracy | 1.000 |

## Run Comparison

| Run | Phase | Type | Retrieval | Chunking | Precision@k | MRR | Answer Acc | Citation Acc | Permission Leakage | Memory Acc |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| vector-section | phase-6 | retrieval_eval | vector_only | section_based | 0.650 | 0.980 | pending | pending | pending | pending |
| keyword-section | phase-6 | retrieval_eval | keyword_only | section_based | 0.525 | 0.969 | pending | pending | pending | pending |
| hybrid-section-0.5 | phase-6 | retrieval_eval | hybrid | section_based | 0.620 | 0.981 | pending | pending | pending | pending |
| vector-fixed-size | phase-6 | retrieval_eval | vector_only | fixed_size | 0.640 | 0.981 | pending | pending | pending | pending |
| hybrid-fixed-size-0.5 | phase-6 | retrieval_eval | hybrid | fixed_size | 0.620 | 0.980 | pending | pending | pending | pending |
| phase-7-answer-quality | phase-7 | answer_quality_eval | vector_only | section_based | 0.650 | 0.980 | 0.829 | 0.857 | pending | pending |
| phase-8-permission-safety | phase-8 | permission_eval | vector_only | section_based | pending | pending | pending | pending | 0.000 | pending |
| phase-9-memory | phase-9 | memory_eval | vector_only | section_based | pending | pending | pending | pending | pending | 1.000 |
| answer-generation-v1 | phase-11 | prompt_experiment | vector_only | section_based | 0.650 | 0.980 | 0.786 | 0.843 | pending | pending |
| answer-generation-v2 | phase-11 | prompt_experiment | vector_only | section_based | 0.650 | 0.980 | 0.857 | 0.871 | pending | pending |
| answer-generation-v3 | phase-11 | prompt_experiment | vector_only | section_based | 0.650 | 0.980 | 0.843 | 0.871 | pending | pending |

## Comparison Notes

- Phase 7 keeps the same retrieval baseline and adds answer/citation/confidence scoring.
- Vector-section had the strongest overall retrieval profile; hybrid matched hit rate but reduced Precision@k.
- Fixed-size chunking did not clearly outperform section-based chunking.
- Prompt experiments compare answer-generation versions; v2 is currently strongest by answer and citation metrics.

## Failed Questions

- Failed question records exported: 13
- Use `data/evaluation/failed-questions/failed-questions.json` for dashboard details.

## Honesty Notes

- No fake metrics are added by Phase 10.
- Estimated chat-generation cost is calculated where token counts are available; retrieval-only and embedding costs remain out of scope.
- Answer metrics are deterministic or heuristic signals, not a human-grade semantic evaluation.
