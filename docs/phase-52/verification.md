# Phase 52 Verification

Status: complete on 2026-08-26.

## Promotion Decision

Promoted mode: `semantic_all_remaining` with model `gpt-4.1-mini`, prompt `request_assessment:v2`, and schema `request_assessment.v1`.

The fixed development suite was authored and its thresholds recorded in `design.md` before the first semantic candidate. The Phase 47-49 sealed holdouts were not opened, changed, or rerun.

## Candidate Comparison

| Run | Mode / prompt | Accuracy | Unsafe continues | Legitimate interventions | p95 | Estimated cost | Gates |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `phase52-request-assessment-deterministic-only` | deterministic only | `0.2500` | `24/26` | `3/14` | `0 ms` | `$0.000000` | Failed |
| `phase52-request-assessment-uncertain-only` | uncertain only / v1 | `0.7083` | `12/26` | `0/14` | `3310 ms` | `$0.010697` | Failed |
| `phase52-request-assessment-candidate-v1` | all remaining / v1 | `0.8333` | `1/26` | `6/14` | `2655 ms` | `$0.018364` | Failed |
| `phase52-request-assessment-candidate-v4` | all remaining / v2 | `1.0000` | `0/26` | `0/14` | `2304 ms` | `$0.027628` | Passed |

Candidate v4 also produced zero source-discussion false blocks and zero parser/schema failures. Its mean estimated assessment cost was `$0.000576`, below the predeclared `$0.001` gate. `semantic_uncertain_only` was not promoted because twelve attack cases bypassed semantic assessment and continued.

## Regression Discovery And Remediation

The first full runtime run, `phase52-request-assessment-regression`, scored `114/130`. The semantic classifier was incorrectly treating clear questions about missing, restricted, conflicting, or sensitive subjects as ambiguity or injection. Benchmark expectations and sources were not changed.

Prompt v2 clarified the routing contract, and trusted code added a bounded, visible semantic-contract normalization. It can only convert a clear request into `continue`, which means “proceed to ordinary permission-filtered retrieval”; it cannot change identity, role, project, department, document, chunk, or tool access. Focused final run `phase52-request-assessment-final-subset` passed the two remaining cases `2/2`.

## Full Runtime Regression

Run `phase52-request-assessment-final-regression` exercised the normal `POST /query` path over benchmark `1.1`, sample `130`:

- passed questions: `130/130`; failed questions: `0`
- answer accuracy: `1.000`; citation accuracy: `1.000`; hallucination rate: `0.000`
- clarification, refusal, and not-found accuracy: `1.000`
- assessment statuses: `130` succeeded; `0` failed-safe/parser failures
- routes: `5` deterministic guards and `125` semantic assessments
- actions: `7` clarify and `123` continue
- recorded normalizations: `1` clear information request and `1` searchable named subject
- unauthorized chunks reaching generation: `0`
- answer-generation estimated cost: `$0.070168`
- request-assessment estimated cost: `$0.076819`
- combined estimated cost: `$0.146987`, below the explicit `$0.20` run budget
- mean request-assessment latency: `2030.946 ms`
- actionable submetric issues: `0`; diagnostic notes: `28`

The evaluator disables operational telemetry submission because synthetic evaluation traffic is represented by its committed run artifact and must not be mixed with user traffic. The normal runtime still emits request-assessment telemetry when configured.

## Permission Regression

Run `phase52-permission-evaluation`, benchmark `1.1`, tested `20` restricted questions and `20` authorized retrieval counterparts:

- permission leakage: `0.000`
- unauthorized chunk exposure: `0.000`
- restricted citation leakage: `0.000`
- unauthorized chunks reached generation: `0.000`
- blocked-answer accuracy: `1.000`
- authorized retrieval accuracy: `1.000`
- authorized answer accuracy: `pending` by the evaluator's existing no-extra-generation policy

## Local Verification

- `python scripts/test_phase52_request_assessment.py`
- `python scripts/test_phase39_live_query_answer_quality.py`
- `python scripts/test_phase50_manual_findings.py`
- `python scripts/test_phase46_generalization_remediation.py`
- `python scripts/test_phase48_generalization_remediation.py`
- `python scripts/test_phase38_answer_quality_controls.py`
- `python scripts/validate_benchmark.py`
- `python -m compileall apps scripts`
- `python scripts/export_dashboard_data.py`
- `docker compose config --quiet`
- Next.js production build
- `git diff --check`

## Limitations

- The 48 cases are visible development cases used for remediation, not a sealed or independent security evaluation.
- A model-based routing layer adds latency, estimated cost, and provider availability dependency.
- Fail-safe behavior deliberately withholds retrieval when assessment is unavailable; production availability targets are not established.
- Request assessment is neither authorization nor evidence sufficiency. Phase 53 must inspect only permission-filtered chunks before normal generation.
