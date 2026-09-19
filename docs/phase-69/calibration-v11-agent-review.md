# Independent agent inspection of calibration v11-01

**Readiness remains failed.** Independent comparison confirms 20/24 exact primary cases, 181/192 expected labels (94.3%), 22/24 overall labels, and 3/3 exact audit-probe dispute sets. The gate requires all 24 primary cases, all three exact probes, and satisfactory source review; the four primary disagreements remain disqualifying.

This is agent inspection, not human adjudication. All 24 candidate/reviewer records and three audit records were inspected against unchanged `challenges-v2.json` and `review-challenges-v1.json`; their hashes match the frozen plan. No APIs or git operations were used, no expectations or frozen outputs were changed, and no independently authored confirmation content was read.

The manifest records `gpt-5.4-mini-2026-03-17`, complete execution, and `semantic_validation_passed=false`. It records cumulative spend of USD 2.13692667; this is cumulative, not the cost of v11 alone. No readiness or performance conclusion about an unexecuted later version is made here.

## Independently recomputed outcomes

| Expected overall | Observed overall | Cases |
| --- | --- | ---: |
| pass | pass | 7 |
| fail | fail | 14 |
| fail | unresolved | 2 |
| unresolved | unresolved | 1 |

There are **zero false passes and zero explicit false fails**. `not-found-with-unsupported-policy-claim` and `supported-answer-without-citation` lose their expected fail classification to unresolved. All seven expected passes pass, and the generic refusal correctly remains unresolved.

The audit probes detect all eight required disputes with no extras among ten expected non-dispute positions: exact sets 3/3, observed specificity 10/10, and dispute precision 8/8. These small authored development checks are not generalization estimates.

## Four primary disagreements

| Case | Cause |
| --- | --- |
| `omitted-required-condition` | Claims assessment treats “The reimbursement cap” as an unspecified broader cap, although the question establishes a Lark taxi claim. The claim is supported by R1/C1 in that context. Reviewer correctly disputes the unknown/missing labels, but the resulting factual and citation dimensions remain unresolved rather than pass. The omitted shift condition remains a separate, correctly detected completeness failure. |
| `not-found-with-unsupported-policy-claim` | Candidate correctly marks the destruction assertion factual unknown and cited support missing. Reviewer agrees the citation is missing yet disputes aggregate citation_support=fail, claiming missing/unsupported is not a citation failure. This contradicts the rubric's reduction from missing cited support to fail, and changes overall fail to unresolved. |
| `supported-answer-without-citation` | The model splits the source sentence into two reconstructed sentences rather than copying exact answer substrings. Neither generated claim string occurs verbatim in the answer: one adds a period where the original continues with “and,” and the other repeats the subject while omitting intervening words. `claim_answer_span` correctly rejects the extraction. Reviewer agrees with the semantic content but misses this provenance defect; overall becomes unresolved. |
| `permission-modality-upgraded` | Candidate correctly classifies answer prose and fails the contradicted required fact, citation support, and derived response behavior. Reviewer says direct answer prose should make response_behavior pass, confusing actual response form with the derived requirement for a correct and complete expected answer. Behavior becomes unresolved while other failures preserve overall fail. |

Context may resolve which cap “the cap” refers to; it must not provide new factual evidence or import a reference answer. Exact-span extraction may retain a full compound sentence or use genuine substrings; semantic atomization does not authorize rewriting the claim text.

## Errors beyond the eight-label score

The modality reviewer also disputes `forbidden_assertion=absent` while explicitly saying there are no forbidden assertions. Its explanation says the dimension should be “agree, not absent,” mixing the audit's agreement vocabulary with the candidate's presence/absence vocabulary. The final forbidden-assertion judgment becomes unresolved. This is a real additional review defect, but `forbidden_assertion` is outside the suite's eight expected labels, so the 181/192 label count does not measure it directly.

No additional substantive false audit dispute was found among the 20 exact primary matches. The former unknown-versus-false confusion is not present in their insurance and history-only judgments. A minor explanation defect remains in the otherwise matching Hazel case: the reviewer says the answer “correctly omits” the fee, then correctly marks completeness fail. The labels and surrounding explanation identify the omission as a failure; the word “correctly” is misleading rather than evidence that the fee should be omitted.

The ordinary and altered Rowan cases now extract their normative deadline claim and retain the intended quotation distinction. Wrong-topic answer form, generic second-person policy wording, and relevance to the hostile part of a mixed request also match the unchanged expectations in this run. These successes do not negate the remaining extraction and audit defects.

The frozen attempt should remain unchanged. Subsequent work must preserve context-only reference resolution, exact answer spans, the missing-citation-to-fail rule, and the distinction between candidate labels and audit agreement. Until the full gate and source review pass, no evaluator promotion, confirmation success, sealed-holdout claim, or RAG-runtime improvement is established.
