# Phase 32 Expanded Baseline Results

Generated at: 2026-06-21T00:30:15.201039+00:00

Budget guardrail: $10.00

## Retrieval Baseline

- Run ID: `phase32-expanded-retrieval`
- Questions: 130
- All-sources hit: `0.967`
- Precision@k: `0.616`
- MRR: `0.954`
- Failed source-coverage questions: 3
- Failed source-coverage IDs: `MULTI-005`, `MULTI-008`, `MEM-004`

## Answer Baseline

- Run ID: `phase32-expanded-answer-generation-v5`
- Questions: 130
- Answer accuracy: `0.85`
- Citation accuracy: `0.844`
- Hallucination rate: `0.205`
- Response type accuracy: `0.758`
- Estimated chat cost: `$0.097194`
- Failed questions: 43
- Failed-question details are exported to `data/evaluation/failed-questions/failed-questions.json`.

## Notes

- This is a baseline on the expanded benchmark, not a claimed improvement.
- Chat cost is estimated from model pricing and excludes embedding and infrastructure cost.
- Retrieval metrics and answer-quality metrics are separated so future tuning can compare like with like.
