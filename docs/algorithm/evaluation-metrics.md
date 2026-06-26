# Evaluation Metrics

The evaluation system makes the RAG behavior measurable. It is not a human judge, and it is not production monitoring. It is a deterministic benchmark suite over a synthetic enterprise corpus.

## Benchmark Shape

The main benchmark is `data/evaluation/benchmark-questions.json`.

Current benchmark metadata:

| Field | Value |
| --- | --- |
| Benchmark version | `1.1` |
| Question count | 130 |
| Source corpus | `data/synthetic-documents` |

Category breakdown from the scorecard:

| Category | Count |
| --- | ---: |
| simple_factual | 30 |
| multi_document | 20 |
| permission_restricted | 20 |
| missing_information | 20 |
| conversation_memory | 20 |
| ambiguous | 10 |
| prompt_injection | 5 |
| conflicting_source | 5 |

Each question usually includes:

- question ID
- question type
- difficulty
- user role
- question text
- previous turns, when memory is required
- expected behavior
- expected answer
- expected source documents
- expected source section or quote
- allowed documents
- notes

## Main Evaluation Runners

| Runner | Purpose |
| --- | --- |
| `scripts/run_retrieval_experiments.py` | Compare retrieval-only configurations. |
| `scripts/run_answer_quality_eval.py` | Run retrieval plus generation and score answer quality. |
| `scripts/run_permission_eval.py` | Test restricted questions for leakage and refusal behavior. |
| `scripts/run_memory_eval.py` | Test follow-up detection, rewrite quality, answer quality, and memory permission leakage. |
| `scripts/run_multi_doc_eval.py` | Compare baseline and multi-doc mode on multi-document questions. |
| `scripts/export_dashboard_data.py` | Combine result artifacts into dashboard summary JSON and scorecard data. |
| `scripts/validate_benchmark.py` | Validate benchmark schema and source references. |

Later phase-specific runners wrap these same ideas with fixed run IDs, prompt versions, retrieval modes, budgets, and output paths.

## Retrieval Metrics

Defined mostly in `apps/api/app/evaluation/metrics.py`.

| Metric | What it means | What it does not prove |
| --- | --- | --- |
| Any-source hit | At least one expected document appeared. | It may still miss other required documents. |
| All-sources hit | Every expected document appeared. | It does not prove the exact supporting sentence was present. |
| Expected-source recall | Fraction of expected documents retrieved. | It is document-level, not claim-level. |
| Precision@k | Share of top-k chunks whose document is expected. | It can be high while a required secondary source is missing. |
| MRR | How high the first expected source appears. | It ignores later required documents. |

Current measured retrieval reference:

| Run | Sample | Precision@k | Expected-source recall | MRR |
| --- | ---: | ---: | ---: | ---: |
| `phase33-vector-lexical-rerank-top3` | 130 | `0.778` | `0.950` | `0.965` |

## Answer Metrics

Defined in `apps/api/app/evaluation/answer_metrics.py`.

| Metric | What it means | How it is scored |
| --- | --- | --- |
| Answer accuracy | Whether the generated answer overlaps expected answer terms. | Full credit at overlap >= `0.65`, half at >= `0.4`. |
| Citation accuracy | Whether citations include expected source documents. | Full if all expected docs cited, half if some cited. |
| Faithfulness | Citation confidence score. | Uses heuristic citation validation. |
| Hallucination rate | Whether unsupported claims exist or citation confidence is too low. | `1.0` for flagged answer, `0.0` otherwise. |
| Response type accuracy | Whether behavior matches expected behavior. | Uses response type to behavior mapping. |
| Refusal accuracy | Whether restricted questions produce `refuse_no_access`. | Only applies to restricted questions. |
| Not-found accuracy | Whether missing-information questions produce `not_found`. | Only applies to missing-information questions. |
| Clarification accuracy | Whether ambiguous questions produce `clarify`. | Only applies to ambiguity questions. |

These are useful regression signals. They are not equivalent to expert human answer review.

## Permission Metrics

Defined in `apps/api/app/evaluation/permission_metrics.py`.

| Metric | Meaning |
| --- | --- |
| Unauthorized chunk exposure | Expected restricted document appeared in retrieved chunks for an unauthorized role. |
| Restricted citation leakage | Expected restricted document appeared in citations for an unauthorized role. |
| Permission leakage | Max of chunk exposure and citation leakage. |
| Blocked-answer accuracy | Unauthorized restricted question returned `refuse_no_access`. |
| Authorized retrieval accuracy | An authorized role can retrieve the restricted source. |

The latest Phase 38 permission run reported zero leakage across all tracked leakage metrics.

## Memory Metrics

Defined in `apps/api/app/evaluation/memory_metrics.py`.

| Metric | Meaning |
| --- | --- |
| Follow-up detection accuracy | The follow-up detector fired. |
| Query rewrite quality | The rewritten query retrieved all expected sources. |
| Memory response type accuracy | The response behavior matched the memory question expectation. |
| Memory permission leakage | Memory did not cause unauthorized chunks or citations. |

Memory answer and citation accuracy reuse answer metrics.

## Multi-Doc Metrics

Defined in `apps/api/app/evaluation/multi_doc_metrics.py`.

| Metric | Meaning |
| --- | --- |
| Source coverage score | Expected-source recall for multi-doc questions. |
| All required sources cited | Every expected document appeared in citations. |
| Multi-doc summary | Averages answer, citation, source coverage, hallucination, and cost fields over multi-doc rows. |

Multi-doc metrics are especially important because many remaining failures involve missing a secondary source or citing only part of the answer.

## Dashboard Export

`scripts/export_dashboard_data.py` reads phase reports and JSON artifacts, then writes:

- `data/evaluation/dashboard-summary.json`
- per-run JSON files under `data/evaluation/eval-runs`
- failed-question summaries under `data/evaluation/failed-questions`
- `data/evaluation/regression-scorecard.json`

The dashboard export adds sample size, pass/fail counts, benchmark version, run timestamp, and category breakdown where available.

## Current Scorecard Story

| Area | Baseline | Current |
| --- | --- | --- |
| Retrieval | `phase32-expanded-retrieval` | `phase33-vector-lexical-rerank-top3` |
| Answer quality | `phase32-expanded-answer-generation-v5` | `phase38-answer-quality-remediation-v8` |
| Permission safety | `phase8-permission-safety` | `phase38-permission-evaluation` |
| Memory | `phase9-memory` | `phase36-memory-evaluation` |

Current metrics from existing artifacts:

| Metric | Current value |
| --- | ---: |
| Precision@k | `0.778` |
| Expected-source recall | `0.950` |
| MRR | `0.965` |
| Answer accuracy | `0.975` |
| Citation accuracy | `0.969` |
| Hallucination rate | `0.000` |
| Permission leakage | `0.000` |
| Memory answer accuracy | `1.000` |

## What The Metrics Prove

They support these claims:

- the benchmark has a known size and category mix
- the system improved on measured retrieval and answer-quality runs
- permission leakage stayed at zero on the evaluated restricted suite
- memory follow-ups are handled correctly on the evaluated suite
- remaining failures are visible rather than hidden

## What The Metrics Do Not Prove

They do not prove:

- production safety under real enterprise documents
- semantic correctness equal to a human reviewer
- perfect hallucination prevention
- real SSO or connector permission parity
- uploaded-document retrieval, because uploaded indexing is not implemented yet
- general multi-document planning beyond the tested scenarios

## Cost Notes

Answer runs estimate chat-generation cost from configured model pricing. They exclude:

- embedding cost
- ingestion cost
- infrastructure cost
- Azure hosting cost
- cached-input or batch discounts

Evaluation runners that call OpenAI use explicit approval flags or budget guardrails in later phases.
