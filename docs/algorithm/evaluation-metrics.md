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
| `scripts/validate_independent_generalization_suite.py` | Validate locked Phase 47 distributions, source/quote truth, permission pairs, roles, behaviors, scopes, and holdout review metadata. |
| `scripts/run_independent_generalization_eval.py` | Run the 70-case development split or one complete sealed 30-case holdout with approval, budget, hash, clean-tree, and frozen-runtime gates. |

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

The latest Phase 46 permission run reported zero leakage across all tracked leakage metrics.

## Memory Metrics

Defined in `apps/api/app/evaluation/memory_metrics.py`.

| Metric | Meaning |
| --- | --- |
| Follow-up detection accuracy | The follow-up detector fired. |
| Query rewrite quality | The rewritten query retrieved all expected sources. |
| Memory response type accuracy | The response behavior matched the memory question expectation. |
| Memory permission leakage | Memory did not cause unauthorized chunks or citations. |

Memory answer and citation accuracy reuse answer metrics.

Live answer-quality reporting keeps the raw `response_type_accuracy` score comparable, so `answer_with_memory` rows that return the normal API behavior `answer` still receive half credit there. The dedicated memory metric treats that behavior as full credit when memory rewrite, answer, citation, and permission behavior are otherwise correct. Phase 39 live reporting therefore separates memory response-type half-credit into diagnostic notes instead of answer/citation failures.

## Multi-Doc Metrics

Defined in `apps/api/app/evaluation/multi_doc_metrics.py`.

| Metric | Meaning |
| --- | --- |
| Source coverage score | Expected-source recall for multi-doc questions. |
| All required sources cited | Every expected document appeared in citations. |
| Multi-doc summary | Averages answer, citation, source coverage, hallucination, and cost fields over multi-doc rows. |

Multi-doc metrics are especially important because many remaining failures involve missing a secondary source or citing only part of the answer.

## Phase 47 Independent Evaluation

Phase 47 is separate from benchmark `1.1` and the Phase 45/46 probes. Runtime commit `50e149c` was frozen before isolated holdout authoring. The approved holdout was hashed as `10d93cfb...b1afb4f` and run once from evaluation commit `58ed3fc`.

| Metric | Development (n=70) | Holdout (n=30) | Holdout target |
| --- | ---: | ---: | ---: |
| Behavior accuracy | `0.986` | `0.767` | `>=0.900` |
| Expected-source recall | `1.000` | `0.947` | `>=0.900` |
| Required-fact completeness | `0.881` | `0.788` | `>=0.850` |
| Citation document accuracy | `0.979` | `0.842` | `>=0.900` |
| Heuristic hallucination rate | `0.000` | `0.333` | `<=0.050` |
| Unauthorized chunk exposure | `0.000` | `0.000` | `0.000` hard gate |
| Unauthorized chunks reached generation | `0.000` | `0.000` | `0.000` hard gate |
| Memory-as-evidence violations | `0.000` | `0.000` | `0.000` hard gate |

The holdout passed source recall and all hard gates but missed the other portfolio gates. Its 14/30 strict automated pass count is evidence of gaps in ambiguity handling, multi-document coverage, longer memory, and restricted-response classification. Human adjudication also identifies deterministic token-overlap false positives; it does not rewrite the frozen automated artifact.

## Phase 49 Reliable Holdout Measurement

Phase 49 makes one-time holdout execution crash-safe: all cases and dependencies are preflighted before case 1, each completed case is written atomically and journaled immediately, recovery resumes from the first unexecuted case without repeating completed external calls, and final metrics are built only from verified detailed rows. A run cannot be marked complete until its contiguous case records and hash-chained journal are complete.

The blind v3 holdout ran exactly once against frozen runtime `7bbb8b4` and hardened evaluator `3d3706e`. It produced `22/30` at estimated cost `$0.022624`: behavior `0.967`, required-source recall `0.982`, required-fact completeness `0.875`, citation accuracy `0.947`, and heuristic hallucination `0.133`. All permission, generation-boundary, restricted-citation, and memory-as-evidence hard gates remained zero. The hallucination and `27/30` gates were missed, so this is valid fresh evidence with no improvement claim.

Manual review preserved the automated result and separately classified the eight failures as four evaluator-only, three product, and one mixed. No human-adjusted score was published. Provider token counts are unavailable from the evaluated endpoint; persisted token fields are therefore null even though estimated cost is available.

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
| Answer quality | `phase32-expanded-answer-generation-v5` | `phase39-live-query-answer-quality-v8` |
| Permission safety | `phase8-permission-safety` | `phase46-permission-evaluation` |
| Memory | `phase9-memory` | `phase36-memory-evaluation` |

Current metrics from existing artifacts:

| Metric | Current value |
| --- | ---: |
| Precision@k | `0.778` |
| Expected-source recall | `0.950` |
| MRR | `0.965` |
| Answer accuracy | `1.000` |
| Citation accuracy | `1.000` |
| Hallucination rate | `0.000` |
| Permission leakage | `0.000` |
| Memory answer accuracy | `1.000` |

## What The Metrics Prove

They support these claims:

- the benchmark has a known size and category mix
- the system improved on measured retrieval and answer-quality runs
- permission leakage stayed at zero on the evaluated restricted suite
- memory follow-ups are handled correctly on the evaluated suite
- current failed-question counts and diagnostic notes are visible rather than hidden
- a separately authored frozen holdout preserved the measured hard permission and memory-evidence boundaries while exposing generalization gaps

## What The Metrics Do Not Prove

They do not prove:

- production safety under real enterprise documents
- semantic correctness equal to a human reviewer
- perfect hallucination prevention
- real SSO or connector permission parity
- production uploaded-document storage durability, because local approval/indexing is implemented but hosted storage is still future work
- general multi-document planning beyond the tested scenarios
- generalization beyond the one synthetic 30-case holdout, or that human adjudication converts the original automated score

## Cost Notes

Answer runs estimate chat-generation cost from configured model pricing. They exclude:

- embedding cost
- ingestion cost
- infrastructure cost
- Azure hosting cost
- cached-input or batch discounts

Evaluation runners that call OpenAI use explicit approval flags or budget guardrails in later phases.
