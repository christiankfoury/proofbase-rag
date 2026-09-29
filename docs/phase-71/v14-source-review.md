# V14 development source inspection

The source-inspection gate fails despite **24/24 matching dimension judgments and
3/3 exact reviewer probes**. The sole authorized temporal correction is consumed.
No v14 confirmation
or Phase 73 holdout may be authored or run under this failed gate. This is primary
agent source inspection, not independent human adjudication.

## Confirmed semantic finding

In `true-answer-wrong-topic`, the question asks for the Cedar meal allowance for
overnight fieldwork. The required fact is meals reimbursed up to 32 credits per
day. The candidate answer instead states the supported parking allowance of
14 credits per day. Both policy facts can be true simultaneously.

The coverage grader labels the meal fact `contradicted`, explaining that the
different category and amount are incompatible. That is incorrect: the meal fact
is **missing** from this answer. It does not assert a different meal limit or
deny the meal allowance. The frozen coverage rubric defines missing as omitted
and contradicted as an explicitly incompatible fact. This is a grader defect,
not a reference-label defect or application failure.

Both statuses reduce to completeness=fail and required response_behavior=fail.
The eight-label comparison therefore reports a match. The semantic reviewer
agrees with the failed completeness dimension and says the required meal fact
is not provided, but leaves the incorrect underlying coverage status unresolved.
Raw contracts and exact spans can validate while this semantic error remains.
Do not count dimensional agreement as a clean source inspection.

Evidence: [case row](../../data/evaluation/quality-completion-v1/v14-calibration/true-answer-wrong-topic.json),
[coverage response](../../data/evaluation/quality-completion-v1/v14-calibration/true-answer-wrong-topic/coverage.json),
and [review response](../../data/evaluation/quality-completion-v1/v14-calibration/true-answer-wrong-topic/review.json).
No labels, reducer, prompt, reference or saved response is changed after execution.

## Temporal correction

All 12 predeclared diagnostic cases match, including six new temporal variants.
Source inspection confirms current permission without inferred history; guessed
topic still fails; explicit unsupported continuity and change-date assertions
remain unsupported; superseded permission and approval-condition contradictions
fail. Six prior failure-category controls still match. Both diagnostic and
calibration coverage explanations call a listed step "first" although the source
supplies no ordering; the factual grader and reviewer correctly avoid asserting
mandatory policy order. Those imprecise explanations do not change the claim or
coverage judgments.

The diagnostic consumed 36 settled calls, estimated USD 0.36164750. Full calibration
consumed 75 settled calls, USD 0.66984750. Both offline replays pass with zero
contract errors or model-disputed primary dimensions. All 24 calibration cases
and three reviewer probes were inspected against their inputs, claims, coverage,
behavior and reviewer explanations. The three probes dispute the exact required
dimension sets. One blocking semantic finding above remains unresolved; the
matching tally is retained, not converted into a clean readiness claim.

V14 total: **111 calls, estimated USD 1.03149500**. Complete reconciled history:
**2,094 calls, USD 5.48490077**, including 387 calls/USD 3.34162000 in this quality
queue. All outcomes settled, no retries, no active reservation. Crossing USD 5
used the previously authorized successor policy, not a new spending approval.
No application API calls or infrastructure were involved.

No extra candidate or selective retry is authorized. Prepared contingent
confirmation drafts were removed after this source finding; no cases were
authored. No evaluator freeze, confirmation seal or Phase 73 execution occurred.
The unchanged Phase 72 regression evidence is reused. Complete evidence/diff
review and whitespace checks precede the evidence commit. This source-review
failure is intentionally published; it is not an unresolved blocking finding in
the repository changes being pushed. Next action: none within the exhausted
bounded queue; further evaluator development needs a new scope decision.
