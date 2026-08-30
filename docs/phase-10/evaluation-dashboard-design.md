# Phase 10 Evaluation Dashboard Design

## Purpose

The Phase 10 dashboard presents the Proofbase as an evaluation-driven enterprise RAG system. It does not create new metrics. It displays real outputs from Phase 6 retrieval experiments, Phase 7 answer-quality evaluation, Phase 8 permission evaluation, and Phase 9 memory evaluation.

The dashboard is designed for guided demos. It should make the product story visible in a few minutes:

- Retrieval was benchmarked across vector, keyword, hybrid, section-based, and fixed-size configurations.
- Answer quality, citation accuracy, faithfulness, and hallucination behavior were measured.
- Permission safety was evaluated against restricted-source benchmark cases.
- Conversation memory was tested on follow-up questions with permission-safe query rewriting.

## Data Source

Dashboard data is exported from existing reports:

- `docs/phase-6/evaluation-results.md`
- `docs/phase-7/evaluation-results.md`
- `docs/phase-7/failed-question-analysis.md`
- `docs/phase-8/permission-evaluation-results.md`
- `docs/phase-9/memory-evaluation-results.md`
- `docs/phase-9/failed-memory-question-analysis.md`

The export script writes:

- `data/evaluation/dashboard-summary.json`
- `data/evaluation/eval-runs/*.json`
- `data/evaluation/failed-questions/failed-questions.json`

## Pages

### Evaluation Overview

Shows headline cards for retrieval hit rate, Precision@k, MRR, answer accuracy, citation accuracy, hallucination rate, permission leakage rate, and memory accuracy.

### Run Comparison

Shows all exported runs in one table. This page compares retrieval-only experiments with answer, permission, and memory evaluation runs without pretending all run types have the same metrics.

### Failed Questions

Shows the failed benchmark questions exported from the failed-question reports. This becomes the next improvement backlog.

### Retrieval Experiments

Shows Phase 6 vector, keyword, hybrid, section-based, and fixed-size retrieval results. The dashboard explicitly states that hybrid did not clearly outperform vector-only retrieval on the current benchmark.

### Permission Safety

Shows Phase 8 permission leakage, unauthorized chunk exposure, restricted citation leakage, blocked-answer accuracy, and authorized source-access checks.

### Memory Evaluation

Shows Phase 9 follow-up detection, query rewrite quality, memory answer accuracy, memory citation accuracy, memory permission leakage, and hallucination rate on follow-ups.

## Design Principles

- Keep the UI quiet and information-dense.
- Use cards only for metrics and tables for comparisons.
- Do not add fake charts or placeholder values.
- Mark unavailable values as `pending`.
- Show what got worse as well as what improved.

## Current Limitation

The dashboard currently reads from a FastAPI endpoint backed by exported JSON. It does not yet use database-backed evaluation history.
