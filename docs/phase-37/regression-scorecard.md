# Phase 37 Regression Scorecard

Generated from `data/evaluation/regression-scorecard.json`.

## Summary

Phase 37 publishes the measured portfolio story without hiding failures. The scorecard compares expanded baseline runs against the latest measured retrieval, answer-quality, permission, and memory runs.

## Run Evidence

| Area | Baseline Run | Current Run | Sample Notes |
| --- | --- | --- | --- |
| Retrieval | `phase32-expanded-retrieval` | `phase33-vector-lexical-rerank-top3` | Both use benchmark v1.1 over 130 questions. |
| Answer quality | `phase32-expanded-answer-generation-v5` | `phase35-citation-alignment-v7` | Both use benchmark v1.1 over 130 questions. |
| Permission safety | `phase8-permission-safety` | `phase36-permission-evaluation` | Current suite expands from 10 legacy restricted questions to 20 benchmark v1.1 restricted questions. |
| Conversation memory | `phase9-memory` | `phase36-memory-evaluation` | Current suite expands from 5 legacy memory questions to 20 benchmark v1.1 memory questions. |
| Memory permission boundary | n/a | `phase36-memory-permission-boundary` | Adds 5 focused probes where previous turns mention restricted topics. |

## Metric Deltas

| Metric | Baseline | Current | Delta | Target | Status |
| --- | ---: | ---: | ---: | --- | --- |
| Source Recall | 0.978 | 0.950 | -0.028 | >= 0.950 | Pass |
| Precision@k | 0.616 | 0.778 | +0.162 | 0.750-0.850 | Pass |
| MRR / First Source Rank | 0.954 | 0.965 | +0.011 | >= 0.950 | Pass |
| Answer Accuracy | 0.850 | 0.919 | +0.069 | >= 0.900 | Pass |
| Citation Accuracy | 0.844 | 0.950 | +0.106 | >= 0.920 | Pass |
| Hallucination Rate | 0.205 | 0.000 | -0.205 | <= 0.080 | Pass |
| Permission Leakage Rate | 0.000 | 0.000 | 0.000 | = 0.000 | Pass |
| Memory Answer Accuracy | 1.000 | 1.000 | 0.000 | >= 0.900 | Pass |

## Failure Reasons

Current answer run: `phase35-citation-alignment-v7`.

Failed questions: 16.

| Failure Type | Count |
| --- | ---: |
| Ambiguity failure | 5 |
| Incomplete answer | 2 |
| Multi-document failure | 3 |
| Retrieval miss | 1 |
| Unsupported answer | 2 |
| Wrong citation | 3 |

Failed question IDs: `MULTI-004`, `MULTI-005`, `MULTI-007`, `MULTI-008`, `MEM-004`, `MULTI-013`, `MULTI-014`, `MULTI-017`, `MULTI-020`, `AMB-006`, `AMB-007`, `AMB-008`, `AMB-009`, `AMB-010`, `ADV-001`, `ADV-005`.

## Supported Portfolio Claims

- Built an evaluation-driven enterprise RAG platform with permission-aware retrieval, citation verification, conversation-memory evaluation, adversarial safety tests, and benchmark dashboard evidence.
- Expanded the benchmark to 130 questions across factual, multi-document, restricted-access, missing-information, memory, ambiguous, prompt-injection, and conflicting-source scenarios.
- On benchmark v1.1 answer runs, improved answer accuracy from 0.850 to 0.919, citation accuracy from 0.844 to 0.950, and hallucination rate from 0.205 to 0.000.
- Maintained 0.000 permission leakage on the expanded 20-question permission suite and 0.000 memory-permission leakage on the 20-question memory suite plus 5 focused boundary probes.

## Limitations

- Legacy permission and memory baselines use smaller pre-expansion suites, so their deltas should be read as coverage expansion plus safety preservation, not a same-sample accuracy comparison.
- The current answer-quality run still has 16 failed questions; the dashboard keeps failure counts and failure reasons visible.
- Metrics use deterministic and heuristic evaluators over a synthetic portfolio corpus, not production traffic or human-judge labels.
- Uploaded-document indexing, production SSO, real enterprise connectors, and hosted Azure deployment are not claimed as completed.
