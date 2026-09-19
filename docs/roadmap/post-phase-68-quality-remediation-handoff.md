# Coding-agent handoff: quality remediation after Phase 68

Prepared 2026-09-19. Status: planned; implementation has not started. This is the
active evaluation-quality queue, superseding the completed Phase 67-68 queue.
Read `AGENTS.md`, [progress](progress.md), and this document before changing code.
The last completed work is `d3f24e1`; runtime measurement used `89b5a38`.

## Goal and honest starting point

Make the application provide complete, grounded answers when authorized evidence
is available, and the correct clarification or safe non-answer otherwise. Make
the evaluator trustworthy enough to measure that behavior.

- Phase 65: **33/60 (55.0%) historical automated protocol passes**, using its
  original combined rubric. Preserve this result unchanged.
- Phase 68: 60 new cases executed once; **no validated replacement overall success
  rate** because semantic grader errors remain.
- Phase 68 model completeness: 30/38. Source inspection identifies two false
  passes, giving **28/38 (73.7%) provisional answer completeness**, not factual
  accuracy or overall success. Inspection is agent review, not independent human
  adjudication. Do not claim an improvement from 55% to 73.7%.
- Zero recorded permission/scope flags in the latest 60 cases is bounded evidence,
  not proof of universal safety. Calibration passed 18 visible fixtures but did
  not prevent semantic grader mistakes.

Evidence: [results](../phase-68/results.md), [agent inspection](../phase-68/agent-review.md),
[all case evidence](../phase-68/case-review.md), [verification](../phase-68/verification.md),
and [raw artifacts](../../data/evaluation/current-runtime-v3).

## Ordered work

### 1. Repair and validate the evaluator

Create a new version; do not edit frozen historical graders or overwrite reports.
Distinguish factual support, completeness, relevance, semantic citation support,
quotation fidelity, and response behavior. A refusal is not automatically a
factual assertion requiring a citation. True facts can still answer the wrong
question. Missing facts cannot be credited merely because gold evidence contains
them. Classify actual response meaning, not metadata alone.

Add explicit challenge cases for these distinctions, partial answers, generic
refusals, legitimate questions mixed with hostile instructions, and contradictions
between a grader's explanation and its labels. Preserve failed calibration
attempts. Invalid or disputed judgments remain unresolved; schema validity and a
perfect visible calibration score are insufficient evidence of semantic validity.
Validate against separately prepared challenge judgments before live measurement.
Reanalysis of saved answers is allowed only as a separately labeled diagnostic
artifact, with no new application calls and no rewriting of original results.

### 2. Fix confirmed application failures on new development variants

Use traces to distinguish retrieval, evidence-sufficiency, generation and output
validation failures before changing behavior. Preserve permission filtering and
memory-as-context boundaries. Avoid case-ID rules and hardcoded policy answers.

Phase 68 examples (IDs refer specifically to `current-runtime-v3`):

- Incomplete answers: 003, 011, 013, 014, 022, 050, 051, 054, 055, 057.
  Case 011 omits the expense submission deadline and receipt threshold; 013/014
  over-abstain on multi-document questions; 022 unnecessarily clarifies.
- Cases 050/051 reject hostile instructions but omit the legitimate policy answer.
  Reject the attack while answering a separable authorized question when supported.
- Case 041 assumes customer-support context for an ambiguous update question.
  Ask for context instead of inventing a topic.
- Cases 025, 028, 030, 032, 034, 036 expose clarification/refusal/not-found grading
  distinctions. Safe non-answers do not prove the intended response behavior.
- Case 055 has internally inconsistent grader coverage and reasoning.
- Six quotation-fidelity failures require exact source excerpts; keep this distinct
  from semantic support and factual correctness.

The earlier Phase 65 `fresh-019` memory bug already received Phase 67 remediation
(`a7aa503`). Do not confuse its ID with Phase 68 `fresh-019`. Live development still
showed over-abstention despite correct memory topic and sufficient retrieval.

Relevant runtime areas: `apps/api/app/memory`, `reasoning`, `retrieval`, `services`,
`prompts`, and `main.py`. Start from actual traces, not an assumed responsible file.
Use new development cases and local regressions to establish before/after behavior;
exposed holdout cases can explain defects but are no longer fresh evidence.

### 3. Freeze, then measure on another untouched holdout

Only proceed after evaluator validation, runtime development and budget preflight.
Freeze application, evaluator, corpus, configuration and indexed data. Then author
and validate 60 new cases in separate context-isolated passes without old questions,
answers or failure reports. Follow the established sealed-suite custody protocol.
Where separate agents are used, obtain the applicable authorization for delegation;
do not substitute an exposed authoring context and describe it as isolated.

Seal hashes and provenance before execution. Run each case once; preserve raw
answers, retrieval, citations, grader requests/responses and costs. Stop on safety,
custody or budget failures. Do not retry selectively, tune against the new holdout,
silently drop cases or change expected answers to improve the score.

### 4. Publish and complete the operating loop

Publish actual results even if the target is missed, with denominators, unresolved
counts, failure taxonomy, source-linked evidence and offline reproduction commands.
Update the methodology, README and Dev/Admin dashboard together when a new result
is publishable. Label model judgments and agent inspection accurately. The user
agreed with agent findings and does not require a per-case review step; this does
not authorize inventing human review or independent assessor validation.

Use plan, implement, verify, commit, commit review, code review and push for each
bounded phase. Update progress and phase notes before committing. Follow AGENTS.md
for branch handling: main is the established workflow; in a newly created worktree,
ask before switching, merging or committing on another branch. Do not silently
override that rule. Preserve unrelated `data/observability/request-logs.jsonl` edits.

## Predeclared success criteria

Target **at least 48/60 (80%) overall complete, grounded, correctly behaved responses**
on the next untouched suite, with **zero observed unauthorized retrieval/disclosure**
as a hard safety requirement. This is a target, not an achieved or promised score.

Before freezing, specify the exact composite formula: answer-expected cases must
cover all required material facts, remain relevant, have authorized evidence and
semantic citation support for factual claims, avoid unsupported additions, and
use the correct response behavior. Non-answer cases must use the appropriate
clarification/refusal/not-found behavior without unsupported assertions or leakage.
Keep exact quotation fidelity separately reported, rather than conflating formatting
with factual errors. Report every dimension with its applicable denominator.

Count unresolved cases as not passing in the 60-case target denominator, but report
grader uncertainty separately from confirmed application failure. Do not publish
a validated overall score while semantic judge reliability remains unresolved.
An interrupted suite has no completed full-suite score. A different suite is not
a controlled before/after comparison. Missing the target requires honest reporting,
not weaker criteria or tuning followed by rerunning the same holdout.

## Cost and safety constraints

The existing approved cumulative API ceiling is **USD 2.00**, not a new allowance.
Recorded cumulative estimated token spend is **USD 1.19689392**, leaving at most
**USD 0.80310608**. Verify the latest durable ledger before any call. Preserve its
complete historical prefix in the next ledger and keep historical ledgers frozen.
Reserve conservative cost before calls, price all models, disable retries and stop
on unknown outcomes. The last holdout alone added about USD 0.543039; do not assume
remaining funds cover development, calibration, indexing and a new full run.
Request additional explicit approval only if the conservative budget requires it.
Existing credential reuse is authorized; never print credentials.

Do not create billable infrastructure. Production integration and independent
security-assessment gates are outside this quality-remediation task. Preserve all
sealed historical suites and their evidence, including Phases 47-49, 55, 65 and 68.

## Verification and useful entry points

Use existing scripts as design references; introduce versioned replacements where
changes would otherwise invalidate frozen custody. Historical reports must still
replay offline against their recorded revisions. Do not start a live runner merely
to inspect its behavior.

```powershell
python -m unittest scripts.test_evaluation_evidence scripts.test_fresh_eval scripts.test_fresh_report scripts.test_dimension_grader scripts.test_phase67_context_coverage scripts.test_current_dimension_grader scripts.test_current_eval_integrity
python scripts/report_current_eval.py --check
python scripts/report_fresh_eval.py --check
python scripts/report_fresh_eval.py --archive --check
python scripts/report_dimension_reanalysis.py --check
python scripts/build_evaluation_evidence.py --check
python scripts/validate_benchmark.py
```

These 70 local tests and evidence checks passed at Phase 68 closeout. Add focused
tests for each new defect; run compilation and web build when relevant. Do not
describe skipped live checks as passing. The latest Docker image build was not
rerun. See `scripts/current_eval_*`, `scripts/current_dimension_grader.py`,
`scripts/report_current_eval.py`, and `docs/evaluation/reproducing-results.md`.

First action for the next agent: inspect branch/status, read the linked evidence,
record the next bounded evaluator phase in the tracker, and start with offline
challenge cases. Do not spend API budget or run a new holdout before the gates above.
