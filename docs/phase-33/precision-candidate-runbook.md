# Phase 33 Precision Candidate Runbook

Generated at: 2026-06-21T02:39:33.851569+00:00

## Candidate Config

- Run ID: `phase33-vector-lexical-rerank-top3`
- Retrieval mode: `vector_lexical_rerank`
- Chunking strategy: `section_based`
- Top K: `3`
- Reranker: `lexical`
- Rerank candidate limit: `20`

## Required Live Commands

```powershell
python scripts/run_phase33_precision_candidate.py --top-k 3 --candidate-limit 20 --allow-external-embeddings
python scripts/run_permission_eval.py --retrieval-mode vector_lexical_rerank --top-k 3 --rerank-candidate-limit 20 --allow-external-embeddings
python scripts/export_dashboard_data.py
```

## Gates

- Precision@k must be `>= 0.75`.
- Expected-source recall must be `>= 0.95`.
- MRR must be `>= 0.95`.
- Permission leakage must remain `0.000`.

## Current Status

- Live run completed; inspect `precision-candidate-results.md`, `permission-candidate-results.md`, and exported dashboard data.
- Phase 33 retrieval gates and permission safety gates passed for `phase33-vector-lexical-rerank-top3`.
- OpenAI-backed retrieval sends benchmark questions to the embedding API; the live commands require `--allow-external-embeddings` and should run only after explicit approval.
