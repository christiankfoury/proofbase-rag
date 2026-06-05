# Phase 10 Run Comparison Design

## Goal

Run comparison should make evaluation progress auditable. Each run has the same metadata envelope even when the metrics differ by run type.

## Run Schema

Each exported run contains:

- `run_id`
- `run_name`
- `phase`
- `run_type`
- `timestamp`
- `retrieval_mode`
- `chunking_strategy`
- `top_k`
- `prompt_version`
- `model`
- `total_questions`
- `metrics`
- `failed_questions`
- `notes`

Supported `run_type` values:

- `retrieval_eval`
- `answer_quality_eval`
- `permission_eval`
- `memory_eval`

## Comparisons

### Baseline vs Current

Compares the Phase 6 retrieval baseline with the Phase 7 answer-quality run. This shows that the same retrieval baseline can be evaluated more deeply with answer/citation metrics.

### Vector vs Keyword vs Hybrid

Compares:

- `vector-section`
- `keyword-section`
- `hybrid-section-0.5`

Current conclusion: `vector-section` performed best overall. Hybrid matched all-sources hit and slightly improved MRR but reduced Precision@k.

### Section-Based vs Fixed-Size Chunking

Compares:

- `vector-section`
- `vector-fixed-size`

Current conclusion: fixed-size chunking did not clearly outperform section-based chunking.

## Metrics Displayed

Retrieval:

- any-source hit
- all-sources hit
- expected-source recall
- Precision@k
- MRR

Answer quality:

- answer accuracy
- citation accuracy
- faithfulness/support score
- hallucination rate
- response type accuracy

Permissions:

- permission leakage rate
- blocked-answer accuracy
- unauthorized chunk exposure rate
- restricted citation leakage rate

Memory:

- follow-up detection accuracy
- query rewrite quality
- memory answer accuracy
- memory permission leakage
- hallucination rate on follow-ups

System:

- average retrieval latency when available
- input tokens
- output tokens
- estimated cost when available

## Honesty Rule

Metrics that were not produced by previous evaluation runners remain `pending` or `null`. Phase 10 does not infer or fabricate missing values.
