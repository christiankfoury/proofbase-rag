# Phase 33 Precision Candidate Results

Generated at: 2026-06-21T02:41:26.829717+00:00

- Run ID: `phase33-vector-lexical-rerank-top3`
- Questions: `130`
- Retrieval mode: `vector_lexical_rerank`
- Top K: `3`
- Reranker: `lexical`
- Candidate limit: `20`

## Metrics

- Any-source hit: `0.978`
- All-sources hit: `0.922`
- Expected-source recall: `0.95`
- Precision@k: `0.778`
- MRR: `0.965`
- Average latency ms: `840.5`
- Failed source-coverage questions: `7`

## Retrieval Gates

- Precision target: `pass`
- Recall gate: `pass`
- MRR gate: `pass`

Matching permission safety was verified in `docs/phase-33/permission-candidate-results.md`: permission leakage `0.000`, blocked-answer accuracy `1.000`, unauthorized chunk exposure `0.000`, restricted citation leakage `0.000`, unauthorized chunks reached generation `0.000`, and authorized retrieval accuracy `1.000`.
