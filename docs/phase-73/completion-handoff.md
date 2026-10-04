# Proofbase completion handoff

Purpose: transfer the project to a new chat without restarting the investigation.
User priority: finish quickly and efficiently with defensible quality; stop
repeating inconclusive grader prompt changes and documentation-only review loops.
This file records state and next-step recommendations, not new paid authorization.
The user's new-chat instruction determines scope; this documentation task does not
resume API work or create a new funding allowance.

## Read first, then inspect only affected evidence

1. `docs/roadmap/progress.md`, current position only.
2. The single active plan: `docs/roadmap/application-reliability-plan.md`, current
   handoff only; historical sections are not work queues or current spending caps.
3. `docs/phase-73/procedural-ordering-contract-v1.md`: latest reference decision.
4. This handoff and `docs/roadmap/execution-policy.md` for verification/custody.
5. Relevant source and exact artifacts below as needed. Do not reread every
   roadmap, old grader version or failed holdout merely to re-establish context.

## Repository and custody

Workspace `S:/github-repos/enterprise-knowledge-agent`, PowerShell, branch `main`.
Last implementation/review commit before this handoff: `f7de9dae`, pushed and
aligned with origin. Prior offline prototype: `5e1ba151`; paid stop: `d0814221`.
Preserve unrelated local `data/observability/request-logs.jsonl` exactly; SHA256
`f37906539da34d369b0259b014fc061bb2d15b42e31605800d55b724335c176e`.
Do not stage, stash, reset or delete it. Review intended diffs before committing,
verify committed contents, inspect all outgoing commits, push main without force.
A historical Python freeze remains immutable; create a new version if necessary.

## Actual product state

The repository already implements project/department knowledge workspaces,
upload -> review -> approve/index, permission-filtered retrieval, citations and
conversation handling. The current work is reliability and acceptance, not a
new application build or unrelated product roadmap.

V4 remains the active default. Candidate application prompt v6 is disabled and
unaccepted. Candidate v6 passes14/14 development tasks (original12/12 versus
reused v4 baseline6/12, plus2 recipient controls); this is agent-inspected
development evidence, not a qualified final accuracy score.
Selection: `data/evaluation/conversation-continuation/application-selection-v2.json`.
Runtime: `apps/api/app/generation/conversational_candidate.py`, candidate promptv6.
Selected candidate uses pinnedGPT5.4-2026-03-05 low, producer1600/checker1000;
exactly one producer and one checker, no repair. Permission filtering precedes
generation; memory is query context only. Keep all exact quotation/citation,
HTTP/SSE checker and authorization protections. No candidate activation yet.

## Current blocker and completed investigation

Grader v34 passes16/16 diagnostic cases plus3 reviewer probes. Calibration stopped
21/22 matched at `answer-injection-award-pass`; two cases and3 probes unexecuted.
The disputed answer starts `First, report the missing card to reception.` and
omits a9-credit fee. The question asks for both steps; the source lists them but
does not establish their order. Presentation and procedural-order readings are
both plausible. Both still produce an incomplete failed answer.

The latest review did NOT prove a uniquely correct replacement reference label.
It records unresolved interpretation, proposes a general explicit uncertainty
convention, and preserves every original expectation/failed result. Do not report
this as a fixed grader, successful calibration or permission to omit the case.
A future source-justified contract/reference version must preserve ambiguity,
omission, injection and ordering coverage and undergo all qualification gates.
The current24-case suite and3 probes are unchanged. No retroactive score repair.

Do not repeat another broad paid run of v34 or another isolated wording patch.
Do not assume two agreeing calls from the same model establish correctness.
Offline prototype `scripts/conversation_blind_review_design.py` constructs two
independent claims/coverage assessments (four requests/case) before comparing
intermediate labels. It has no provider client, live executor, automatic credit
or release integration. Same-model bias and extraction differences remain risks.
The earlier two-case pilot is deferred because its unambiguous controls cannot
resolve the original reference; it is not the default next paid action.

## Budget: exact current authorization, not account-balance telemetry

| Item | USD |
| --- | ---: |
| Cumulative ceiling after approved CAD13.11 replacement |14.88536776|
| Confirmed cumulative spending |9.17047526|
| Original failed network request, full reservation held |0.14820250|
| Accounted total |9.31867776|
| Unreserved authorized headroom |5.56669000|
| Final-measurement launch floor |4.50|
| Headroom above that floor |1.06669000|

The old USD12.50 and earlier CAD amounts are historical, not additional money.
The CAD13.11 was the entire remaining account balance when approved, converted
conservatively to USD8 including the existing hold; no unused remainder added.
Current live account balance has not been independently rechecked. No top-ups.
Since that amendment, confirmed new spendingUSD2.28510750;1218 settled requests.
All subsequent offline work costUSD0. No new unknown outcomes.

Authoritative records in `data/evaluation/conversation-continuation`:
`cad1311-authorization.json`, `cad1311-budget-stop.json`,
`network-recovery-authorization.json`, and all historical receipt ledgers.
Use `scripts/conversation_cad1311_budget.py` to replay accounting; `spent_usd`
means accounted total INCLUDING the hold. Never release the held amount without
provider evidence and appropriate authorization. Complete per-request reservation,
no provider retries, full output caps and unknown-outcome stop remain mandatory.
The single prior transport exception applies only to its immutable receipt.

Another complete v34 qualification was estimatedUSD2.190283 BEFORE repair checks,
already aboveUSD1.06669 available for qualification. That is an empirical estimate,
not a guarantee, lower bound or price quote for a new four-call design. The latter
may cost more. No presently funded path to final acceptance is established.
Do not spend simply because an individual pilot fits; reconcile the complete
remaining path before paid work. Do not silently reduce the final-launch floor.

## Reusable verification and execution details

Latest offline command:
`python -B -m unittest scripts.test_procedural_ordering_review scripts.test_conversation_blind_review_design`
Result16/16, network blocked;6 contract-review checks plus10 prototype checks.
Eight supplemental examples are specification evidence, not model-generated wins.
Historical calibration replay:
`python -B -m scripts.conversation_grader_v11 report grader-v34-calibration`.
It remains early_stopped21/22. Reuse passing checks while relevant files/config
remain unchanged; do not repeat web builds or paid runs due only to a commit.

Current frozen development tooling:
- `scripts/quality_eval_contract_v34.py` / `quality_eval_transport_v34.py`.
- `scripts/conversation_grader_v11.py` (development).
- `scripts/conversation_confirmation_v11.py` (fresh confirmation, never run forv34).
- `scripts/conversation_measurement_v12.py` (final-v2, never run).
These are frozen predecessors, not ready-to-launch successor qualification tools.
Existing grader caps8192 claims/4096 coverage/4096 review; pinned model and effort
are in transport. Do not cut them to fit a budget.

Previously prepared local environment: `scripts/conversation_environment.py`,
`environment-preparation.json` and `environment-verified.json` in the continuation
folder. Dedicated DB `proofbase_conversation_eval_20261003`,32docs/247chunks/
247embeddings; original DB preserved; Redis14 without flush. Recheck environment
fingerprint when a new final freeze is needed; don't assume services still run.
Existing isolated upload/index and tenant/RLS evidence is recorded in continuation
notes. Keep telemetry off and local-run files in ignored directories.

Existing API credential reuse was already explicitly authorized; never expose it.
No credential is needed for offline review. On this Windows host, restricted
network requests failed with WinError10013. Approved elevated HTTPS access worked;
any later authorized paid command must obtain the appropriate sandbox/network
permission. Do not diagnose another sandbox failure by repeatedly spending.
Git writes/push similarly need appropriate tool permissions. Do not import
`test_application_reliability` into a paid process: it sets a dummy credential.

## Completion gates and efficient next decision

Done still means: application accepted under all gates, candidate activated,
results/limitations documented, verified changes committed and pushed.
Required gates: full16+3 diagnostic;24+3 calibration; fresh independently authored
and validated16 confirmation; fresh frozen60-case final with at least48/60 plus
zero permission/scope and mandatory safety failures, exact citations/quotations,
and no unresolved cases counted as successes. Preserve all existing category
coverage and full output allowances. Failed evidence stays immutable.

Fresh author/validator agents must be newly isolated after freeze. Never reuse
old confirmation/final agents or exposed final-v1 cases. Retired final-v1 reached
two graded cases and an HTTP capture; it is not a final score or reusable holdout.
Use new versioned scripts/custody when behavior changes; no fresh suites until
readiness and budget gates pass. No Azure provisioning or account changes.

The next chat should make ONE concrete completion decision from this evidence:
choose and implement a defensible versioned uncertainty/reference approach with
full preserved coverage, or identify the exact semantic decision it cannot make.
Avoid another circular audit that merely repeats that `First` is ambiguous.
Do the useful offline work first. Then present one whole-path budget assessment
before any further paid execution. If current funds cannot cover the required
path with the existing floor, report that clearly rather than initiating a paid
experiment and stopping at the same funding boundary again. No guaranteed release
claim or promise that more money will solve the grader problem.
