# Generated answers versus application responses

2026-10-02; offline review at `eef9f4ef`. **The conversational scenario v5
candidate is closed as unsuccessful and remains disabled for ordinary use.**
The [eight-call experiment](conversational-scenario.md) found incorrect scope
interpretation, unnecessary rejection and protection dependent on malformed IDs.
Its earlier “revise before activation” recommendation is superseded by closure.
Keep the existing bounded calculator unchanged; no expansion or prompt cycle.
The configured default is evidence-assessment v4, with no version override found
in the process environment or the root/API `.env` files. The opt-in candidate
files remain historical implementation evidence, not an approved release.

## Evidence and counting boundary

This review covers **all 18 attempts** in the two focused application diagnostics:
[live-v1](application-reliability-live.md), runtime `8e9fcb97`, and
[live-v2](reliability-live-v2-results.md), runtime `d4c50ebe`.
Ten have generation receipts and final responses; nine initial generations are
parseable answer objects and one is malformed. Five other application outcomes
precede generation; three attempts stop at local diagnostic bounds.

Compare the actual provider output, any repair, final answer/type/citations,
validation trace and captured authorized chunks. Source judgments below are
coding-agent inspection, not independent adjudication or new evaluator labels.
The original request supplies scenario amounts; policy amounts come only from
authorized sources. Inspect full chunks as well as displayed citation excerpts.
Request roles, tenant/project metadata and citation IDs were checked against the
saved evidence. These cases have no department scope or conversation memory.

Counts describe observed mechanisms, **not a pass/fail partition or accuracy
rate**. Mixed observations can overlap. Older full evaluations are outside this
bounded comparison; their unresolved grades remain unchanged. The conversational
experiment tested extraction with frozen sources, not generated fallback answers,
so it contributes no answer-comparison cases. Offline counterfactuals add no cases.
Neither diagnostic measures the current runtime's overall behavior.

## Ten generation-to-final comparisons

Case links contain the final response and authorized sources. `G` and `V` identify
generation and validator `raw/call-NNN.json` files in that case's directory;
the directory matters because numbering restarts between segments.

| Case; receipts | Original → final; source inspection |
| --- | --- |
| [v1-01](../../data/evaluation/application-reliability-live-v1/run/diag-01.json); G003, V004 | Same answer and quote: conference registration USD 1,500/event, manager approval before purchase. FIN-001 Expense Categories supports both. Retention of a supported answer, not a correction. |
| [v1-03](../../data/evaluation/application-reliability-live-v1/run/diag-03.json); G011, repair012 | Correct requested comparison, user USD 143 below FIN-001's USD 300 category limit, becomes `not_found`. The deterministic guard demands policy support for USD 143 and rejects the identical repaired prose. **Harmful rejection of the bounded comparison.** This does not establish overall purchase permission. |
| [v1-05](../../data/evaluation/application-reliability-live-v1/run/diag-05.json); G019, V020 | Same remote-work answer. HR-003 supports manager approval for short domestic changes and People Operations review for longer ones. “Without needing further review” is broader than the explicit text if read as a universal exemption; it can also mean only the contrasted People Operations route. **Leave that interpretation unresolved**, retaining the supported core. |
| [v1-08](../../data/evaluation/application-reliability-live-v1/remaining/diag-08.json); G005, V006 | Same partial answer appropriately leaves the visa form unknown, but broadens HR-003's outside-Canada/US ambiguity condition to international work generally. The validator substitutes the narrower source claim for the actual wording and accepts it. **Scope error passed validation.** |
| [v1-09](../../data/evaluation/application-reliability-live-v1/remaining/diag-09.json); G010, V011 | Same supported OPS-001 answer: return within ten business days unless HR Admin extends; shipping label may be provided, not guaranteed. No correction. |
| [v1-10](../../data/evaluation/application-reliability-live-v1/remaining/diag-10.json); G015, V016 | Answer body unchanged; `answer` becomes `partial_answer`. Formatter replaces reordered source sentences with a contiguous OPS-001 excerpt: **beneficial quote-fidelity correction**, but its 240-character prefix loses all payroll support. Full chunk requires review before payroll action and says this policy alone does not authorize deductions. The answer omits that caveat. Whether “do not automatically deduct” overstates the policy, and whether the partial label is warranted, remain contextual judgments rather than forced failures. |
| [v2-01](../../data/evaluation/application-reliability-live-v2/run/check-01.json); G003, V004 | Correct requested USD 217 versus USD 300 comparison becomes `not_found`: validator returns empty `numeric_context`. **Harmful rejection**, although failing closed on missing provenance is required by the contract. Earlier assessment also wrongly attributes the user's amount to FIN-001; that error does not itself cause the rejection. |
| [v2-03](../../data/evaluation/application-reliability-live-v2/run/check-03.json); G013, V014 | Same multi-policy answer joins longer domestic changes and outside-Canada/US work under “such requests” being ambiguous. HR-003 limits ambiguity to the latter. Validator preserves the sentence this time but incorrectly accepts its meaning. **Scope error passed validation.** |
| [v2-04](../../data/evaluation/application-reliability-live-v2/run/check-04.json); G018, V019 | Supported payroll-review/no-independent-authorization and discretionary-label prose remains unchanged. Formatter replaces reordered OPS-001 sentences with a contiguous excerpt containing the relevant payroll text: **beneficial citation correction**. Whether `partial_answer` overstates missing information is unresolved; the source does not specify every possible payroll action. |
| [v2-05](../../data/evaluation/application-reliability-live-v2/run/check-05.json); G023, V024 | Human-readable answer contains the correct IT-ADMIN-001 monthly/quarterly intervals and exception fields, but invalid escaped quotation delimiters break JSON. The old parser passes raw JSON text onward; the validator assesses only three embedded claims, violating candidate coverage, then finalization returns `not_found`. **Application generation/contract failure**, not proof that a valid answer was needlessly rejected or that a factual error was successfully corrected. |

Among these ten captures: **two citation-fidelity corrections, two harmful
comparison rejections, two confirmed scope errors accepted, and zero demonstrated
corrections to answer-body factual content**. Three cases retain unresolved
semantic judgments (v1-05, v1-10, v2-04); the malformed case is separate. The
v1-10 citation correction has a confirmed excerpt-selection defect, so it is
not an unqualified improvement. No whole-case score is assigned.

## Outcomes before generation and diagnostic limitations

**Three confirmed avoidable abstentions:**
[v1-02](../../data/evaluation/application-reliability-live-v1/run/diag-02.json)
(assessment007),
[v1-04](../../data/evaluation/application-reliability-live-v1/run/diag-04.json)
(assessment015), and
[v2-02](../../data/evaluation/application-reliability-live-v2/run/check-02.json)
(assessment007). Authorized FIN-001 rows directly correct the proposed conference
and office-supplies limits/approval rules. Assessment treats a disproved premise
as missing evidence, clears generation evidence and returns `not_found`.
V2 even states the correct rules inside `missing_information`. No generated
answer exists to credit or blame; a topical source ID alone would not justify
overriding this gate.

**Two appropriate early routes:**
[v1-06](../../data/evaluation/application-reliability-live-v1/run/diag-06.json)
asks the user to resolve domestic versus cross-border intent;
[v2-06](../../data/evaluation/application-reliability-live-v2/run/check-06.json)
denies the Employee's privileged-access request without restricted evidence or
facts. These are controls, not generation corrections or a completed security gate.

**Three diagnostic-tool interruptions:**
[v1-07](../../data/evaluation/application-reliability-live-v1/run/diag-07.json),
[v1-11](../../data/evaluation/application-reliability-live-v1/remaining/diag-11.json),
[v1-12](../../data/evaluation/application-reliability-live-v1/final/diag-12.json).
The harness rejects estimated assessment inputs before submission. They are not
model failures, semantic abstentions or completed permission comparisons.
The earlier laptop/PTO preflight rejection is also tooling/planning evidence,
not an additional executed answer case. V2's overstrong expectations concerning
location/role clarification and an explicit prohibition on threatening deductions
are not source-backed requirements; their absence is not counted as a defect.

## Priority and stopping decision

**The strongest next target in this bounded sample is false-premise evidence
sufficiency:** three confirmed lost answers, versus two numeric rejections and
two accepted geographic errors. Repeated wording variants are not independent
frequency estimates, and this does not establish the most common production bug.
Retrieval supplied the relevant rows; retrieving more chunks would not address
the demonstrated decision error.

Recommend one future structural intervention at the existing assessment boundary:
**represent the requested policy fact and its source span separately from the
truth of the user's premise**, then derive answerability from available facts.
The [current normalizer](../../apps/api/app/reasoning/evidence_assessment.py)
derives insufficiency from unsupported facts and collapses `contradicted` into
`supported`; the [caller](../../apps/api/app/main.py) empties generation chunks
for non-answer routes. Neither represents this distinction reliably. Preserve
permission filtering and fail-closed behavior for missing/conflicting evidence;
do not promote an unsupported fact merely because it names a chunk or parse a
correction out of free-text missing-information notes. Source selection and
entailment still require reasoning. Future acceptance must contrast a false
premise with an unknown field, conflicting rules and unauthorized evidence.
This recommendation does not authorize implementation, a new prompt cycle,
calculator expansion or further paid work.

Review complete: inspected all ten candidate/final pairs and eight earlier exits;
read-only Python checks verified 18 manifest row hashes, 80 raw receipt hashes,
authorization metadata and generated citation identities. Local links and
`git diff --check` pass. Only this report and the tracker change; no runtime tests
or builds are needed for documentation. Historical artifacts, grades, accounting
and the unrelated request log remain unchanged. **API calls/cost: 0 / USD 0;
remaining budget USD 3.73920000.** Commit and push this documentation, then stop.
