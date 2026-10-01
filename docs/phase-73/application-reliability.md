# Offline application reliability

Started 2026-10-01 on main at `c1d842ee`; implements R1–R4 of the
[active plan](../roadmap/application-reliability-plan.md). External API budget:
USD 0. Preserve historical evidence and the USD 3.79479490 remainder.

Goal: correct source-confirmed application defects in App chat without a new
overall score. No UI/schema/database change, evaluator candidate, paid call,
benchmark edit, security-policy change or new holdout. Stop after R4 publication.

Acceptance: reproduce each code defect before editing; retain the same new
positive/negative/interaction fixtures after editing; verify actual validator and
caller behavior, one repair, source-only grounding and authorization boundaries.
Run affected shared offline regressions, review complete diffs and push main.
Mocked semantic decisions establish plumbing only, never live entailment quality.

## Predeclared coverage and attribution

| Cause / owning layer | Valid / negative / interaction coverage | Evidence and disposition |
| --- | --- | --- |
| Overlapping numeric spans, dropped sign/currency and 20-literal truncation / post-generation validator | Grouped money, codes, decimals, dates, durations, repetitions and sentence boundaries; changed amount/unit/currency/sign; false approver/negation plus semantic handoff, timeout, missing/unauthorized citations and one-repair caller | V6 source review 056 locates fragments after retrieval; new fixtures use unrelated values. Baseline/after recorded under `data/evaluation/application-reliability-v1`. Fixed in `afd9fcd7`. |
| Scenario quantity treated as a policy literal / post-generation validator | Question-only value versus changed policy threshold and hostile override | V6 002/012/016/055 are diagnostic pointers, not acceptance fixtures. No numeric whitelist planned; interpretation remains semantic and requires live validation if not safely reproducible offline. |
| Late ambiguity keyword overrides sufficient evidence / generation routing | Answer and partial-answer in both generation paths; no-evidence, unauthorized chunks, unresolved intent and conflict controls | Newly composed software-policy fixture fails in four route combinations before the fix. Application defect; not attributed to a specific v6 row. |
| Repeated interrogative mistaken for a named subject / request normalization | New schedule/version choices versus historical named incident lookup; hostile role instruction remains blocked | V6 041 raw call `03945` requests clarification for `which calendar`; runtime normalization erases it before retrieval. New independent choice fixtures reproduce the general cause. |

Historical model failures are not an oracle. Attribution compares the question,
authorized source, saved candidate if present, validation and final response;
grader errors are tracked separately. Missing saved stages remain unknown.

## Compact handoff

R1 tests authored before runtime editing. Required artifacts: baseline and after
test results with source hashes, final regression record, cost/time assessment and
evaluator decision record. Unrelated request-log hash at start:
`f37906539da34d369b0259b014fc061bb2d15b42e31605800d55b724335c176e`.

## R1 result

Baseline: 10 test methods, 4 passed, 6 failed (7 failed assertions including
subtests). After: 10/10 numeric methods and 2 shared wrappers pass. `r1-before.json` and `r1-after.json` retain
the same numeric fixtures, failures, source hashes and elapsed test time. The
shared wrapper was added afterward; numeric assertions were unchanged.

The application validator generated `730.50` inside `$2,730.50`, treated positive
`34`/`$34` as present in negative evidence, split dates and ignored numbers beyond
20 distinct literals. One ordered scan now preserves whole tokens, signs,
currency codes, durations and percentages. Normalized whole tokens must agree;
USD and CAD and their symbols are deliberately not inferred equivalent. It also
checks single-digit claims. Only line-leading numeric list labels are structural.
All extracted values are checked; the silent 20-item slice is removed. A 26-value
test rejects an unsupported trailing claim. Evidence is tokenized once per
validation, so removing the cap does not multiply evidence scans per claim.

False approvers/negation still reach semantic validation and are rejected by the
controlled semantic response. Missing/unauthorized citations, timeouts, source
instruction checks and the one-repair limit remain active. The caller test now
passes the unchanged grouped amount to semantic validation without a repair.
No extra default model call is added. Numeric words, conversion, locale-specific
formats and scenario interpretation remain semantic/unverified limitations.
Question numbers are never added to policy evidence or whitelisted.

Verification: `python -B scripts/test_application_reliability.py NumericTests
--record data/evaluation/application-reliability-v1/r1-after.json`; shared wrapper
`SharedTests --record .../r1-shared.json` passes Phase 54 and all 7 quality-runtime
methods (including Phase 35/39/46/48 controls). HTTP/socket blockers record no
attempted external access. Compilation uses Python's in-memory `compile`.
No schema/benchmark/UI changes: benchmark validation, web build and live checks
are skipped by scope and the USD 0 instruction. Semantic diff review found no
remaining blocking issue. R1 implementation is complete; R2 follows the push.

## R2 result

R1 commit `afd9fcd7` was verified and pushed before R2. R2 baseline has five
methods: three pass, two fail (five failed assertions including route variants).
All five pass afterward; `r2-before.json` / `r2-after.json` preserve evidence.
Both changes are application routing corrections. Request normalization now keeps
an unresolved choice or missing decision variables instead of calling the echoed
question a named subject. Existing specific information-search normalizations
still pass. Generation's late ambiguity keyword fallback now respects the earlier
authorized-evidence answer/partial decision, like its existing missing-topic gate.
This can enable the normal generation and validation calls for requests previously
stopped incorrectly; it adds no retry or new processing stage.

New controls exercise both generation paths with sufficient evidence, absent
evidence and role-disallowed chunks; conflicts produce clarification, and mixed
hostile requests remain blocked before retrieval. The historical Phase 52 ASGI
tests also exercise `/query` and `/query/stream`. Retrieval, tenant, project and
department filtering code is unchanged. Unknown empty retrieval is still not
treated as access denial. Paraphrased restricted intents not recognized by trusted
role rules remain a refusal-wording limitation; no forbidden-document lookup was
added. This does not establish production or department-only security coverage.

Verification: `python -B scripts/test_application_reliability.py SharedTests
RoutingTests --record data/evaluation/application-reliability-v1/r2-shared-final.json`
passes all nine methods, including Phase 52/53/54 and quality-runtime suites.
The initial `r2-shared.json` failure was the harness blocking Windows asyncio's
local self-pipe, not a provider call or product failure. The final harness blocks
real HTTP transports and outbound `create_connection` while permitting the ASGI
transport and local self-pipe. Failed harness evidence is retained. Compilation,
complete intended diff review and whitespace checks pass. R2 is complete pending
its commit/push; R3 follows immediately. No API usage or historical rerun.
