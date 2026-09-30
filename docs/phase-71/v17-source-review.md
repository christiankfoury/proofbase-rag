# V17 development source inspection

Decision: failed; no evaluator freeze or fresh confirmation is permitted for v17.
Primary coding-agent inspection, not independent human adjudication.

Diagnostic: 25/25 exact cases plus 3/3 reviewer probes. Full calibration: 23/24
exact cases plus 3/3 probes. All supplied questions, answers, sources, required
facts, extracted claims, fact statuses, spans, explanations and reviews were
inspected in both stages. Offline replay verified the raw requests, responses,
reducers and complete token accounting. One semantic finding remains.

In `ambiguous-question-assumed-context`, the user asks how far ahead they must
book. The answer gives a sourced two-day equipment-booking requirement but guesses
the booking topic. The existing reference correctly separates these: supported
policy and citation, failed relevance and clarification behavior. V17 instead
marks the policy unsupported because the answer says "You must book" while the
source says equipment "must be booked". Its reviewer agrees with that error.

The v16 agency instruction is overbroad: the question already establishes the
participant doing the booking. Addressing that same task's deadline to the user
does not add a separate responsible party. This differs from assigning an audit,
inspection or recordkeeping duty to someone merely allowed to reserve/use an
object. Explicit actor restrictions and prohibitions still override any user
premise. The topic guess must still fail relevance and behavior. No original
expectation, output or reduced result has been changed.

The other 23 full cases and all diagnostic controls/probes have no additional
source-inspection finding. Coverage paraphrase, genuinely unsupported agency,
explicit prohibitions, conditions, temporal rules, injection resistance, speech
acts and separate quotation fidelity remain tested. V18 will refine only the
same-action contextual participant distinction with new controls and retain all
prior diagnostics. Unchanged v17 will not be rerun.

Calls: diagnostic 78 (USD 0.87927750), full 75 (USD 0.74998250), total 153
(USD 1.62926000). Cumulative: 2,428 calls, USD 8.88441327. All settled; zero retries.
No v17 confirmation was authored or executed. Phase 73 preparation remains
contingent, and no fresh application quality score exists.
