# Bounded scenario calculation

Authorized 2026-10-02: implement only priority one of the
[structural decision](reliability-structural-decision.md), starting at `918822a1`.
App sync/stream callers must use original-request operands and authorized table
rows, then independently recheck the complete calculation and rendered answer.
No policy amounts, document IDs or captured-case identifiers in runtime code.

Acceptance declared before implementation: replay captured case 01 through both
HTTP callers; add independently worded below/above/equal and grouped-decimal
cases, wrong currency/sign/unit, multiple amounts, false-premise wording, partial
request matches, memory contamination, duplicate/conditional rules, altered
provenance, unauthorized roles and project/department isolation controls. Verify
unsupported inputs still take existing guarded paths. Prove the calculation uses
no semantic evidence, generation, numeric-provenance or repair response.

Scope: a complete, bounded purchase-question grammar and a three-column category
table with a per-purchase limit and a literal approval-above-limit rule. Preserve
security assessment, retrieval filtering, citations and existing fallback behavior.
Stop rather than broaden interpretation, add model calls or relax a guard. No
paid calls, prompt versions, evaluator work, false-premise or geographic changes.
Historical evidence and the unrelated tracked request log remain untouched.

## Implemented boundary

[Calculator](../../apps/api/app/reasoning/scenario_calculation.py), called by
[both query routes](../../apps/api/app/main.py), runs after request security and
authorized retrieval, before semantic evidence assessment. It accepts these
complete case-insensitive ASCII forms, with no unmatched prefix/suffix:

- `My {category} purchase {would cost|costs} {currency} {amount}. Does that category's standard limit trigger {approver} approval for this purchase?`
- `For my {category} purchase of {currency} {amount}, does the category's standard limit require {approver} approval?`

Categories contain at most six alphabetic words separated by spaces/hyphens
(64 characters); approvers at most three space-separated words (32 characters).
Amounts are unsigned, at most 12 integer digits, optionally correctly grouped by
commas, with at most two decimal places. Zero is supported; negatives, refunds,
currency conversion, multi-amount questions and further clauses decline this path.
The currency is a matching three-letter unit code, not an ISO/FX interpretation.

An authorized Markdown table must have exactly the headers `Category`, `Standard
Limit`, `Approval Required`, a valid separator and one exact category row. Its
cells must fully match `{currency} {amount} per purchase` and `{approver} approval
above limit`. Values and identities come from retrieval. Duplicate rows (even
identical), duplicate chunk IDs, competing category statements, prose preambles,
recognized table qualifications, unknown units/operators and extra rule-cell
conditions decline. This conservative screening is **not** a semantic proof that
all prose elsewhere has no exceptions. The answer therefore states only the
quoted row's strict `>` comparison, explicitly withholding purchase approval and
any waiver of other requirements. Interpreting broader applicability, precedence,
exceptions or arbitrary phrasing still belongs to the existing reasoning path;
no blacklist expansion was used to admit broader requests.

A frozen internal record binds the original question hash and input/category
spans, decimal operand, source identity/hash/row span, currency, limit, approver,
operator, result and effective role/project/department. Memory/rewrite text cannot
provide an operand. The evidence assessment attributes **only the policy rule**
to the source. The answer labels the amount as user-supplied and cites the exact
row; existing citation formatting and confidence calculation remain in use.

Finalization independently reconstructs the record from the original question
and currently authorized chunks, then requires the entire candidate to equal the
fixed rendering. Changed spans, operator, input, rule, answer, citation, access,
scope or role fail closed without repair. Neither zero tokens nor a serialized
model-supplied label establishes provenance. No new public response fields, data
model, prompt versions or evaluator rules were introduced; route/reason enums
identify the new deterministic decision. Tenant filtering remains upstream in
retrieval, and membership/role/project/department checks remain in place.

## Before / after and verification

The preserved [live-v2 case](../../data/evaluation/application-reliability-live-v2/run/check-01.json)
asked about a user-supplied USD 217 office-supplies purchase and retrieved the USD
300-per-purchase row. Historically, assessment wrongly cited the purchase operand
as a policy fact; generation made the right comparison; validation omitted its
required numeric provenance and abstained. Replaying those saved responses through
the pre-change callers at `918822a1` also abstained, but under current v4 the old
v3 response fails schema validation. This distinction is preserved in
[before.json](../../data/evaluation/scenario-calculation/before.json); it is not a
new live measurement of v4.

[After.json](../../data/evaluation/scenario-calculation/after.json) records both
real HTTP callers returning the same bounded comparison: USD 217 does not exceed
the cited USD 300 row, so that row's above-limit condition is not triggered.
Each uses zero evidence-assessment, generation and validation provider stubs;
request assessment still uses one captured response and retrieval uses saved
authorized chunks. No model response supplies numeric provenance. The artifact
includes the typed calculation as JSON for inspection. Recorded historical usage
in the baseline is replayed metadata, **not new spending**.

Fresh checks on this working diff (baseline `918822a1`):

| Command | Result / evidence boundary |
| --- | --- |
| `python scripts/test_scenario_calculation.py --record after.json` | 13 methods pass, 5.325 s; TestClient invokes `/query` and `/query/stream`, including actual finalization and streamed answer/metadata parity. Provider network transports are blocked. |
| `python scripts/test_reliability_remediation_v3.py` | 17 methods pass; saved failure contracts, telemetry and payload regressions retained. |
| `python scripts/test_reliability_remediation_v2.py` | 25 methods pass; unsupported numeric provenance, citations, conditional claims and budget bounds retained. |
| `python scripts/test_application_reliability.py` with `EVIDENCE_ASSESSMENT_PROMPT_VERSION=v2`, `POST_GENERATION_VALIDATION_PROMPT_VERSION=v2` | 30 methods pass, including nested request/evidence/claim, permission, memory, multi-document and frozen-history checks; the two environment overrides are compatibility fixtures, not configuration changes. |
| `python scripts/test_reliability_v3_custody.py` | Four frozen live-v2 custody/accounting/tampering methods pass. |
| `python -m py_compile apps/api/app/main.py apps/api/app/reasoning/scenario_calculation.py apps/api/app/reasoning/evidence_assessment.py apps/api/app/reasoning/post_generation_validation.py scripts/test_scenario_calculation.py` | Pass. |

New fixtures exercise EUR 125/620 against EUR 480, equality, zero, one-cent
boundaries, grouped decimals and a different category/approver with CAD 1,730.25.
Negatives cover false-premise wording, missing operands, wrong currency/sign/unit,
two asks, incomplete grammar, contradictory/conditional rows and stale memory.
Both callers reject altered final proofs and preserve request-attack and project
membership denial. Retrieval fixtures apply real role predicates and scope
filters; spoofed requested roles cannot elevate the effective principal. Fixed
rendering cannot follow source instructions or drop citations. Zero-usage ordinary
answers retain the numeric guard. These are development regressions, not a sealed
holdout or overall success-rate measurement.

Database retrieval, production identity and embeddings are seams in these tests;
no claim of a fresh PostgreSQL/tenant-isolation integration run. No frontend build
was needed: the public shape/UI is unchanged. No paid diagnostics, full evaluation
or evaluator qualification ran. Existing request assessment and retrieval may
still incur calls in live use; the entire query is not claimed to be free.

## Review and handoff

Semantic review checked the complete intended diff, original-request binding,
permission placement, citation provenance, finalization failure paths and source
values. Review hardened duplicate chunk-ID rejection and added role/access/scope,
operator and span tampering regressions. The final focused suite and compilation
pass; earlier shared passes remain valid (only a docstring and new tests changed
after them). The harness uses a fresh real in-memory rate limiter per fixture so
the batch does not exhaust a shared test principal's request quota; production
admission controls are unchanged. Historical custody passes, old artifacts remain
unmodified and the unrelated tracked request log is excluded.

Stopping rule met for the declared grammar: captured and independent supported
cases need no model-generated provenance, negative boundaries stay guarded, and
sync/stream finalization verifies the same record. Do not broaden the grammar to
recover semantic cases or start priorities two/three. Live request-routing and
retrieval reachability remain unmeasured; a future explicitly authorized small
diagnostic could check the supported forms, exact boundary and guarded fallback,
with fresh pricing/payload bounds. **No calls or spending now: USD 0; remaining
ledger USD 3.74777920.** Elapsed work time was not measured; focused reruns followed
fixture/review changes. Next action after reviewed commit/push: stop and report.
