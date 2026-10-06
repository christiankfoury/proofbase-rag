# Evaluation reliability and application diagnosis

## Current scope and authorization

Created 2026-10-06 at the user's request to document the phases for recommendation
steps 1 and 2. **This request authorizes planning documentation only.** All phases
below are planned, not started. Publishing this plan does not start implementation,
reopen the closed Phase 73 attempt, or authorize model calls. A later instruction
to execute the offline plan can authorize ER1 -> ER2 -> AD1 -> AD2 under these bounds.
Steps 3-5 remain conditional possibilities, not an implementation queue.

This is the single current planning reference linked from
[progress](progress.md). The [previous application plan](application-reliability-plan.md)
and [completion handoff](../phase-73/completion-handoff.md) retain historical custody.
Use [AGENTS.md](../../AGENTS.md) and [execution policy](execution-policy.md) for the
operating loop and verification matrix; historical standing authorizations do not
override this planning-only scope.

V4 remains active. Conversational candidate prompt V6 stays experimental, disabled
and unaccepted. Its 14/14 inspected development tasks do not establish fresh quality:
only the original 12 have the matched historical V4 comparison (6/12 versus 12/12);
the two recipient controls have no V4 baseline. The older Phase 73 measurement
named v6 is a different artifact, not this candidate's fresh evaluation.

The last release attempt remains failed at evaluator qualification. Preserve its
16+3 diagnostic result, calibration stop at 22/23, unexecuted cases/probes and
unstarted fresh16/fresh60. No historical result, reference, receipt, hold or gate
is overwritten by a diagnostic projection or prospective comparison contract.

## Goal, product impact and boundaries

User-facing goal: identify how to make App chat answer useful questions completely
and correctly, with authorized evidence and appropriate clarification, before
choosing further application or AI architecture changes.

The implementation surface proposed here is offline Dev/Admin evaluation tooling
and diagnostic artifacts. No App UI, public dashboard score, API behavior, database
schema, ingestion policy, permission rule, default model or candidate activation
changes are planned. Existing application modules may be inspected and exercised
through isolated offline fixtures; product fixes require a subsequent scope.

Separate three mechanisms throughout: software regression tests, the runtime
answer checker, and the offline quality evaluator. Their failures and evidence
are not interchangeable. Agent inspection is not human or external adjudication;
two blind calls to the same model are not statistically independent proof.

Success for this investigation means a verified offline comparison implementation
with explicit limits, a source-linked diagnosis of existing application evidence,
and a concrete next-action decision. It does not mean a qualified live evaluator,
an accepted candidate, improved model accuracy or a completed release.

## Planned sequence

| Phase | Recommendation step | Deliverable | Dependency / exit |
| --- | --- | --- | --- |
| ER1: evidence and comparison contract | 1 | Hashed evidence inventory, labeled comparison matrix and prospective contract | No unresolved scoring change silently adopted |
| ER2: offline comparison implementation | 1 | Versioned comparator, broad positive/negative checks and historical replay | All declared contract checks pass; no release credit |
| AD1: trace-based application diagnosis | 2 | Linked stage traces, failure attribution and measured/missing data inventory | ER2 offline acceptance; uncertain causes stay explicit |
| AD2: controlled diagnostic comparisons and decision | 2 | Offline comparison harness/replays, available results, acquisition gaps and ranked decision | Stop after evidence-backed recommendation; no automatic steps 3-5 |

ER/AD identifiers are local to this plan, not new versions of historical Phase 73
results. At execution time create phase notes under
`docs/evaluation-reliability-diagnosis/` and artifacts under
`data/evaluation/evaluation-reliability-diagnosis/`, separated by phase/version.
These are proposed destinations, not existing completed deliverables.

## Required context and evidence reuse

At each phase start read the current-position section of progress, this plan and
the relevant new phase note. Reuse already-read context unless changed. Follow
source references on demand rather than reopening every predecessor.

- [Project overview](../../README.md) and [algorithm reading order](../algorithm/README.md).
- [Application reliability fixes](../phase-73/application-reliability.md) and
  [candidate development](../phase-73/conversation-continuation.md).
- [Structured evaluator design](../phase-73/structured-blind-evaluator-v1.md),
  [empty-set projection](../phase-73/structured-blind-evaluator-v2.md), and
  [final execution/closure](../phase-73/structured-blind-execution-v2.md).
- [Ordering contract v2](../phase-73/procedural-ordering-contract-v2.md) and
  [earlier audit](../phase-73/conversation-offline-grader-audit.md), only for
  existing uncertainty decisions and known limitations; do not repeat that audit.
- [Evaluation methodology](../evaluation/methodology.md) and
  [failure taxonomy](../evaluation/failure-taxonomy.md), checked against actual code.
- Source entry points: `scripts/structured_blind_evaluator_v1.py`,
  `scripts/structured_blind_evaluator_v2.py`, their focused tests,
  `apps/api/app/main.py`, `apps/api/app/generation/conversational_candidate.py`,
  retrieval, reasoning, memory, citation and prompt modules as implicated by traces.

Bind evidence to source/configuration/corpus versions, not filenames alone. Keep
the original baseline and all failed attempts. Exposed historical holdouts may
support diagnosis but cannot become fresh acceptance data. Do not author a new
holdout or open an unexposed sealed suite during this investigation.

## Shared phase operating loop

Apply this loop separately to ER1, ER2, AD1 and AD2 when execution is authorized:

1. **Plan:** record the user-facing goal, affected surface, backend/data impact,
   input versions/hashes, hypotheses, acceptance criteria, checks, artifact paths,
   non-goals, cost and stopping conditions in the phase note before changing code.
2. **Implement:** reproduce the relevant failure first where a defect is claimed;
   implement the smallest complete diagnostic or comparison change. Preserve
   before/after evidence on identical cases. Reuse existing tools where sound.
3. **Verify:** run focused checks from the execution-policy matrix. Exercise real
   parsing, comparison and caller paths as applicable; mocks establish plumbing,
   not model judgment quality. Record skipped and unavailable checks explicitly.
4. **Review:** inspect the complete intended diff, including new artifacts, for
   semantic errors, regressions, authorization leaks, misleading metrics and
   evidence/reference mutation. Fix findings and rerun only affected checks.
5. **Commit to main:** stage only reviewed scope; include docs and a detailed
   product/engineering/verification/limitations message. Ask before switching or
   committing if the current branch is not main. Preserve unrelated local edits.
6. **Verify commit:** inspect `git show --stat --oneline HEAD`,
   `git show --name-only HEAD` and `git show --check HEAD`; compare with the reviewed
   change. Recheck only a hook/staging delta if contents changed.
7. **Push:** inspect the full outgoing range and branch/status, require an empty
   index and no unexpected commits/divergence, then push main without force.
   Confirm alignment with origin/main and record any failure.
8. **Continue or stop:** within a later authorized offline run, advance through
   the planned sequence after each successful gate. Stop dependent work at a
   material evidence/scoring/permission/cost decision; complete unaffected work.
   AD2 is the terminal milestone. Planning publication itself stops before ER1.

Each phase note records the compact handoff required by execution policy: tested
revision/diff and input hashes, commands/results, reused evidence, review findings,
remaining uncertainty, next action, elapsed time if measured and new call/spend
counts. Do not introduce an additional review ceremony or repeat passing checks
merely because a commit was created. Ordinary work needs no subagents; historical
isolated holdout-author/validator authorization does not apply to these phases.

## ER1: evidence inventory and comparison contract

**Plan.** Define which differences are representational and which change the
substantive judgment. Review saved judgments together with exact questions,
conversation, answers, authorized sources, citations and reference versions.

**Implement.** Create a read-only, hashed inventory of relevant saved evidence:
all available structured-blind v1/v2 diagnostic and calibration packets, existing
ordering controls/probes, and predecessor examples needed for known failure
families. Declare selection rules before labeling; list missing/unexecuted inputs
and reasons rather than silently excluding them. Preserve the full inventory even
when a bounded representative matrix is used for detailed analysis.

Build a comparison matrix covering identical judgments, equivalent category or
witness choices, reordered claims, split/combined claims, real support differences,
different omitted facts, modality/actor/recipient/condition differences, ambiguous
ordering, scenario versus policy values, empty/nonempty forbidden sets, invalid
spans, unauthorized evidence and malformed/missing output. Include positive and
negative controls for every normalization proposed. Synthetic variants are marked
as fixtures, never model observations.

Specify three comparison outcomes: equivalent, substantively different and
unresolved/invalid (with an explicit reason). Preserve claim-to-answer alignment,
required-fact coverage, factual and citation verdicts, behavior, uncertainty and
safety dimensions. Same aggregate fail is insufficient. Category names alone are
insufficient to prove difference or equivalence. Never discard a condition,
extra unsupported claim, missing fact or plausible conflicting reading to match.

**Verify and accept.** Every matrix expectation links to source evidence and a
written rationale; every inventory row is accounted for. Identify labels by
provenance: inherited frozen reference, proposed diagnostic annotation, synthetic
control or named human review. Unsettled semantics remain unresolved, without
positive credit. A change to scoring meaning, reference policy or adoption of
human adjudication requires an explicit decision before dependent implementation;
prepare the exact alternatives and affected cases first.

**Artifacts/review/stop.** Publish `er1-evidence-and-contract.md`, the manifest,
comparison matrix and contract version. Review for cherry-picking and hidden
reference changes. Complete the shared review/commit/push loop. Do not claim
model improvement, relitigate the single ordering case or start a paid pilot.

## ER2: versioned offline comparator and reliability evidence

**Plan.** Freeze ER1's inputs and supported normalization rules. Specify the
baseline failure and all invariants before implementation. This phase changes
offline tooling only; it must not alter frozen evaluators or live runners.

**Implement.** Add a separate deterministic comparator/replay entry point using
the existing validated packet structure where possible. Retain both original
judgments, exact witnesses and a trace of every normalization. Validate packets
before comparison. Use stable source/span/fact bindings rather than case IDs,
company names or special phrases. Do not add a new model call to decide whether
two judges agree. If correspondence cannot be established from defensible fields,
return unresolved instead of inventing a semantic match.

Exercise the frozen ER1 matrix and all compatible saved packets. Include symmetry
and order-invariance checks where the contract promises them, duplicate/missing
claim handling, unsupported extra-claim preservation, invalid witness rejection,
and changed-condition/negation/modality negative controls. Split/combined claims
must remain unresolved unless the declared correspondence preserves every claim.
Equivalent formatting/category changes must not hide a real semantic difference.

**Verify and accept.** All predeclared deterministic controls pass with outbound
network blocked, original hashes unchanged and no case-specific branches. Replay
every inventoried compatible packet or record its incompatibility. Report counts
and denominators for expected equivalence, genuine disagreements, unresolved and
invalid inputs, including false matches and missed matches. Do not collapse this
into a new model accuracy score. Any unjustified equivalence is blocking; any
unresolved mandatory equivalence control prevents offline acceptance. If the
contract is insufficient, record the general limitation instead of accepting a
single-case patch. Preserve qualification failures as failures.

**Artifacts/review/stop.** Publish `er2-comparator-results.md`, versioned code/tests,
machine-readable comparison traces, before/after report and hash verification.
`release_eligible` and target credit remain false. Complete the shared loop before
AD1. Passing establishes offline comparison behavior on declared evidence only;
it does not qualify a live judge, demonstrate semantic correctness on unseen
outputs, or authorize another paid correction cycle.

## AD1: application trace attribution

**Plan.** After ER2 acceptance, define diagnostic cohorts from saved application
evidence. Include successes and failures across the five reported problem families:
premature clarification, scenario/policy confusion, lost conditions, incomplete or
overstated answers, and incorrect validation/quotation handling. Include scope,
memory, conflict and no-evidence controls. Declare inclusion rules and denominators
before summarizing results; do not pool incompatible runtime versions.

**Implement.** Link each case/turn to original intent, resolved conversation
references and corrections, effective authorization scope, retrieval queries,
retrieved passages/ranks, generation context, draft answer, checker decision,
delivered answer and evaluator result wherever saved. Record absent stages as
missing evidence. Trace current caller branches against the captured version;
do not infer that old behavior still exists in current main.

Classify causes as source/document deficiency, retrieval/context selection,
request/memory routing, evidence composition/generation, runtime checking,
offline evaluation, mixed or unresolved. Distinguish observed defect from causal
hypothesis. Cite the exact trace/source and give one falsifiable next comparison
for each hypothesis; multiple causes per case are allowed and counts must say so.
Reuse the matched original12 V4/V6 subset honestly; report recipient controls
separately. Do not treat separately authored suites as controlled before/after data.

**Verify and accept.** Every included case has a trace or explicit missing-data
record and an attribution with confidence/limitations. Check document eligibility
before using passages as evidence. Inspect successful examples for missed errors,
not just rejected answers. Measure correct drafts rejected and incorrect drafts
accepted only where the draft and source-grounded label exist; mark checker rates
unavailable otherwise. Record reviewer provenance and unresolved labels separately.

**Artifacts/review/stop.** Publish `ad1-application-attribution.md`, trace manifest,
case matrix and dimension-level summary. Derive cost from saved receipts and stage
latency from actual timestamps; report unavailable values and keep evaluator cost
separate from user-request cost. Complete the shared loop. No runtime fix, new
embeddings, model call, accepted quality claim or evaluator prompt iteration.

## AD2: controlled diagnostic comparisons and next-action decision

**Plan.** Use AD1 to select the smallest cohort covering the competing causes and
their negative controls. Freeze questions, history, scope, expected facts and
source bindings before comparing. Prefer existing matched evidence; distinguish
replay, synthetic plumbing checks and genuinely new model observations.

**Implement.** Prepare an offline harness for three matched observations:

| Observation | Controlled input / question | Interpretation limit |
| --- | --- | --- |
| Reference evidence | Manually selected sufficient authorized passages with exact citations | Tests generation with adequate evidence only when a real model response exists; not retrieval performance |
| Normal retrieval evidence | Same question/history/scope/model settings with normal retrieved context | A matched difference can implicate evidence selection; unrelated model/config changes confound it |
| Draft -> checker -> delivery | Same saved draft and actual checker/final outputs | Separates checker catches, false rejection and delivery changes where source labels are defensible |

Use existing responses only when their exact inputs/configuration match. Do not
pretend that replaying a draft generated from one context measures generation
from a different context. Record passage selection rationale and verify sufficient
evidence; where the corpus does not contain an answer, retain that limitation.
The reference-evidence arm is an isolated diagnostic, never an authorization bypass
or production retrieval replacement. Permission and quotation checks stay intact.
One matched model pair is diagnostic evidence, not proof of a stable causal effect;
record model variability and predeclare any future sampling before execution.

Offline fixtures may test harness wiring and deterministic calculations/guards.
They cannot produce a live counterfactual. For missing paired observations, publish
a prospective experiment manifest with exact hypotheses, fixed profiles, all
application/embedding/checker/evaluator calls, full token reservations, expected
cost versus hard caps, timing estimate, stop conditions and required decision.
No provider client execution is enabled by default and no credentials are needed.

**Verify and accept.** Validate matched-input bindings, authorization, invalid and
missing-stage handling, receipt accounting and read-only replay. Report each arm
as executed saved evidence, offline fixture or not executed. Report completeness,
unnecessary clarification/abstention, factual/citation correctness, condition and
correction handling, observed safety violations, latency and cost with denominators
and provenance. These diagnostic measures supplement, never replace, release gates.

**Artifacts/review/stop.** Publish `ad2-comparison-and-decision.md`, harness/tests,
paired-input manifest, available comparison report and a ranked recommendation.
Each proposed action must name the supporting cases, uncertainty, affected layer,
smallest change, expected benefit as a hypothesis and how it would be verified.
Choose one first action if evidence supports it; otherwise identify the exact
missing observation or semantic decision. A complete offline report may conclude
insufficient causal evidence. It must not mark unexecuted live comparisons complete.
Complete the shared loop and stop; do not automatically implement the recommendation.

## Cost, quality and decision gates

New model/API spending for planning and the proposed offline phases: **USD 0**.
No service startup is needed unless later justified for a strictly local check;
block provider transports in tests and never read or print secrets for this work.

Preserved closure accounting: cumulative ceiling USD20.75794526; accounted
USD12.65040476 including the same USD0.14820250 unknown-request hold; unreserved
headroom USD8.10754050, untouched. These are recorded authorization amounts, not
verified current provider balance or permission to spend. Do not add historical
remainders, release the hold, infer a top-up or consume the USD4.50 final floor.

If AD2 needs new paid observations, finish the concrete offline harness, manifest
and costed proposal first. Then obtain separate user scope/budget authorization;
an instruction to execute this offline plan alone does not authorize paid work.
Include the complete intended diagnostic stage and any subsequently proposed
qualification/release path, not merely the next cheap request. Preserve synchronous
requests, zero retries, full existing allowances, per-request reservations and
unknown-outcome stops. No guarantee that remaining funds cover future acceptance.

No release gate changes here: full16+3 diagnostic, full32+3 calibration, fresh16
confirmation, fresh60 with at least48 successes, all mandatory safety/citation/
quotation/source-review gates, zero unauthorized retrieval/disclosure, no unresolved
credit, frozen runtime/evaluator/corpus/config/index and isolated fresh-suite custody
remain required for a later release. This plan neither runs nor grants those stages.

For scoring/reference/permission decisions, prepare reviewable alternatives and
counterexamples before asking. Routine implementation choices remain autonomous
within a later authorized phase. Unresolved evidence does not justify removing a
control or repeatedly proposing another paid judge prompt.

## Conditional possibilities: recommendation steps 3-5

These are options for a subsequent separately scoped plan, not authorized phases.

| Possibility | Evidence that would justify it | Required future verification |
| --- | --- | --- |
| Step 3: improve context handling | AD1/AD2 implicates lost user corrections, scenario/policy confusion, or missing rule applicability | Matched development examples and negative controls for actors, recipients, exceptions, modality, arithmetic and memory provenance |
| Step 4: change AI or retrieval components | Documented retrieval misses, poor ranking, missing subqueries, or generation failures despite sufficient evidence | One-variable comparison of surrounding-section retrieval, learned reranking, bounded extra search, model configuration or structured extraction; include latency/cost and safety |
| Step 5: measure resulting experience and consider release | A specific application change has passed development checks and a qualified evaluator/funded release path exists | Useful-answer/completeness and unnecessary-clarification/false-rejection measures plus unchanged independent release gates; no development score promoted to fresh accuracy |

Step 5's diagnostic measures already inform AD1/AD2. Its future full measurement
and release execution remain conditional. More AI, fine-tuning or a multi-agent
architecture is not a default deliverable. Prefer the smallest evidenced change;
preserve all runtime checker criteria rather than removing gates for convenience.

## Planning publication and handoff

This documentation work adds the plan and updates current navigation in AGENTS,
progress and the previous plan/handoff. No ER/AD implementation or phase artifact
is claimed. Required publication checks: local links, scope/gate/accounting
consistency, full intended documentation diff, whitespace and unrelated log
preservation; then reviewed commit verification and push per the shared loop.
Publication verification: reviewed the complete intended documentation including
this new file; checked 169 local links across the five intended files with no
missing targets. Scope, preserved accounting and gate consistency were reviewed.
Git whitespace and unrelated request-log hash checks are required again on the
final staged scope. No application build or runtime test was run because this
change is documentation only. New external model calls/spending: 0 / USD 0.
The unrelated log retains its pre-task SHA256
`f37906539da34d369b0259b014fc061bb2d15b42e31605800d55b724335c176e` and is excluded.

After publication, report the plan location and proposed phase sequence, then
stop. The next possible instruction is to execute the offline ER1 -> ER2 -> AD1 ->
AD2 plan; until then all four phases remain planned.
