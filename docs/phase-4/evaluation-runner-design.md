# Evaluation Runner Design

## Purpose

The evaluation runner measures whether the RAG system improves across versions. It uses `data/evaluation/benchmark-questions.json` and runs each benchmark question through the same retrieval and answer pipeline used by chat.

## Runner Flow

1. Load benchmark questions from `data/evaluation/benchmark-questions.json`.
2. Import or update `evaluation_questions`.
3. Create an `evaluation_runs` record with the system configuration.
4. For each benchmark question, simulate the specified user role and previous turns.
5. Run retrieval with the configured retrieval mode, top_k, and chunking strategy.
6. Generate an answer, refusal, not-found response, clarification, or memory answer.
7. Store `retrieval_runs`, `retrieved_chunks`, `answer_runs`, and `citations`.
8. Score the result against expected behavior, expected answer, expected source documents, and expected citations.
9. Store `evaluation_results`.
10. Produce summary metrics and compare runs.

## Evaluation Configuration

```json
{
  "run_name": "baseline-vector-only",
  "retrieval_mode": "vector_only",
  "chunking_strategy": "section_based",
  "top_k": 5,
  "prompt_version": "answer_v1",
  "model": "gpt-4.1-mini"
}
```

## Metrics

Retrieval:

- retrieval hit rate
- Precision@k
- Recall@k
- MRR

Answer quality:

- answer accuracy
- citation accuracy
- faithfulness
- hallucination rate
- refusal accuracy

Security:

- permission leakage rate
- blocked-answer accuracy

System:

- latency
- token usage
- cost per answer

Use placeholders such as X% to Y% until real evaluation runs produce measured values.

## Database Storage

Use:

- `evaluation_questions` for benchmark imports
- `evaluation_runs` for run metadata and config
- `evaluation_results` for per-question scores
- `retrieval_runs` and `retrieved_chunks` for retrieval trace
- `answer_runs` and `citations` for generation trace

## Run Comparison

The dashboard should compare:

- baseline vector retrieval vs improved retrieval
- prompt version A vs prompt version B
- chunking strategy A vs chunking strategy B
- top_k changes
- model changes

The most useful comparison is:

```text
baseline-vector-only -> improved-hybrid -> enterprise-hybrid-rerank
```

Each comparison should show metric movement from X% to Y%, not vague claims.
