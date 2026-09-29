# Quality completion: coding-agent entry point

Prepared 2026-09-28 following the user's request to resume answer quality,
evaluator reliability, and fresh measurement. This supersedes the Phase 70
deferral for these three areas only. The portfolio release remains complete.
This handoff preparation is documentation-only; implementation has not resumed.
The user approved the bounded workflow below on 2026-09-28.

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
- Required sequence: check the known v11 failure categories on visible
  development cases before spending another full 75-call attempt. If the same
  defects recur, stop that candidate early; retain the partial diagnostic result
  without declaring calibration complete. Do not tune on confirmation cases.
- Bound this phase to one full candidate attempt and, if justified by a specific
  new failure hypothesis, one repair attempt. If reliability still fails, record
  the blocker and request a method/scope decision; do not continue indefinitely
  through new version numbers or weaken expectations to obtain a passing score.
  An early-stopped candidate consumes its attempt; do not reset this limit by
  renaming versions or repeatedly running small diagnostics. Record the selected
  diagnostic cases and expected judgments before calls. Passing the diagnostic
  permits the full calibration but does not itself satisfy evaluator readiness.
- Deliver docs/phase-71 notes, versioned artifacts, focused tests, ledger audit
  and a clear readiness decision. Failed results are retained and reported.

## Phase 72: confirmed runtime failures

- Use new development variants to establish before/after evidence for incomplete
  answers, unnecessary abstention, ambiguity, memory and multi-question behavior.
  Confirmed defects may be fixed while evaluator validation is pending when
  source inspection and meaningful regression tests establish the expected
  behavior. Label these as focused development checks, not validated overall
  quality gains. Evaluator readiness remains mandatory for Phase 73 measurement.
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

- Require Phases 71/72 gates and whole-run cost/call-count preflight. Freeze runtime,
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
  Stop on custody, safety, unknown-call-outcome or provider quota failures.
- Deliver docs/phase-73 notes, offline-reproducible evidence and consistent
  README/methodology/Dev-Admin reporting. No invented human adjudication or
  independent security validation. Stop after this bounded queue is completed.

## API spending authorization (updated 2026-09-28)

The user explicitly removed the prior local USD 5 approval gate for this quality
queue, stating that an account-level hard budget is configured. Do not ask again
to increase the old USD 5 or proposed USD 10 ceiling. The account configuration
is user-reported, not independently verified here; do not change it.

Retain cost estimates, complete ledgers including auxiliary calls, bounded
attempts/call counts, disabled automatic retries and stops on unknown outcomes
or provider quota errors. Last documented conservative spend is USD 2.14328077;
reconcile Phase 69/70 history without rewriting frozen ledgers. The recorded
v12 USD 7.72026250 reservation is historical, not a current expected charge.

The existing v12 runner still enforces USD 5 in code. Phase 71 must introduce
and test a versioned successor authorization path recording this user instruction;
do not silently alter frozen calibration evidence or pretend this Markdown edit
removed the runtime check. Preserve application/tenant abuse limits: this change
applies to the development/evaluation runner, not product-wide spending controls.
This authorization does not extend to cloud provisioning or unrelated work.

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
4-8 hours, Phase 73 3-6 hours; total 10-20 hours assuming local services work
and evaluator convergence. Allow several sessions over 2-4 days.
Provider delays and failed reliability gates can extend this;
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
