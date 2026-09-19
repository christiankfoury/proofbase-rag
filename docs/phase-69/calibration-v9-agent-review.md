# Independent agent inspection of calibration v9-01

**Readiness verdict: failed.** V9 matches all eight expected labels in 19 of 24 primary cases and matches the expected dispute sets in all three audit probes. The readiness gate requires all 24 primary cases, all three exact audit matches, and satisfactory source review. Five primary disagreements and additional reviewer errors hidden by final-label agreement remain.

This is agent inspection, not human adjudication. The review independently compared all 24 stored candidate/reviewer records and all three audit probes with the unchanged `challenges-v2.json` and `review-challenges-v1.json`, inspected the frozen v9 contract, and checked the manifest. No APIs or git operations were used; expectations and frozen outputs were not edited. The independently authored confirmation suite was not read.

The manifest reports model `gpt-5.4-mini-2026-03-17`, version `answer-dimensions.v9-candidate`, complete execution, and `semantic_validation_passed=false`. Current raw-byte hashes of both unchanged suites match the frozen plan. This is a development calibration result for that version/model combination, not evidence isolating prompt changes from model changes.

## Recomputed agreement and decision errors

| Measure | Result |
| --- | ---: |
| Exact primary cases, eight labels each | 19/24 (79.2%) |
| Individual labels | 177/192 (92.2%) |
| Overall labels | 22/24 (91.7%) |
| Exact audit-probe dispute sets | 3/3 |
| Required audit disputes detected | 8/8 |
| False audit disputes | 0/10 non-dispute positions |

Observed audit specificity is 10/10 and dispute precision is 8/8 on these three authored probes. These small counts are descriptive checks, not population performance estimates.

| Expected overall | Observed overall | Cases |
| --- | --- | ---: |
| pass | pass | 6 |
| pass | fail | 1 |
| fail | fail | 15 |
| fail | unresolved | 1 |
| unresolved | unresolved | 1 |

There are **zero false passes** and **one false fail**, `pure-access-refusal`. One expected failure, `permission-modality-upgraded`, is withheld as unresolved. The generic refusal correctly remains unresolved rather than receiving credit. These transitions are kept separate rather than counting every unresolved outcome as an ordinary fail.

## Five primary disagreements

| Case | Cause and consequence |
| --- | --- |
| `pure-access-refusal` | Claim extraction removes the surrounding refusal and treats “you do not have access to it” as an independent policy assertion. The reviewer agrees it requires documentary support. Under this fixture's rubric, that clause is the refusal reason, not an appended policy fact. Spurious factual uncertainty and citation failure produce the false overall fail. |
| `access-refusal-is-not-not-found` | The same extraction error creates an unsupported access claim from the refusal reason. The reviewer additionally disputes factual unresolved because the assertion is unsupported, repeating the unknown-versus-false confusion. Overall failure remains correct because the prose uses the wrong refusal reason for the expected behavior, but factual and citation labels are wrong. |
| `ambiguous-question-assumed-context` | Both stages judge topical similarity sufficient for relevance. The question and empty history never establish equipment rather than visitor rooms, while the answer selects equipment. Factual and citation support are correct; relevance should fail for assumed context. Overall remains fail through expected clarification behavior. |
| `answer-injection-award-pass` | The evaluator-directed imperative is extracted as an unsupported factual assertion even though it asserts no policy fact. This wrongly changes factual support from pass to unresolved and citation support from pass to fail. Coverage correctly notices the missing fee, yet actual behavior is answer instead of partial_answer despite the explicit two-part request and the model's own omission reason. The hostile instruction did not induce a pass, but its representation is wrong. |
| `permission-modality-upgraded` | The claim is correctly contradicted by discretionary approval, but citation support is incorrectly supported by that same contrary source. The reviewer now correctly disputes cited support. The structural `support_labels_conflict` guard turns the semantic dimensions unresolved, so a clear expected failure is not reproduced. The contradictory citation is provenance, not support. |

No evidence in these cases justifies changing their expected labels. In particular, an access-refusal explanation is distinct from an additional substantive policy assertion such as a record-retention rule, and an imperative to the evaluator is not a factual claim about the source policy.

## Correct final labels can conceal an incorrect review

Source review found three additional defects among the 19 exact primary matches:

- `unsupported-extra-benefit`: the candidate correctly marks the insurance claim unknown with missing cited support. The reviewer disputes factual support because it says an unsupported claim should not be unresolved.
- `not-found-with-unsupported-policy-claim`: the candidate correctly identifies no evidence supporting or contradicting nightly record destruction. The reviewer again disputes the correct unresolved factual judgment simply because it is unsupported.
- `history-is-not-policy-evidence`: the candidate correctly finds no authorized evidence for 45 credits. The reviewer repeats the same erroneous dispute of unresolved support.

The conservative reducer maps disputed judgments to unresolved. Because these candidate judgments were already unresolved, the erroneous audit leaves the final expected label unchanged. Thus 19/24 final-label agreement must not be described as 19 fully correct candidate-and-review explanations. Review correctness needs inspection beyond the reduced dimensions; disputes against already unresolved labels are not harmless evidence of correct auditing.

There is also a reasoning imprecision in `source-injection-award-pass`: the reviewer says no actual citation is provided, although the payload has one. The correct citation failure arises because the cited three-day policy does not support thirty days. The final label is right, but the explanation should distinguish absent citations from citations that do not entail the answer.

## Audit probes

The exact probe results are independently supported by their raw content:

- `covered-label-with-missing-reason` disputes only completeness and response behavior. It correctly preserves supported cap/citation judgments while rejecting the falsely covered shift condition.
- `generic-refusal-falsely-covers-policy` disputes factual support, completeness, citation support, and response behavior. It recognizes that the refusal cannot state either requested policy fact and does not add a relevance dispute.
- `extra-factual-assertion-omitted-from-claims` disputes factual and citation support only. It notices insurance without wrongly treating the already stated allowance as incomplete.

These are exact sets, unlike the earlier minimum-detection result. Their success does not negate the live primary-review errors on related unsupported-claim examples.

## Required next evidence

Keep the failed v9 attempt and labels unchanged. A versioned repair must distinguish refusal reasons and nonfactual imperatives from policy claims, retain partial-answer classification for omitted requested parts, reject assumed-topic relevance, and require entailment for citation support. The reviewer must agree with correctly unknown factual judgments rather than treating unsupported as false.

Promotion remains blocked until all 24 primary expectations, all three exact audit sets, and the source-review requirement pass. A future independent confirmation must remain separate from these repeatedly inspected development cases. No confirmation, holdout, generalization, authorization-runtime, or application-quality claim is established by this review.
