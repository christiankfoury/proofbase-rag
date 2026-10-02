# Conversational scenario experiment

2026-10-02; starting runtime `0d018586`. Implement one optional extraction in the
existing semantic evidence-assessment call. Keep the exact-grammar fast path;
share source binding, arithmetic and finalization. No new question templates,
aliases, extra model calls, policy interpreter or evaluator changes.

Acceptance: original request reaches assessment intact; extraction quotes bind
only to that request, with one explicit currency/amount and an exact category.
Only an unqualified row-comparison request with sufficient, conflict-free evidence
may calculate. Overall permission, policy assertions, multiple amounts, missing
currency and extra conditions retain ordinary guarded fallback. Preserve the
model dependency for interpretation/completeness; arithmetic verification is not
semantic proof. Test extraction plumbing, arithmetic and applicability separately,
then sync/stream integration, permissions and finalization tampering.

One predeclared live component experiment: eight cases in
`data/evaluation/conversational-scenario/cases.json`, one real evidence-assessment
call each against the frozen authorized source chunks from live-v2 case 01.
No live retrieval, identity, request assessment, generation or evaluator calls.
Source fixtures isolate interpretation; offline HTTP tests cover caller plumbing.
Three ordinary paraphrases and five negative categories. Inspect raw proposals,
bound records and rendered comparisons against original questions and sources.

Report correct interpretation / 8, unsafe calculator acceptance / 5 negatives,
and unnecessary calculator rejection / 3 supported requests separately. A correct
positive requires correct scope, explicit amount/currency/category and source
binding; a correct negative must classify its disqualifying scope or ambiguity.
Malformed/service outcomes are failures, not correct rejections. Mocked tests
never count toward these metrics. Report model-proposal errors even if code catches
them. Retain only if all eight interpretations are correct, no unsafe acceptances,
and all three positives calculate; otherwise recommend revise or abandon and stop.
This small development diagnostic cannot establish a population success rate.

Authorization: up to USD 0.50 from USD 3.74777920 remaining; no new allowance.
Standard synchronous GPT-4.1-mini only, retries disabled; at most eight requests,
16,384 reserved input tokens and 2,048 output tokens per call. Absolute uncached
upper bound USD 0.07864320, plus per-payload preflight before submission. Pricing
verified 2026-10-02 at https://developers.openai.com/api/docs/models/gpt-4.1-mini:
USD 0.40 input / 0.10 cached input / 1.60 output per million tokens. Preserve raw
receipts and append shared accounting; stop on unknown outcomes, custody failure,
changed pricing, bound violation or observed unsafe acceptance. No automatic
second experiment or prompt cycle. Freeze and commit reviewed runtime, suite and
preflight before spending; publish results separately. Preserve historical files
and the unrelated tracked request log.

## Offline implementation and freeze

The integration is opt-in with `EVIDENCE_ASSESSMENT_PROMPT_VERSION=v5` (candidate);
the default remains v4. Existing prompt files, evaluation standards, fallback
payloads and the exact-grammar path are preserved. V5 retains the complete original
request separately from retrieval wording and adds one typed proposal to the same
assessment response. No extra provider call is introduced. Quotes must occur once
in the original request; code reads source values, checks currency and scope, and
rejects additional numeric operands. Finalization binds the original assessment
request hash and extraction hash as well as source/input spans and arithmetic.
Interpretation and complete-request coverage remain model judgments, explicitly
labeled in answer validation notes. Source-row matching remains exact: no aliases,
free-form rule parsing, overall purchase permission or exception interpretation.

Eleven new methods in `scripts/test_conversational_scenario.py` pass: extraction
schema/payload plumbing, model-free arithmetic/binding, applicability declines,
real sync/stream integration/fallback, and finalization mutations. Three methods
in `scripts/test_conversational_diagnostic.py` verify all preflight hashes and
payloads, eight synchronous stub receipts, and timeout/no-retry/reservation
handling. These results are not extraction-accuracy evidence. Existing 17/25
remediation, 30 shared compatibility (assessment/validation v2 fixtures), and four
frozen-evidence methods pass. Python compilation passes for changed modules and
the diagnostic runner. The 13 exact-grammar caller methods are also rerun.

`preflight.json` binds runtime/source/case hashes and every complete canonical
request. Prepared input reservations are 5,659–5,677 tokens, including 2,048
framing tokens; total uncached reservation **USD 0.0443520** with full output caps.
The shared journal confirms USD 3.74777920 remaining, no unsettled calls. The
runner reserves before submission, captures raw receipts, settles cache-aware
usage, retains full reservations on unknown outcomes, refuses reruns and stops on
observed unsafe acceptance. A changed request or frozen dependency blocks payment.
The diagnostic uses authorized saved sources, not live database retrieval.

Pre-commit semantic review covered complete-request binding, permission placement,
source-derived values, opt-in configuration, old-path preservation, accounting,
and test/evidence claims. No blocking finding remains. Review added assessment
request-hash binding, whole-token input/category bindings and preserved historical
v4 payload behavior. The initial preflight is retained as `preflight-review-draft.json`;
the final preflight binds the reviewed code with identical payload costs. No frontend
build: public response fields are unchanged. No evaluator qualification/full
evaluation. Next action after freeze commit: one authorized live pass, source
inspection, results commit/push, then stop regardless of outcome.
