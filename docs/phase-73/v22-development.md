# Phase 73: CAD-bounded evaluator continuation

## Goal and limits

Produce a defensible new full measurement after resolving the general evaluator
and reference-construction concerns exposed by v5. The affected surface is
evaluation evidence and its eventual Dev/Admin publication. No application,
retrieval, permission, database-schema or scoring-reducer change is planned.
Original v4/v5 results, all failed evidence and unrelated request-log edits remain
unchanged. A valid full measurement may miss the 48/60 target; never manufacture
a pass or restart an exposed suite.

The user's 2026-10-01 CAD 14.32 continuation funds at most USD 9 new calls. Use
CAD 1.59/USD for conservative budgeting (CAD 14.31), without reusing the previous
USD 0.12176315 balance. This is a chosen buffer above recent indicative exchange
data, not a billing quote. [Bank of Canada reference](https://www.bankofcanada.ca/rates/exchange/daily-exchange-rates/).
The new journal preserves the original USD 9.87823685 prefix; its combined limit
is USD 18.87823685. Historical total: USD 20.73393762 and 3,474 attempts. All
historical unknown reservations remain retained. New unknowns stop execution.

## General failure hypotheses

- Contextual address to a role supplied in the question does not independently
  verify identity. Explicit verification, access or newly assigned duties still
  need evidence. V22 clarifies this boundary without relaxing policy support.
- Attribution to an authorized document needs its actual title, which the former
  text-only grader input omitted. V22 accepts title metadata bound to the saved
  authoritative evidence. Forged metadata invalidates the judgment; titles never
  establish policy rules by themselves. The eventual capture must obtain titles
  from the database, not trust answer-supplied citation titles.
- Required facts must match the question's requested scope. Fresh authoring and
  independent validation must map every material reference clause to an explicit
  requested part or a necessary condition. Do not bundle an unrequested general
  rule into a concrete-outcome question. Existing sealed facts are unchanged;
  coverage scoring still requires every supplied fact in full.

The v21 schema, reducers, quotation metric, pinned model, medium reasoning,
4,096-output-token cap and 180-second timeout remain unchanged. A length-limited
empty review is still invalid and earns no credit, with no retry. This work does
not guarantee that future model outputs are valid or correct.

## Stages and acceptance

1. Eight separately composed synthetic development controls plus the unchanged
   three reviewer probes: maximum 27 calls, USD 1.00 hard stage cap, early stop
   on a diagnostic mismatch. Positive/negative cases cover role context versus
   verified identity/permission, true/wrong attribution, titles versus policy
   entitlements, field-list scope and a concrete timing conclusion.
2. Only after exact diagnostic labels and clean source inspection: unchanged
   24-case calibration plus three probes, maximum 75 calls, USD 1.50 cap.
3. Only after full clean calibration: freeze before isolated new 16-case
   confirmation authoring and independent validation; execute once with 48 calls
   and a separately declared cap. Require 16/16 and clean source inspection.
4. Only after qualification: new runtime/config/index freeze and separate fresh
   60-case author/validator contexts. Reserve adequate remaining allowance before
   launch, execute once, preserve all outcomes and publish the full result or an
   honest interruption. No selective retries, label changes or historical-score
   replacement. Maintain the same composite and zero-disclosure safety gate.

Stage caps are enforced before each request, using conservative reservations and
settled cache-aware usage. The diagnostic's token-based worst-case sum is USD
3.4615975, above its USD 1.00 stage cap; the cap can stop it before completion.
This is a bounded diagnostic, not a promise to spend its theoretical maximum.
Maintain sufficient allowance for the full measurement instead of consuming it
on unchanged candidates. Continue only with a source-supported failure hypothesis.

## Verification and current position

Preparation working diff on main after `8af62f76`: seven offline tests pass,
including full saved-response/reducer replay, diagnostic early stopping, stage
reservation blocking, reference consistency, forged metadata rejection, exact CAD
policy and immutable historical accounting/shared-cap checks. Python compilation
passes for all five new modules. Diagnostic dry-run passes: 27-call bound, no
provider retries, separate unused folder and unchanged accounting prefix.
These tests reuse historical responses only as transport/reducer fixtures; they
are not a live v22 qualification result. No paid call has been made in this cycle.

Review the complete intended diff before committing the preparation. Next action:
`python scripts/quality_development_v22.py execute --stage diagnostic --allow-external-ai`.
Preserve the result, inspect every claim/fact/reviewer decision and run offline
replay before any qualification gate is approved. Frontend build is deferred until
its published data changes; application tests are reused because runtime is unchanged.
