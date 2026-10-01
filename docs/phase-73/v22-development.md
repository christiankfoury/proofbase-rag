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

Preparation was reviewed, committed and pushed as `214645dd`. Frontend build is
deferred until its published data changes; application tests are reused because
runtime is unchanged.

## Preserved diagnostic and v23 clarification

V22 stopped at its third case: 2/3 exact, nine settled calls, USD 0.109716.
[Source inspection](v22-diagnostic-source-review.md) confirms that correct title
attribution was accompanied by invalid metadata IDs/title text in exact-witness
fields. The strict validator rejected them correctly; the model reviewer did not
identify the contract error. Five cases and all probes remain unexecuted.
New allowance remaining: USD 8.890284; cumulative total USD 20.84365362,
3,483 attempts. No unknown outcome or retry.

V23 clarifies that attribution metadata is explained in the claim reason, while
source/citation witnesses may contain only their respective text IDs and literal
text substrings. It inherits the same strict parser, metadata binding, schema,
scoring reducers and model configuration. The same eight development references
and three probes are copied unchanged into a new one-shot stage; these are
development controls, never fresh holdout claims. Bounds remain 27 calls/USD 1.00
for diagnostics, then 75 calls/USD 1.50 for the unchanged full calibration.

Separate v23 confirmation tooling and neutral author/validator briefs are prepared
but no fresh cases are authored before qualification and freeze. Its 16-case
stage cap is USD 1.20/48 calls. The validator must explicitly record the
question/reference-scope check for every case, and title metadata must exactly
match the authoritative evidence mapping. No former holdout content is provided.

V23 preparation verification: eleven offline controls pass (seven development/
accounting controls, saved 16-case confirmation replay, failed-development gate,
scope-review requirement and forged title mapping); compilation and diagnostic
preflight pass. All prior v22 requests, judgments and costs replay exactly. The
new stage's theoretical token sum is USD 3.4958925; its hard cap remains USD 1.00.
Semantic review found no blocking preparation issue. Next: the one-shot v23
diagnostic, followed by source inspection; qualification is not yet established.

V23 diagnostic passed 8/8 plus 3/3 probes with clean
[source inspection](v23-diagnostic-source-review.md) and exact offline replay.
It used 27 settled calls and USD 0.31000450. Across this new allowance, 36 calls
cost USD 0.41972050, leaving USD 8.58027950. Cumulative history is 3,510 attempts
and USD 21.15365812. Next: unchanged 24-case/three-probe calibration, capped at
75 calls and USD 1.50; qualification is still pending.

Full v23 calibration now passes 24/24 and 3/3 probes with clean
[source inspection](v23-calibration-source-review.md) and offline replay. All 75
calls settled at USD 0.6685975. New allowance spending is USD 1.08831800 across
111 calls; USD 7.91168200 remains. Cumulative history: 3,585 attempts and
USD 21.82225562. No retries or new unknown outcomes. Next: commit the clean
calibration, freeze v23, then isolated fresh 16-case confirmation (48 calls,
USD 1.20 stage cap). The separate [v6 preparation](v6-measurement-preparation.md)
is committed/pushed as `f13c9e8f`; it makes no qualification or application claim.
