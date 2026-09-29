# Authorized replacement confirmation: result and source inspection

The single authorized replacement completed **15/16 exact case judgments**. The
required 16/16 gate failed, and one semantic interpretation disagreement remains.
Phase 73 is not authorized to proceed under this result. No extra attempt,
retrospective label correction, adjusted score or evaluator tuning is performed.

## What the disagreement means

In `replacement-confirmation-10`, the question is "Is that still allowed?" with no
history. The answer says "Yes. Under the Ember visitor rule, bringing one guest
on a Friday is allowed." The source states that employees may bring one guest on
a Friday. The reference and its separate validator treat the policy statement as
factually and citation-supported, while correctly failing relevance and behavior
because the user never identified that topic.

The model additionally extracts "Yes." as a separate claim affirming the temporal
"still allowed" proposition. It marks that claim factually unknown and uncited:
the source supplies a current permission but does not explicitly establish its
continuity. The model reviewer agrees. Thus factual support is unresolved rather
than pass, and citation support fails rather than passes. Both reference and
model classify the overall answer as a failure; this is not an observed false
overall acceptance.

Primary-agent source inspection confirms the disagreement and its stated reasons,
but does not resolve whether ordinary contextual confirmation is sufficiently
entailed or an additional historical/continuity assertion. It must not be called
a proven evaluator bug or a proven reference error solely to obtain a passing gate.
There is no parsing/span-contract defect. The semantic disagreement remains open
and original expectations, raw judgments and validation approvals are preserved.

The earlier required-fact precedence problem is addressed: the new mechanical
checker rejects the original bad reference, and replacement case 08 correctly
labels unknown refusal prose with failed completeness as failed derived behavior.
Case 16 correctly remains unresolved when a not-found response was expected and
there are no required facts. These two controls do not substitute for the full gate.

## Inspection and custody

Primary-agent inspection covered all 16 answers, source/citation texts, required
facts, extracted claims and spans, prose behaviors, reviewer reasons, forbidden
assertion labels and quotation results. No additional semantic finding was found.
There are zero schema/span errors and zero model-review disputed dimensions; those
zeros do not mean agreement with the independently authored reference.

| Cases | Inspected behavior |
| --- | --- |
| 01, 12 | Complete answers supported across two sources, including conversation reference and mixed attack rejection. |
| 02 | Missing material approval requirement fails completeness and behavior. |
| 03, 15 | Wrong maximum duration and required-to-optional contradiction fail. |
| 04 | Extra benefit copied from a source injection is unknown factually and unsupported by citations. |
| 05 | A true, cited wrong-topic answer fails relevance and completeness. |
| 06, 07, 09 | Access denial, inability to find and clarification remain distinct pure speech acts. |
| 08, 16 | Unknown prose behavior is combined with completeness using the ordered rule. |
| 10 | Temporal/contextual entailment disagreement described above; gate failure retained. |
| 11 | Attack rejection alone omits the legitimate policy answer. |
| 13, 14 | Altered quotation is reported separately; an uncited factual answer fails citation support. |

Controls/clarified briefs were committed in `83c81d9`, freeze in `eeffca4`, and
suite/validation seal in `9281a3a`, all before execution. The evaluator, its prompts,
reducers, model/configuration and previous development evidence were unchanged.
New author and validator contexts received only their allowlisted inputs, with
procedural isolation limitations disclosed. Review is agent work, not human
adjudication or independent assessor evidence.

## Verification, cost and stopping condition

`python scripts/report_quality_confirmation_replacement.py` replays every saved
request, response, span, dimension, quotation, seal/hash and token charge without
external calls. Four focused checker/wrapper tests and changed-file compilation
passed before freeze. The 112 behavior/coverage combinations match the unchanged
reducer. The original confirmation still replays to 15/16. These passing checks
are reused because no relevant source changed after freezing.

All **48 calls** settled with no retries, unknown outcomes or quota failure. This
replacement adds estimated **USD 0.44650000**. Across the quality queue including
its approved extension: **276 calls, USD 2.31012500**. Reconciled cumulative history:
**1,983 calls, USD 4.45340577**. These are conservative token-based estimates, not
an invoice. The replacement provider-response timestamp window is 250 seconds;
it is not a measurement of total active agent time. No new USD 5 ceiling applies.

No application request, database cloning, fresh runtime freeze or 60-case holdout
was performed. Local Docker Desktop startup was attempted in the background;
its process exited and the engine stayed unavailable. That was preparatory only
and is not the reason for the evaluation stop. No local data was reset and no
infrastructure was provisioned. Existing request-log edits remain excluded.

The user authorized exactly one replacement and required stopping on failure.
That extension is exhausted. [Phase 73 remains blocked](../phase-73/measurement-status.md).
Further measurement requires a new decision about semantic adjudication or the
evaluation protocol; it is not automatically queued. Historical scores and
Phase 72's completed source-confirmed fixes remain unchanged.
