# Phase 33 Precision Candidate Runbook

Generated at: 2026-06-21T01:21:58.740830+00:00

## Candidate Config

- Run ID: `phase33-vector-lexical-rerank-top3`
- Retrieval mode: `vector_lexical_rerank`
- Chunking strategy: `section_based`
- Top K: `3`
- Reranker: `lexical`
- Rerank candidate limit: `20`

## Required Live Commands

```powershell
python scripts/run_phase33_precision_candidate.py
python scripts/run_permission_eval.py
python scripts/export_dashboard_data.py
```

## Gates

- Precision@k must be `>= 0.75`.
- Expected-source recall must be `>= 0.95`.
- MRR must be `>= 0.95`.
- Permission leakage must remain `0.000`.

## Current Status

- Dry run only.
- OpenAI-backed retrieval sends benchmark questions to the embedding API; run only with explicit approval.
