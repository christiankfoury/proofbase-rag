# Phase 32 Verification

Generated at: 2026-06-21

## Ingestion

- Command: `python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based`
- Documents: 19
- Chunks: 119
- Embeddings: 119
- Failures: 0

This regenerated embeddings for the expanded synthetic corpus after user approval to send the corpus content to OpenAI embeddings.

## Expanded Baseline Runs

Retrieval-only baseline:

- Run ID: `phase32-expanded-retrieval`
- Benchmark version: `1.1`
- Questions: 130
- Retrieval mode: `vector_only`
- Chunking strategy: `section_based`
- Top K: 5
- Any-source hit: `0.989`
- All-sources hit: `0.967`
- Expected-source recall: `0.978`
- Precision@k: `0.616`
- MRR: `0.954`
- Average latency ms: `848.123`
- Failed source-coverage questions: 3 (`MULTI-005`, `MULTI-008`, `MEM-004`)

Answer baseline:

- Run ID: `phase32-expanded-answer-generation-v5`
- Benchmark version: `1.1`
- Questions: 130
- Prompt version: `v5`
- Model: `gpt-4.1-mini`
- Answer accuracy: `0.85`
- Citation accuracy: `0.844`
- Faithfulness: `0.8`
- Hallucination rate: `0.205`
- Response type accuracy: `0.758`
- Refusal accuracy: `0.55`
- Not-found accuracy: `0.95`
- Clarification accuracy: `0.5`
- Failed questions: 43
- Input tokens: 122211
- Output tokens: 30192
- Estimated chat cost: `$0.097194`

The answer baseline sent benchmark questions and retrieved synthetic corpus content to OpenAI chat after user approval. Cost is a chat-model estimate and excludes embedding, infrastructure, cached-input, and batch-processing cost.

## Dashboard Export

- Command: `python scripts/export_dashboard_data.py`
- Exported runs: 15
- Exported current failed-question items: 43
- New run files:
  - `data/evaluation/eval-runs/phase32-expanded-retrieval.json`
  - `data/evaluation/eval-runs/phase32-expanded-answer-generation-v5.json`

## Additional Checks

- `python -m compileall apps scripts`
- `python scripts/validate_benchmark.py`
- `git diff --check`

## Notes

- Phase 32 establishes the expanded baseline only. It does not claim any improvement.
- Legacy 60-question headline metrics remain legacy artifacts until later phases produce measured before/after runs.
- Phase 33 should start from the expanded precision@k baseline of `0.616` while preserving all-sources hit `0.967`, MRR `0.954`, and permission filtering.
