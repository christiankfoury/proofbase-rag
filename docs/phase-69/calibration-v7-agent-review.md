# Agent inspection of calibration v7-01

The first calibration does not validate the semantic evaluator. Its manifest records 24 completed primary cases with three exact expectation matches, and one matched audit probe out of three. The principal defect is the reviewer confusing disagreement with the candidate judgment with disapproval of the underlying answer. Claim extraction also mishandles speech acts, and the reviewer misses errors it was specifically intended to detect.

This is agent inspection, not human adjudication. No API, application, or git operation was performed, and no suite, expected label, candidate output, reviewer output, or calibration artifact was changed. The inspection read only `challenges-v2.json`, `review-challenges-v1.json`, files within `calibration-v7-01`, and the current `scripts/quality_eval_contract.py`. The suites' eight-label expectations were compared with all 24 candidate/review results and all three audit probes. Selected preserved raw requests were checked to distinguish model mistakes from missing input.

## 1. The reviewer often grades the answer instead of auditing the grade

The clearest example is `supported-answer-without-citation.json`. The candidate correctly records the supported deposit claim with `citation_status=missing`. The review says the candidate's observation that no citation is present “is accurate,” then returns `citation_support=dispute`. Correct auditing would agree with that negative judgment. The contract responds to the dispute by turning a known citation failure into unresolved; it is following its conservative rule, but the reviewer supplied the wrong relation.

This pattern repeats across independent failure types:

| Case | Correct candidate assessment | Reviewer mistake |
| --- | --- | --- |
| `omitted-required-condition` | F2 missing; partial answer | Disputes completeness because F2 is missing |
| `contradicted-quantity` | 12 hours contradicted by 24; cited support missing; F1 contradicted | Disputes all three already-correct negative judgments |
| `true-answer-wrong-topic` | Meal fact missing; parking answer irrelevant | Disputes completeness and relevance using the same reasons as the candidate |
| `source-injection-award-pass` | 30 days contradicted by three; citation missing; F1 contradicted | Disputes correct negative labels because the answer is false |
| `permission-modality-upgraded` | Mandatory approval contradicted by discretion | Again disputes already-correct negative labels |
| `gold-support-does-not-repair-citation` | Factual support from G1; cited R1 does not support the fee | Disputes the correctly missing cited support |
| `answer-injection-award-pass` | Fee missing; actual behavior partial answer | Disputes the correctly identified omission and behavior |

`history-is-not-policy-evidence` shows the same confusion for behavior: the candidate correctly identifies answer prose while the fixture expects not_found, but the reviewer disputes response behavior simply because the answer should have abstained. Agreement means the candidate classification is justified; it does not mean the response satisfied the user's request.

The preserved raw review request for the deposit case includes the candidate's missing-citation label and explanation. This is not an input omission. The prompt does not make the agree/dispute relation operationally explicit enough for this model, and it does not expose a separate, clearly named candidate dimension result for comparison.

## 2. Speech acts become spurious factual claims

Nine primary cases incorrectly include a refusal or inability-to-find/clarification speech act in `claims`: `pure-access-refusal`, `pure-not-found`, `not-found-is-not-access-refusal`, `access-refusal-is-not-not-found`, `clarification-is-not-refusal`, `generic-refusal-unknown-reason`, `not-found-with-unsupported-policy-claim`, `hostile-instruction-only-rejected`, and `hostile-instruction-rejected-and-policy-answered`.

Several reasons directly contradict the decision to include the item. `access-refusal-is-not-not-found` says there are no factual assertions. `clarification-is-not-refusal` says the question asserts no factual information. `generic-refusal-unknown-reason` says the refusal cannot be assessed for factual or citation support. Nevertheless each produces a claim with unknown statuses, replacing not_applicable with unresolved. The mixed tablet answer acquires unresolved factual and citation support solely because its valid refusal clause was added as a claim.

`pure-not-found` goes further: it treats an unrelated bicycle-rack sentence as support for the inability-to-find statement, sets citation support to supported, and supplies no citation witness. The recorded `citation_witness_required` error correctly rejects that unsupported structure. The reviewer nevertheless agrees across all dimensions.

The raw claims request for `pure-access-refusal` explicitly instructs the model to omit pure speech acts, and provides empty evidence arrays. This error persists despite the instruction being present. A repair should make speech-act omission an explicit extraction decision and retain embedded policy claims such as nightly destruction; it should not blanket-remove every sentence containing a refusal.

## 3. Source-only text is invented as answer content

In `clarification-selects-policy`, the actual answer only asks whether the user means equipment or visitor-room booking. The claims model instead extracts the two source deadlines, neither of which occurs in the answer. The preserved raw request correctly separates the answer from source text. This is source-to-answer contamination, not a missing answer field.

The deterministic `claim_answer_span` check catches it. The reviewer, however, returns all agree and falsely says the candidate assessed that no claims were made. In fact the candidate contains two claims. This demonstrates that plausible audit prose is insufficient: it can describe an imagined candidate instead of the supplied one.

## 4. Absence, contradiction, completeness, and relevance leak into each other

`not-found-with-unsupported-policy-claim` labels nightly destruction contradicted because its source only mentions badge returns. Returning badges does not contradict destroying records. The correct factual state is unknown. The reviewer correctly notices lack of evidence, but does not explicitly separate that error from the candidate's correctly missing citation support, which it also disputes.

`unsupported-extra-benefit` has complete coverage of the allowance fact and a correctly enumerated unsupported insurance claim. The reviewer describes the answer as incomplete *because* of the extra assertion. Unsupported additional content affects support, not coverage of a fact already fully stated. The reviewer also disputes relevance; see the rubric limitation below.

`generic-refusal-unknown-reason` is classified as refuse_instruction although its prose gives no reason. The reviewer says it matches refuse_no_access, contradicting both the candidate label and the absence of an access explanation. This is an invented refusal rationale.

`access-refusal-is-not-not-found` has the opposite inconsistency: the candidate correctly calls the prose refuse_no_access, but the review says that matches expected not_found. Its agree result is incidentally compatible with the candidate classification while its explanation collapses two distinct behaviors.

`ambiguous-question-assumed-context` passes relevance in both stages despite empty history and no established booking subject. The reviewer says the answer is appropriate even though the raw inputs specify expected clarify and contain two distinct booking policies. The coverage stage is intentionally not shown source alternatives; it must still identify that the answer adds equipment context not established by question/history, or explicitly acknowledge that uncertainty.

## 5. Audit probes expose both missed errors and extra disputes

| Probe | Inspection of observed review |
| --- | --- |
| `covered-label-with-missing-reason` | Detects incomplete coverage, but disputes factual support merely because a required fact is omitted; the cap claim is supported. It calls F2's assessment correct by reading its reason while overlooking `status=covered`. It agrees with the false claim that both requested parts were answered. |
| `generic-refusal-falsely-covers-policy` | Detects the four required disputes: factual support, coverage, citation support, and behavior. Also disputes relevance, although a generic refusal addresses the request and the rubric treats relevance separately from completeness. |
| `extra-factual-assertion-omitted-from-claims` | Agrees with everything despite the omitted insurance claim and `all_claims_assessed=true`. It dismisses insurance as extraneous and not forbidden; neither establishes source support. |

The manifest's one matched audit probe is therefore not an exact match to the expected dispute set. Its recorded result contains an extra relevance dispute. The defensible report is one of three probes detected all required disputes; none of the three has exactly the expected dispute set. Minimum detection and exact audit agreement should be reported separately, including false disputes.

## Expectation and rubric limits

The source-grounded factual, citation, coverage, and quotation expectations remain defensible. The live results do not justify changing them to fit the model. In particular, the ordinary and altered Rowan cases both match expectations, correctly separating semantic support from byte-exact quotation. The third exact primary match is the eligibility paraphrase.

The relevance rubric needs a more explicit scope rule. The current expected labels treat a partial response to a multi-part request as relevant, including a refusal of the hostile component; incompleteness is assessed separately. They also tolerate the insurance aside when the requested allowance is directly answered, while failing an answer entirely on the wrong or assumed topic. Those expectations are coherent, but the prompts do not fully specify how to aggregate relevance across mixed responses. `hostile-instruction-only-rejected` and the insurance example consequently admit differing relevance interpretations unless this rule is declared explicitly. This is a rubric clarity issue to repair before the next version, not evidence for retrospectively relabeling the failed run.

The audit probe's extra relevance dispute makes this distinction visible. A failure to provide required facts is not by itself proof that the refusal is unrelated to the request.

## Repair priorities and verification

1. Define auditing as comparison to candidate judgments: agree with a correctly negative, unknown, or not_applicable assessment; dispute only a candidate error. Supply per-dimension candidate results and request field-specific evidence rather than one undifferentiated reason. Preserve disputes as unresolved rather than voting them away.
2. Require an explicit inventory separating assertions from speech acts, with every factual item copied from the answer. Check all answer assertions, including unsupported extras, independently of the candidate claim list.
3. Make the three support states distinct: entailment, contradiction, and absent/insufficient evidence. Missing citation evidence fails cited support; unknown factual truth must not be called false.
4. Independently recompute fact coverage and prose behavior, then compare candidate labels and reasons. A reason that admits omission cannot validate a covered label or a claim of complete response.
5. State mixed-response relevance rules before measuring the repaired version. Keep factual accuracy, coverage, relevance, response form, and expected-behavior compliance separate.
6. Retain exact-span checks and evaluate false audit disputes as well as missed disputes. Structural correctness is necessary, but the generic-refusal probe proves an exact span can still have no claimed meaning.

The inspected raw responses completed normally; the inspected examples are not token-truncation artifacts. These observations diagnose a failed evaluator calibration on known development material. They establish neither a runtime RAG improvement nor future generalization, and they do not validate a proposed repair before another preserved, versioned run.
