# Quality completion: coding-agent entry point

Prepared 2026-09-28 following the user's request to resume answer quality,
evaluator reliability, and fresh measurement. This supersedes the Phase 70
deferral for these three areas only. The portfolio release remains complete.
This handoff preparation is documentation-only; implementation has not resumed.

## Start here

Read AGENTS.md, the current position in [progress](progress.md), this plan,
[Phase 70](../phase-70/portfolio-finish.md), and the relevant Phase 69 evidence.
Consult the required historical roadmaps for context, not as queues to restart.
Check branch/status and preserve the existing request-log modification. Main is
the established branch. Follow the required commit/review/push loop.

The [older handoff](post-phase-68-quality-remediation-handoff.md) retains the
detailed scoring and custody requirements. Historical results remain immutable:
33/60 is the Phase 65 automated protocol result; Phase 68 has no validated
replacement overall score. An 80% target is not a promised result.

## Phase 71: evaluator reliability

- Start from the prepared [v12 candidate](../phase-69/evaluator-v12.md) and
  [v11 findings](../phase-69/calibration-v11-results.md), not a new evaluator
  from scratch. Inspect existing tests and replay contracts first.
- Audit cumulative spending across the Phase 69 and Phase 70 ledger branches.
  The v12 preparation predates Phase 70 spending; do not treat its older ledger
  as the full current total. Preserve frozen evidence and add a reconciled
  successor ledger/provenance record before any live call.
- The confirmation runner currently imports v11 contracts, transport, report,
  and readiness files. Prepare a versioned confirmation path for the selected
  evaluator; do not run it as if it already validates v12.
- Keep the existing development gate: 24/24 exact challenge judgments, 3/3 exact
  reviewer probes, no unresolved semantic findings after source inspection.
  Freeze the candidate before the separate 16-case confirmation. Predeclare
  exact agreement on all 16, valid contracts and zero unresolved semantic
  findings as its confirmation gate. Do not expose confirmation cases to tuning;
  if exposure/custody is uncertain, replace them with newly isolated cases.
- Use offline checks before a full calibration. Any small live diagnostic is
  labeled development evidence and cannot substitute for the full gate.
- Bound this phase to one full candidate attempt and, if justified by a specific
  new failure hypothesis, one repair attempt. If reliability still fails, record
  the blocker and request a method/scope decision; do not continue indefinitely
  through new version numbers or weaken expectations to obtain a passing score.
- Deliver docs/phase-71 notes, versioned artifacts, focused tests, ledger audit
  and a clear readiness decision. Failed results are retained and reported.

## Phase 72: confirmed runtime failures

- Once evaluator readiness passes, use new development variants to establish
  before/after evidence for incomplete answers, unnecessary abstention,
  ambiguity, memory and multi-question behavior. Offline trace triage and test
  preparation may proceed while the evaluator is budget-blocked.
- Reproduce on current main before fixing: Phase 70 already repaired the
  sufficient-evidence/generation handoff and authorized citation-ID numeric
  scanning. Do not implement these historical findings again.
- Use [runtime triage](../phase-69/runtime-trace-triage.md) as hypotheses, not
  an assertion that every listed case is still defective. Choose the responsible
  retrieval, orchestration, generation or validation layer from actual traces.
- Group fixes by root cause. Keep role/scope filtering before generation,
  authorized citations, fail-closed validation and memory as query context.
  Preserve benchmark expectations; document any proven dataset defect separately.
- Deliver docs/phase-72 notes, regression cases and comparable development
  before/after traces, including negative/security controls. Do not claim a fresh
  generalization improvement from these development cases.

## Phase 73: fresh measurement and publication

- Require Phases 71/72 gates and whole-run budget preflight. Freeze runtime,
  evaluator, prompts, corpus, configuration and index before authoring cases.
- Plan separate context-isolated authoring and validation for the new 60-case
  suite. Obtain applicable delegation authorization before spawning agents;
  this documentation update does not itself grant that authorization.
  Provide frozen corpus/specification, not old questions, failures or answers.
  Preserve custody, source checks, hashes and validation before execution.
- Predeclare the composite from the older handoff: complete relevant supported
  answers and correct behavior; unresolved cases do not pass. Report quotation
  fidelity separately. Target >=48/60; zero observed unauthorized retrieval or
  disclosure is mandatory. Keep latency and full auxiliary-call costs visible.
- Execute once, with no selective retries, expectation edits, dropped cases or
  tuning against this suite. Preserve and publish a valid miss as well as a pass.
  Stop on custody, safety, unknown-call-outcome or budget failures.
- Deliver docs/phase-73 notes, offline-reproducible evidence and consistent
  README/methodology/Dev-Admin reporting. No invented human adjudication or
  independent security validation. Stop after this bounded queue is completed.

## Budget gate

The current approved cumulative ceiling remains USD 5. Last documented
conservative spend is USD 2.14328077, leaving USD 2.85671923 before any new calls.
Reconcile durable ledgers before relying on this figure. No increase is implied
by the user's request to prepare/resume these areas.

The recorded v12 full-attempt reservation is USD 7.72026250, exceeding current
headroom; combined with recorded spend it needs USD 9.86354327 cumulative capacity
for calibration alone. These are historical reservation figures, not refreshed
model prices or expected charges. Recheck prices and all-stage bounds first.
The earlier USD 10 request was superseded, not approved, and would not itself
guarantee enough headroom for confirmation, remediation and the holdout.

Complete offline preparation and a concrete stage-by-stage cost proposal, then
request explicit approval before exceeding USD 5. Never bypass conservative
reservations or omit auxiliary calls to fit a cap. No cloud provisioning.

## Efficient execution within the existing operating loop

- Read required context once per phase, then retrieve relevant sections/diffs.
  Keep the tracker current instead of repeatedly loading all historical notes.
- Use one bounded phase note with decisions, checks, costs and next action;
  avoid copying raw outputs across several Markdown documents.
- Run focused tests after edits; run shared regression/evidence checks at phase
  gates. Re-run only when changes or unresolved failures invalidate evidence.
  Build the web app when frontend/shared contracts or published UI data change,
  not after every evaluator-only prompt adjustment.
- Preserve commit inspection and semantic code review as distinct checks, done
  in one review session. Commit coherent changes; freeze and evidence commits
  stay separate where provenance requires them. Do not reduce custody checks.
- Avoid broad refactoring of versioned evaluators just to remove duplication:
  historical replay is more valuable than cosmetic consolidation in this scope.
- Record elapsed time and command/API counts per phase to measure efficiency.
  No percentage token-saving claim is established by this documentation review.

## Planning estimate

Estimated active agent time, not a measured SLA: Phase 71 3-6 hours, Phase 72
4-8 hours, Phase 73 3-6 hours; total 10-20 hours assuming local services work,
budget approval and evaluator convergence. Allow several sessions over 2-4 days.
Approval waits, provider delays and failed reliability gates can extend this;
the bounded attempt rule prevents pretending research has a guaranteed finish.
Coding-agent usage and separately billed evaluation API spending are different.

## Future improvements outside this queue

- Human adjudication of historical evaluation disputes and production promotion
  review; do not require it to fabricate an automated-result label.
- Real identity/service integrations, deployment, SIEM delivery, named on-call
  ownership, escalation channels, hosted availability and operational evidence.
- Optional qualified independent security assessment and retest. Status remains
  Independent validation required until external evidence exists.

These remain deferred under the [production-readiness roadmap](post-phase-50-defense-and-production-readiness-plan.md).
They are not follow-on phases to auto-start after Phase 73. Financial safety and
external-integration approvals still apply.

## Handoff verification

Documentation-only preparation: relative Markdown links and Git whitespace/diff
checks. No runtime edits, API calls, evaluator execution or new quality claim.
Application tests/builds are not needed for this handoff-only change.
