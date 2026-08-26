# Phase 53 Verification

Status: complete on 2026-08-26.

## Promotion Decision

Promoted mode: `hybrid` with model `gpt-4.1-mini`, prompt `evidence_assessment:v2`, schema `evidence_assessment.v1`, no provider retry, and a bounded 15-second provider timeout.

The gate runs after permission-filtered retrieval and before ordinary generation in both `POST /query` and `POST /query/stream`. The Phase 47-49 sealed holdouts were not opened, changed, or rerun.

## Mode Comparison

| Run | Mode | Accuracy | Unsafe answers | Semantic calls | p95 | Estimated cost | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `phase53-evidence-assessment-deterministic-only` | Deterministic only | `20/30` | `6/13` | `0` | `0 ms` | `$0.000000` | Rejected |
| `phase53-evidence-assessment-semantic-always-v1` | Semantic always | `29/30` | `0/13` | `30` | `4292 ms` | `$0.019625` | Passed gates but not selected |
| `phase53-evidence-assessment-hybrid-v11` | Hybrid | `29/30` | `0/13` | `19` | `4381 ms` | `$0.015036` | Promoted |

Hybrid matched semantic-always quality while avoiding 11 model calls and reducing estimated suite cost by about 23%. The one accepted miss, `EA-MULTI-002`, was a conservative `partial_answer` on complete authorized evidence; the predeclared multi-document gate was `>=4/5` and passed.

The promoted fixed-suite run also recorded:

- forbidden or inaccessible-source disclosures: `0`
- unauthorized or invented references in returned assessments: `0`
- parser/schema/contract failures: `0`
- partial-evidence actions: `5/5`
- complete multi-document actions: `4/5`
- conflict actions: `4/4`
- mean estimated assessment cost: `$0.000501`; total: `$0.015036`

Earlier candidate and runtime runs are retained as development evidence. They exposed nano-model quality loss, compact-schema latency, transient timeout handling, over-filtered generation context, source-discussion materiality, and redundant-field inconsistencies. Benchmark answers, behaviors, sources, and the fixed 30-case suite were not changed.

## Full Runtime Regression

Run `phase53-live-query-regression-v5` exercised the normal `POST /query` path over benchmark `1.1`, sample `130`:

- passed questions: `130/130`; failed questions: `0`
- answer accuracy: `1.000`; citation accuracy: `1.000`; hallucination rate: `0.000`
- refusal, not-found, and clarification accuracy: `1.000`
- evidence-assessment fail-safe count: `0`
- evidence routes: `120` hybrid semantic, `3` deterministic source-instruction safety, `7` pre-retrieval stops with no evidence assessment
- evidence actions: `82` answer, `2` partial answer, `39` not found, and `7` pre-retrieval stops
- bounded contract normalizations: `3`, all `assessment_contract_invalid`; every referenced ID was validated against the authorized input
- unauthorized chunks reaching generation: `0`
- answer-generation estimated cost: `$0.066771`
- request-assessment estimated cost: `$0.077049`
- evidence-assessment estimated cost: `$0.136930`
- combined estimated cost: `$0.280750`, below the explicit `$0.45` run budget
- mean request-assessment latency: `2020.692 ms`; mean evidence-assessment latency: `3411.041 ms`
- actionable submetric issues: `0`; diagnostic notes: `28`

The evaluator disables operational telemetry submission for synthetic evaluation traffic. Normal runtime still emits evidence-assessment telemetry when a destination is configured.

## Permission Regression

Run `phase53-permission-evaluation`, benchmark `1.1`, tested `20` restricted questions and `20` authorized retrieval counterparts:

- permission leakage: `0.000`
- unauthorized chunk exposure: `0.000`
- restricted citation leakage: `0.000`
- unauthorized chunks reached generation: `0.000`
- blocked-answer accuracy: `1.000`
- authorized retrieval accuracy: `1.000`
- authorized answer accuracy: `pending` under the evaluator's no-extra-generation default

The permission evaluator completed successfully. Optional platform-telemetry submissions reported network errors; those failures did not affect local evaluation rows or the committed permission metrics.

## Verification Commands

- `python scripts/test_phase53_evidence_assessment.py`
- `python scripts/test_phase52_request_assessment.py`
- `python scripts/test_phase39_multi_doc_orchestration.py`
- `python scripts/test_pre_phase39_guardrails.py`
- `python scripts/run_evidence_assessment_eval.py --mode hybrid --allow-external-ai ...`
- `python scripts/run_evidence_assessment_eval.py --mode semantic_always --allow-external-ai ...`
- `python scripts/run_phase39_live_query_answer_quality.py --allow-external-ai --budget-usd 0.45 ...`
- `python scripts/run_permission_eval.py --allow-external-embeddings ...`
- `python scripts/validate_benchmark.py`
- `python -m compileall apps scripts`
- `python scripts/export_dashboard_data.py`
- `docker compose config --quiet`
- Next.js production build
- `git diff --check`

## Limitations

- The 30 fixed cases are visible development cases used for remediation, not a sealed or independently authored evaluation.
- The semantic gate adds material latency, cost, and provider availability dependency. The live benchmark mean was `3411.041 ms` before generation; production latency and availability objectives are not established.
- A 15-second timeout fails safely, which protects integrity but can temporarily withhold an otherwise answerable response.
- Deterministic and semantic normalization are integrity controls, not authorization. Identity, tenant, project, department, role, document, and chunk access remain separate preconditions.
- This phase provides no new generalization claim because the sealed Phase 47-49 holdouts remained untouched.
- Post-generation semantic claim and source-instruction validation remains Phase 54 work.
