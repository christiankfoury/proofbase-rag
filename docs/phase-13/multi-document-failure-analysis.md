# Phase 13: Multi-Document Failure Analysis

## Benchmark

10 MULTI questions in `data/evaluation/benchmark-questions.json`. Each requires synthesis from exactly 2 expected source documents.

## Phase 11 Results (v3 prompt, baseline retrieval)

9 out of 10 questions failed or underperformed.

| Question | Expected Docs | all_sources_hit | response_type | answer_accuracy | Failure Type |
|----------|--------------|-----------------|---------------|-----------------|--------------|
| MULTI-001 | HR-003, IT-002 | 1.0 | not_found | 0.0 | confidence_threshold_downgrade |
| MULTI-002 | IT-001, IT-003 | 1.0 | partial_answer | 0.5 | confidence_threshold_downgrade |
| MULTI-003 | HR-001, HR-002 | 1.0 | partial_answer | 1.0 | confidence_threshold_downgrade |
| MULTI-004 | SALES-002, SALES-003 | 0.5 | partial_answer | 1.0 | missing_secondary_citation |
| MULTI-005 | SALES-001, SALES-002 | 0.0 | partial_answer | 0.0 | missing_secondary_source |
| MULTI-006 | MGR-001, MGR-002 | — | partial_answer | — | confidence_threshold_downgrade |
| MULTI-007 | HR-003, IT-002 | 1.0 | partial_answer | 0.5 | incomplete_synthesis |
| MULTI-008 | HR-001, HR-004 | 1.0 | partial_answer | 0.5 | missing_secondary_citation |
| MULTI-009 | IT-ADMIN-001, IT-001 | 1.0 | partial_answer | 1.0 | hallucination_flag (unsupported inference) |
| MULTI-010 | HR-003, HR-ADMIN-001 | 1.0 | partial_answer | 1.0 | confidence_threshold_downgrade |

## Failure Pattern Summary

| Pattern | Count | Description |
|---------|-------|-------------|
| confidence_threshold_downgrade | 6 | Retrieval succeeded; citation_confidence < 0.7 caused partial_answer or not_found |
| missing_secondary_citation | 2 | Both sources retrieved; model cited only primary source |
| missing_secondary_source | 1 | Vector retrieval missed SALES-002 entirely (rank issue) |
| hallucination_flag | 1 | Correct answer but unsupported inference clause triggered hallucination scorer |

## Phase 13 Fixes Applied

1. **confidence_threshold_downgrade** → loosened thresholds in multi_doc mode (0.3/0.5 instead of 0.5/0.7) + suppressed "Based on limited supporting evidence" prefix

2. **missing_secondary_citation** → grouped context format + v4 prompt requiring citation per contributing document

3. **missing_secondary_source** → query decomposition generates a subquery per domain, ensuring SALES-002 retrieval has a dedicated pass

4. **hallucination_flag** → v4 prompt discourages unsupported inference; multi_doc threshold reduces impact

## Results After Phase 13

Run `python scripts/run_multi_doc_eval.py` to produce current metrics.
Results are saved to `data/evaluation/multi-doc-eval.json`.
