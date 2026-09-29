# Phase 71: bounded evaluator reliability

Started 2026-09-29 on main at `a3eac80`. The unrelated tracked request-log edit
is preserved and excluded. No application behavior changes belong to this phase.

Goal: validate the prepared v12 evaluator without changing challenge expectations
or reducers. Acceptance: 24/24 exact challenges, 3/3 exact reviewer probes, valid
contracts and zero unresolved semantic findings after source inspection; freeze
before a separate 16/16 confirmation with the same contract/source-review gate.
Failed results are a deliverable, never evaluator readiness.

Predeclared first diagnostic (in order): `omitted-required-condition`,
`not-found-with-unsupported-policy-claim`, `supported-answer-without-citation`,
`permission-modality-upgraded`. Expected judgments are the unchanged rows in
`challenges-v2.json`, bound by hash in each plan. These directly exercise all four
v11 defect categories. Stop this candidate at the first mismatch, invalid contract
or disputed dimension. Passing permits the full 75-call development calibration;
it does not establish readiness. Diagnostic calls are development evidence.

At most two candidates including early stops. A repair requires a specific new
failure hypothesis recorded before calls. No confirmation exposure for tuning;
the old confirmation's documented custody is insufficient to establish isolation
from all later evaluator work, so author and validate fresh confirmation only
after selecting and freezing a successful development candidate. The user has
authorized isolated authoring/validation agents. No Phase 73 authoring before
application/evaluator/corpus/configuration/index freeze.

The successor ledger reconciles the 1,696-call Phase 69 history and 11-call Phase
70 suffix. Conservative starting spend: USD 2.14328077. Prior floor rounding is
preserved. The user removed the local USD 5 ceiling; account budget is user-reported,
not verified. Whole-stage token reservations and call limits, no SDK retries,
unknown-outcome/quota stops and complete auxiliary accounting remain mandatory.
Historical ledgers, prompts, reports and product abuse limits remain unchanged.
GPT-5.4 standard rates remain USD 2.50/M input and USD 15/M output, checked against
https://developers.openai.com/api/docs/models/gpt-5.4 on 2026-09-29; no cache discount.

Verification: focused successor ledger/runner tests, unchanged v12/replay tests,
historical report replay, source inspection and complete diff review. No frontend
build required for evaluator-only work. Current initial check: 19 v12/confirmation/
calibration-replay tests passed; no external calls yet.

Compact handoff: goal/gates above; implementation in progress; next action is
offline successor runner verification then the first bounded diagnostic. Stop
on custody, unknown outcome or quota errors. Elapsed time and final cost pending.
