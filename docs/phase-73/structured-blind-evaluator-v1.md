# Structured interpretation and blind comparison: offline implementation

The user authorized this offline successor after V35 stopped at calibration.
Goal: make interpretation uncertainty a software-enforced part of judgments and
remove candidate anchoring from semantic review. This affects evaluation tools
only; no App/API, database, permission, default prompt or provider change.

Decision: two blind claim/coverage judgments, with typed alternative readings and
a deterministic comparator. Both judges see original authorized inputs only.
The evaluator preserves the ordering-v2 references, all 16+3 diagnostic and 32+3
calibration controls, and fresh 16/60 acceptance gates. It cannot submit requests.

Acceptance for this work: implemented request planning, interpretation validation
and reduction, blind comparison and probe checking; meaningful offline negative
controls; a receipt-based component-reuse and complete-path funding assessment;
reviewed changes committed and pushed. Synthetic judgments prove code behavior,
not that a model now gets the disputed case right. No saved failure is repaired.

Non-goals: another ambiguity audit, reference edits, V36 prompt experiment, paid
pilot, reduced output limits, hold release, new holdout authoring or activation.
Stop after publishing the offline implementation and consolidated budget decision.

## Delivered implementation

[Evaluator](../../scripts/structured_blind_evaluator_v1.py) builds four requests:
claims and coverage for judge A, and claims and coverage for judge B. Both plans
are built from the same original inputs before either judgment exists. Neither
judge receives the other's claims, labels or reasons. Coverage keeps the exact
V35 prompt, schema and input partition. Claims use the frozen V35 evidence rubric
with a new structured interpretation schema. The pinned model, high reasoning
effort, and full 8192/4096 claims/coverage limits remain unchanged. There is no
candidate-conditioned review request, provider client, retry or paid entry point.

Each claim retains its exact answer span. A non-ordering claim has one literal
reading; potential ordering requires both action-order and presentation-order
readings, with explicit plausibility decisions and exact contextual witnesses.
Each plausible reading carries its own evidence verdicts and exact source/citation
witnesses. An excluded reading must retain its reason and context witnesses, but
cannot carry a positive support verdict. Context can interpret a claim; it cannot
prove a policy, identity, permission or entitlement.

Code validates all readings before projection. If plausible readings have different
support labels, the complete claim becomes factual unknown / citation unknown,
with empty support witnesses. If context resolves a reading, ordinary evidence
rules apply. Thus clearly unsupported order remains citation missing; supported
order or explanation can remain supported. Two readings that both lack support
cannot use ambiguity to erase that failure. Facts, omissions and other claims are
assessed independently. The disputed reference and all original controls are
unchanged. No case ID, company name or special handling of the word "First" exists
in the evaluator.

The deterministic comparator checks intermediate claims, facts, interpretations,
behavior, relevance and forbidden assertions. Disagreement stays unresolved even
when both judgments produce the same aggregate failure. It never manufactures a
semantic model's "agree" response. Probe checking compares intentionally wrong
candidates only after the blind judgments, preserving all six existing probes.
The original semantic dimensions/overall convention remains; quotation fidelity
and response-type metadata retain separate blocking checks. Permission flags,
unauthorized citations, invalid exact witnesses and malformed outputs cannot earn
candidate success. `target_credit` and `release_eligible` are always false in this
offline implementation, even for a structurally valid candidate pass.

Raw-envelope replay requires all four exact planned requests, settled responses,
the pinned model, valid schemas and distinct response IDs. Copying one response
to impersonate another blind draw fails. This checks structure, not authenticity:
a future live runner must still bind receipts to the spending journal and frozen
execution plan, qualify this complete evaluator and satisfy source review.

## Reuse and consolidated funding decision

[Assessment tool](../../scripts/structured_blind_budget_v1.py) verifies exact request
identity, frozen source bindings, saved response/row hashes and receipt charges.
It identifies **38 reusable coverage components**, 16 diagnostic and 22 calibration,
including coverage in the failed case. That case's covered reporting step and
missing fee remain unchanged; its failed claim judgment is never reused as a pass.
Each component is reusable only for judge A. Judge B still requires a distinct
response. Claims changed schema; old anchored reviews changed architecture; neither
is reusable. **Zero stage acceptances carry over.** Development inspection remains
required for every newly combined result. Fresh confirmation/final cannot reuse
old suites or judgments. Application V6's 14/14 development evidence remains valid
only as development evidence because application code/configuration did not change.

The [saved assessment](../../data/evaluation/conversation-continuation/structured-blind-v1/offline-assessment.json)
reconciles every ledger and the original USD0.14820250 hold. Amounts below are rounded
for readability; the artifact uses Decimal arithmetic. Proxies apply frozen rates
to observed V35 token counts without future cache discounts. Structured output may
cost more; these are planning proxies, not bounds or a promise of success.

| Remaining stage | New requests after reuse | Cost proxy USD |
| --- | ---: | ---: |
| Diagnostic: 16 cases + 3 probes | 60 | 0.70068813 |
| Calibration: 32 cases + 3 probes | 118 | 1.13895523 |
| Fresh isolated confirmation: 16 cases | 64 | 0.61862182 |
| Total qualification | 242 | 2.45826517 |
| Qualification without component reuse | 280 | 2.83587017 |

Cumulative ceiling USD16.77047526; accounted USD10.90614776; remaining USD5.86432750.
Preserving the USD4.50 final-launch floor leaves only USD1.36432750 for qualification.
Qualification plus that floor is approximately **USD6.95826517**, exceeding the
remainder by **USD1.09393767** before contingency. This successor would also require
240 final grader requests rather than 180, plus the unchanged maximum 32 application
calls per case. The floor is not a measured final cost. Exact fresh-input costs and
reservations remain unknown until the required freeze and isolated authoring.

**Decision: no paid execution.** Component reuse does not make the complete path
credibly fundable. No smaller pilot, allowance reduction, retry or top-up is proposed.
The offline delivery is complete; accepted activation remains blocked by unqualified
evaluator behavior and insufficient whole-path funding. Preserve the remaining
funds and V4. A future scope/budget decision must reconcile the complete path again;
the estimated gap alone is not a guaranteed completion price.

## Verification and limitations

`python -B -m unittest scripts.test_structured_blind_evaluator_v1 scripts.test_procedural_ordering_review scripts.test_conversation_blind_review_design`:
36 tests pass with network connection attempts blocked. Twenty new checks cover
interpretation projection, missing and duplicate readings, unknown witness rules,
unchanged negative/reference controls, intermediate disagreement, all original
reviewer probes, exact receipt isolation, component reuse and the budget stop.
Synthetic ordering packets satisfy the disputed reference without waiving the
missing fee; a complete ambiguous answer remains unresolved and earns no success.
These are software tests, not newly measured model results. Saved V35 failure stays
21/22, and historical V34 evidence is unchanged.

Models can still omit a claim, misjudge a reading's plausibility or agree on a wrong
interpretation. Both use the same pinned model: blind inputs remove exposure to a
candidate, not statistical correlation or shared biases. Exact witnesses prove
provenance, not entailment. Natural-language meanings/reasons are preserved for
source inspection; code compares structured decisions, not their semantic validity.
Only full qualification and fresh independent reference validation can establish
whether this architecture works. No human/external adjudication is claimed.

The saved assessment replays with
`python -B -m scripts.structured_blind_budget_v1 --check`. Existing application,
frontend build and paid checks are deliberately not rerun: their implementation
is unchanged and no paid path is funded. New API calls/spending: **0 / USD0**.
Historical references, ledgers and the unrelated request-log edit are preserved.
Future release requirements remain 16+3 diagnostic, 32+3 calibration, fresh16
confirmation, fresh60 with at least48 successes and all safety/citation gates,
source review, accepted activation and committed/pushed results. No gate is waived.

The three new modules compile; 251 local documentation links resolve. Final
semantic review retained the separate response-type gate and its focused check
passes. Complete intended code, test, assessment and documentation review found
no blocking offline-delivery issue; the unmeasured model behavior and funding
block remain explicit. Git whitespace, historical hashes and log preservation
checks pass. The reviewed commit records this complete offline work unit.
