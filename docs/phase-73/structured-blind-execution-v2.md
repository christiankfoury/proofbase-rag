# Corrected evaluator: one authorized full qualification

## User-confirmed finalization: 2026-10-04

The user explicitly closed this release attempt and ended spending. V4 stays
active; V6 remains experimental, disabled and unaccepted. USD8.10754050 stays
untouched. No new qualification, correction cycle or unrelated roadmap work is
queued. The acceptance blocker below remains unresolved; closure does not claim
a successful release or a new V6 application failure.

Future work requires a new scope instruction. Before considering paid
qualification, it must demonstrate offline that comparison logic treats
equivalent judgments consistently and preserves genuine disagreements across
the existing evidence, including difficult cases and uncertainty. A patch for
only the latest failure is insufficient. Historical results, citation and
permission safety, evaluator qualification and the 48/60 release gate remain
unchanged. This finalization does not start that future work.

Documentation-only verification: local settings retain v4 evidence assessment
and post-generation validation, with `conversational_candidate_enabled=False`;
the V6 answer prompt remains `experimental`. No runtime setting was changed.
The offline `structured_blind_execution_budget_v2.prefix()` result exactly
matches the saved closure ledger prefix; ceiling minus accounted spending is
USD8.10754050 and the USD0.14820250 hold is unchanged. The unrelated request-log
SHA256 is unchanged. Reviewed the intended documentation diff and local links,
and ran `git diff --check`. Existing runtime verification is reused; no model
calls, application tests or builds are required for this documentation change.

## Final outcome: qualification failed; paid experiments ended

Diagnostic passes16/16 and3/3 probes. Calibration at `a03f8ff2` stopped22/23 on
`permission-modality-upgraded`, with nine cases and all three calibration probes
unexecuted. The answer upgrades discretionary approval to a guarantee. Both judges
correctly assign contradicted factual support, missing citation support and
contradicted required-fact coverage. However, judge A encodes the main sentence as
literal, while judge B encodes it as action-order with presentation-order excluded.
The frozen comparer requires those interpretation encodings to agree, so it
returns factual/citation unresolved and fails the reference-agreement gate.

[Raw-replayed report](../../data/evaluation/conversation-continuation/structured-blind-v2-calibration/report.json),
[source inspection](../../data/evaluation/conversation-continuation/structured-blind-v2-calibration/source-inspection.json)
and [comparison analysis](../../data/evaluation/conversation-continuation/structured-blind-v2-calibration/comparison-analysis.json)
preserve this failure. The analysis confirms equal projected claim verdicts but
different interpretation encodings; it does not adjudicate or promote the result.
The disputed ordering case22 matched the prospective uncertainty reference and
still failed for its omitted fee. All historical results remain unchanged.

The user-approved stopping condition now applies: end paid experiments and retain
V4. No new evaluator version, correction cycle, fresh16 confirmation, final60 or
activation is started. V6 is unaccepted. Completing its release would require a
separately authorized remedy for representation consistency and all remaining
qualification/release gates; available money does not remove that requirement.

### Final accounting and verification

130 new settled calls cost USD1.65716600: diagnostic60/USD0.84072300 and
calibration70/USD0.81644300. Thirty-eight exact coverage components were reused.
Cumulative confirmed USD12.50220226 plus the retained USD0.14820250 hold gives
accounted USD12.65040476. Under unchanged ceiling USD20.75794526, new-call headroom
is USD8.10754050; balance including the hold is USD8.25574300. The protected USD4.50
floor remains intact. No provider retry or new unknown outcome occurred.

Frozen implementation reuses its16 passing focused checks; no source changed
during execution. Report replay verifies request/receipt/ledger hashes, full
reservations, usage, cost and exact coverage reuse. Root-agent source inspection
covers all executed cases/probes, including citation fidelity and the stopping
failure; it is not independent or human validation. No unrelated build or paid
application check was run. The unrelated tracked request log remains unchanged.

## Original authorization

The user accepted the recommendation with “lets do this”: freeze the implemented
empty-set correction, qualify it once against all controls, then proceed through
fresh16 confirmation and fresh60 V6 measurement only if each gate passes. Activate
only at 48/60 or better with every safety, citation, quotation and source-review
gate satisfied. A further qualification failure ends paid experiments; retain V4.
No additional funds, provider retries, reduced allowances or historical relabeling.
The earlier authorization for isolated author and validator agents remains valid.

## Goal, scope and cost reconciliation

Goal: accepted V6 activation or a preserved mandatory-gate failure. This changes
evaluation tooling only; application behavior, source permissions and references
remain frozen. V4 stays active until accepted activation. Do not restart unrelated
roadmap work. Preserve the unrelated tracked request log.

Existing cumulative ceiling USD20.75794526, accounted USD10.99323876 including the
unchanged USD0.14820250 hold, leaves USD9.76470650 for new requests. This is not a
new balance or an increment. Full qualification needs 242 new calls: diagnostic
60, calibration118, fresh confirmation64. Only the same38 exact V35 coverage
components are reused for judge A; no historical stage acceptance is reused.

Use observed structured-v1 usage from all six new receipts, priced without cache
discounts: mean claims USD0.01810125, coverage USD0.0113750. Remaining qualification
has140 claims and102 coverage calls: USD3.694425. Calibration plus confirmation
estimates USD2.75632750; confirmation alone USD0.94324000. Adding the unchanged
USD4.50 final-launch floor gives USD8.194425, leaving USD1.57028150 planning buffer.
These two simple observed cases are a limited cost proxy, not a guarantee. Final
measurement requires240 grading calls plus application calls (max32 per case).
Reconcile the remaining path before each stage; reserve full allowances before
each call. Stop if the path ceases to fit, a request outcome is unknown or a gate
fails. Keep all original output caps and the floor throughout qualification.

## Frozen implementation and custody

The v2 evaluator is the already implemented empty-set correction; no new prompt
or reference change. Separately versioned execution, live, confirmation, budget
and final adapters retain strict receipt replay, mandatory intermediate agreement,
all16 diagnostic/32 calibration controls and three probes at each stage. They use
fresh destinations and acceptance paths. Final preflight now explicitly verifies
all60 IDs and unchanged call/output bounds and requires the plan to be committed.

Neutral v2 author/validator briefs preserve the prior rubrics. Author fresh suites
only after qualification and the appropriate evaluator/application freeze; seal
and commit before execution. No fresh holdout content is authored in preparation.

Verification: 16 focused execution/projection regression tests; compilation and
preflight bindings, historical v1 raw replay, intended diff review, then commit and
push before the paid diagnostic. Reuse the previously passing unchanged evaluator
and design checks. The old live-budget snapshot assertion remains historical and
is not reused as a current balance test. No frontend or unrelated application build
is required because runtime behavior is unchanged.

## Diagnostic result and calibration handoff

At frozen `81d7a9e9`, diagnostic passes16/16 plus3/3 reviewer probes. All original
inputs and references are preserved; negative-control answers remain failed.
60 new settled requests cost USD0.84072300, with16 exact judge-A coverage receipts
reused. No unknown request or retry. Raw replay and root-agent source inspection
pass; this is not independent human validation or a V6 quality result.

Accounted USD11.83396176 includes the original hold; headroom USD8.92398350.
Calibration plus confirmation estimates USD2.75632750 and the final floor remains
USD4.50, leaving USD1.66765600 buffer. Full32+3 calibration is prepared, max118
new requests plus22 exact saved coverage components. Commit/push its preflight
with diagnostic evidence before launch. No fresh suites authored yet.
