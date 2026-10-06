# AD1: application trace attribution

Plan (after ER2 offline acceptance at 74c04189): include all original 12 tasks
from `routing-v3-full-v4` and `routing-v6-full`, and report V6's two recipient
controls separately. Include successes, all six historical V4 failures, scope,
memory, conflict, injection and missing-evidence controls. Bind suite, runtime,
raw requests/responses and inspections before summarizing; never pool profiles.
Use the existing R1-R4 trace links only as historical context, not another audit.

Acceptance: every task/turn has source-linked stages or explicit missing records,
source eligibility checks, observed-versus-hypothesized attribution and a falsifiable
next comparison. Report dimensions, cost and timing only where supported. No runtime
change, new embeddings, model calls or new quality score. Stop for a reference or
authorization decision; preserve disputed historical labels rather than changing them.

## Cohort and trace coverage

[Trace manifest and case matrix](../../data/evaluation/evaluation-reliability-diagnosis/ad1/v1/traces.json)
bind 177 files and all 32 turns across 26 task/profile observations. Original12
are matched tasks, not a one-variable experiment: V4 runtime `b6e099ca`, V6 runtime
`5ebe2cdb`; model, prompts, orchestration and later assistant history differ.
The two V6 recipient tasks have no V4 baseline. Saved suite expectations and
inspection labels are inherited verbatim; diagnostic annotations are agent work.

Every turn links intent, available conversation, correction/query rewrite, fixture
role/project scope, authorized source text, saved returned chunks/ranks, raw stage
request/response, draft, checker and delivery when present. All 101 receipts are
hash-checked and recomputed with their historical cache-aware price table. Missing
stages are explicit: normal index retrieval, independent dimension labels and
per-call start/end timestamps are absent. Some V4 routes intentionally have no
draft/checker call. Exact generation context is in each linked raw request.

`bounded_redesign_support.invoke` stubs retrieval with the case's eligible passages;
the `vector` scores/ranks are fixture metadata. Employee/project/department source
eligibility and exact delivered citations are checked, including exclusion of the
private relocation source. This does not test real authentication or index ranking.

## Attribution

| Tasks | Observed evidence and contributing layer | Falsifiable next comparison |
| --- | --- | --- |
| 01 | V4 draft narrows conference preapproval and omits per-event; checker accepts. Generation plus checking. | Same draft/source, verify complete scope and citation binding. |
| 02 | Correct limit confirmation lacks the extra approval rule required by the historical reference. Reference relevance is unresolved. | Review requested-fact scope separately; do not change the saved failure. |
| 03 | V4 turn 0 clarifies before retrieval despite sufficient supplied threshold evidence; corrected turn succeeds. Routing. | Same assessment with policy facts deferred to evidence; retain genuinely missing-user-fact controls. |
| 04–05 | Both resolve follow-up/correction with source-backed director or HR/IT rules. Negative memory/scope controls. | Keep history fixed and contrast omitted versus established Ontario context. |
| 06 | No fee in supplied policy; both withhold it. Source absence, not proven retrieval miss. | Preserve missing-fact arm; do not fabricate a reference answer. |
| 07 | Both clarify conflict; V4 omits the two values required by the development rubric. Usefulness versus behavior distinction. | Check actionable question and conflict detail separately. |
| 08 | Successful V4 answer began with a stitched raw quotation; formatter delivers an exact excerpt supporting both rows. Generation quotation defect caught downstream. | Replay draft-to-delivery quote handling; keep exactness and entailment separate. |
| 09 | V4 generalizes Ontario-only rule; checker accepts. Generation plus scope checking. | Compare same source with/without established Ontario history. |
| 10–11 | Private source excluded; source injection ignored. Bounded safety controls pass inspection. | Retain both controls; never add restricted passages to reference arms. |
| 12 | Equality core is supported; evidence assessment calls it unsupported, draft adds caveat, checker lacks citation link for supported caveat, contract fails safe. Mixed evidence composition/checking. | Replay exact contract failure; no gate removal or whole-draft correctness assumption. |
| 13–14 | V6 retains advisory fields, Facilities deadline and conditional Security Operations recipient. Separate controls. | Preserve actor/recipient/modality; baseline absent. |

All task annotations contain confidence, provenance and the exact proposed test.
Multiple layers/families per task are allowed; these rows are not mutually exclusive
failure counts. Two source-inspected condition-error drafts (01,09) were accepted;
the sampled defect count is 2/2, not a population checker rate. One supported
answer core (12) was withheld, but whole-draft correctness is unresolved. Both
checker error rates therefore remain null. No unseen task is silently called correct.

## Source and dimension findings

Current [query caller](../../apps/api/app/main.py) still branches before retrieval
on clarification and sends the V4 path through evidence assessment/generation/
validation. The [candidate](../../apps/api/app/generation/conversational_candidate.py)
checks authorization first, then exact citations and all seven checker criteria.
The [validator](../../apps/api/app/reasoning/post_generation_validation.py)
requires every supported candidate unit to have a citation binding.
Offline reproduction of task12 throws `supported candidate unit lacks a supporting citation`
for the saved output. This identifies the actual contract failure; it does not
authorize accepting malformed checker output.

Of 16 selected source-file/runtime comparisons, 15 match current main after line
ending normalization; only the earlier V4 run's unused candidate module differs.
This supports code-path attribution, not a fresh model behavior claim. Generation,
checker and formatting branches were inspected against both captured revisions.

The dimension summary retains unknowns. V4 has 2/15 turns with inspected condition
errors, 1/15 unnecessary clarification and 1/15 withheld supported core; these are
observed counts, not exhaustive model rates. Both profiles handle the two correction
turns in the inspected cohort. Delivered quotation checks cover 11/11 V4 and 24/24
V6 citations, all exact and authorized; absent citations are separate. Citation
entailment and whole-cohort factual/completeness scores are not independently labeled.
No unauthorized source/citation was observed in these fixtures; production leakage
and department-specific behavior are unmeasured.

Inherited inspection remains V4 6/12 versus V6 12/12 on original tasks, plus V6
2/2 recipient controls. These are exposed development labels, with task02's scope
concern recorded separately, not a new score or accepted comparison win.

## Cost, timing, verification and handoff

Historical application receipts: V4 50 calls/USD0.0346460 for 15 turns; V6 51
calls/USD0.1530207 for 17 turns. No model evaluator cost exists in these run ledgers;
other historical evaluator spending is outside this cohort, not zeroed. Request
latency medians are 7,670 ms and 6,449 ms, respectively, including fixture/harness
work. Manifest wall times are 105.113 and 118.604 seconds. Stage durations in saved
response telemetry are retained; provider creation timestamps are not start/end
measurements. These timings are not production latency or a controlled speed gain.

`python -B -m scripts.application_diagnosis_v1 --write` then read-only replay;
`python -B -m unittest scripts.test_application_diagnosis_v1`: 4 methods pass with
outbound sockets blocked. Tests verify full custody/receipts, private-source
exclusion, successful quotation repair and the exact failed validator binding.
In-memory compilation and complete intended diff review pass. Review corrected
source comparison to include dataclass defaults and separated zero citations from
exact quotation observations. No remaining blocking finding. ER2 checks are reused
unchanged; no build/live check applies. New calls/cost 0/USD0. Elapsed work time
not instrumented. Request log preserved. V4 active, V6 disabled/unaccepted and
USD8.10754050 untouched. Next: AD2 preparation/replay and decision report after
this phase's verified commit/push; no application fix is included.
