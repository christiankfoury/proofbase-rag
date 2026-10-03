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

## Live result: do not promote the candidate

Frozen runtime **`2539b084`** completed the one pass. The
[receipt-backed report](../../data/evaluation/conversational-scenario/results.json)
and [raw run](../../data/evaluation/conversational-scenario/run/manifest.json)
preserve every response. These eight real model outputs, not the mocked tests,
give the predeclared metrics:

| Metric | Observed result |
| --- | --- |
| Complete interpretation/extraction contract | **2/8** |
| Scope classification alone (additional diagnostic, not a replacement rubric) | **5/8** |
| Unsafe calculator acceptance on negative requests | **0/5 observed** |
| Unnecessary calculator rejection on supported requests | **1/3** |
| Supported comparisons returned | **2/3** |

The full interpretation criterion includes exact source/input binding and null
bindings for declined scopes. Policy-assertion and extra-condition cases selected
the correct scope but failed that full contract. Reporting scope-only correctness
separately preserves this distinction rather than changing the frozen rubric.

Every-case inspection against the original question, raw response and FIN-001's
office-supplies row (USD 300 per purchase, manager approval above limit):

| Case | Source/answer inspection and remaining defect |
| --- | --- |
| Below-limit paraphrase, USD 164 | Correct scope and amount/category; source ID has an extra `},` suffix. Exact binding rejects it, unnecessarily. No answer produced by this component. |
| Above-limit paraphrase, USD 425 | Exact input and source binding. Returned comparison correctly says 425 exceeds 300 and the row's condition triggers, with the exact row citation and no purchase permission. |
| Equality paraphrase, USD 300 | Exact binding. Returned comparison correctly says strict `>` is not triggered at equality; no approval exemption or blanket permission is claimed. |
| Policy assertion | Correctly labels `policy_assertion`, but populates binding fields instead of null; malformed source ID and nonmatching category quote also fail the contract. Declined. |
| Multiple amounts | Wrongly labels `row_comparison` and complete, but emits null amount/category. Deterministic binding rejects. It has not correctly interpreted this negative. |
| Missing currency | Wrongly labels `row_comparison` and invents `USD 164` although the question says only `164`; malformed source ID as well. Original-request binding rejects the invented currency. |
| Extra emergency condition | Correctly labels `conditional`, but fills binding fields instead of null. Scope gate declines. The separate emergency source requires contextual reasoning and cannot become a simple threshold decision. |
| Overall purchase permission | Wrongly labels `row_comparison` and complete. Its malformed source ID blocks calculation. This is an unsafe interpretation masked by an independent binding failure. |

The **0/5 observed unsafe acceptances is not evidence that intent handling is
safe**. An explicitly labeled [offline counterfactual](../../data/evaluation/conversational-scenario/scope-counterfactual.json)
changes only the overall-permission proposal's malformed source ID to the real
authorized ID. The frozen calculator then accepts the narrow row comparison for
that broader request. Its answer still withholds blanket purchase approval, but
the routing incorrectly treats the request as completely handled. This probe made
zero calls, did not modify the raw live response and is excluded from live counts.
Do not sanitize the malformed IDs: that would remove the incidental protection.

**Recommendation: revise before activation; retain the deterministic calculator.**
Do not enable this v5 candidate for ordinary users. The extraction-as-automatic-
routing-authority design did not earn its added complexity: only two of three
supported paraphrases completed, three of five negative scopes were misread, and
the apparent safety result depends partly on malformed output. A future separately
authorized design should keep a model proposal advisory and preserve semantic
coverage/applicability validation for conversational requests, or use explicitly
confirmed structured inputs. Merely fixing copied IDs or adding prompt examples
does not address the authority problem. No such redesign, prompt cycle or second
live pass is started here. V4 remains the default; v5 remains an unqualified,
explicitly selected experiment, with this failed-result evidence preserved.

Eight synchronous GPT-4.1-mini calls used 24,544 input tokens (13,440 cached) and
1,746 output tokens. **Actual receipt-derived cost: USD 0.00857920; remaining
shared budget: USD 3.73920000.** No retries, unknown outcomes or additional paid
stages. Run wall time was 27.742274 seconds including local persistence; this is
not an end-to-end application latency measurement. The original USD 0.50 ceiling
was not a new allowance and the unspent portion is not added again.

The initial launch was blocked by automatic approval review over possible
sensitive payload disclosure; no process or API call ran. Read-only checks matched
all five excerpts to the repository's synthetic FIN-001/HR-004 files, consistent
with README/AGENTS declarations. Resubmission of the unchanged command with that
evidence was approved. This was an approval retry, not a provider retry.

Results verification: `python scripts/report_conversational_scenario.py` validates
all frozen hashes, result/receipt links, original journal entries, exactly eight
new settlements, canonical token bounds, cached charges and remaining balance;
it replays deterministic bindings/finalization and recomputes the frozen metrics.
Report compilation passes. Manual source inspection covered all eight cases and
the counterfactual. No runtime or prompt changed after freeze. The unrelated log
hash remains `f37906539da34d369b0259b014fc061bb2d15b42e31605800d55b724335c176e`.

Completion is the predeclared **failed-candidate experiment deliverable**, not a
quality release. Live identity/retrieval, broader conversation, category synonyms,
and actual generated fallback answers were not measured. No overall success-rate
improvement, evaluator qualification or full-evaluation claim. Review and publish
only the evidence/accounting/docs, then stop.
