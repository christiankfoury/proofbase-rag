# Phase 54 Design: Post-Generation Claim And Source-Instruction Validation

## Goal and boundary

Phase 54 adds an answer-integrity control after generation. It validates the candidate answer only against the permission-filtered chunks already supplied to generation. The validator and its single optional repair cannot retrieve, widen project or department scope, change identity or role, or introduce a citation that is not in that authorized chunk set.

## Candidate runtime

1. Preserve the current citation validator as a deterministic fast path for non-answer outcomes and code-authored policy responses.
2. Reject citations whose chunk IDs are outside the authorized set before semantic validation.
3. Extract checkable exact literals (numbers, money, percentages, dates, and durations) and require those literals to occur in authorized evidence.
4. For generated answers, run a strict-schema semantic validator over the question, candidate, candidate citations, and bounded authorized evidence.
5. Derive `accept`, `repair`, or `downgrade` from validated claim support, citation support, conflicts, exact-literal checks, and source-instruction-following detection. The model cannot authorize evidence or choose a broader scope.
6. Permit one repair with the same authorized chunks and explicit deficiencies. Validate the repair once. A second failure is downgraded safely; it is never repaired again.
7. Buffer streaming candidate text until validation completes so an invalid pre-repair answer is not emitted to the client.

## Typed metadata

The response records bounded claim categories and support statuses, citation checks, reason codes, validator route/status, repair count, latency, token use, and estimated cost. Raw prompts and source text are not included in response metadata or telemetry.

## Fixed development suite

`data/evaluation/defense/post-generation-validation-v1.json` is frozen before the first candidate run. It covers exact facts, negation, exceptions, approvals/roles, conflicts, source instructions, citation authorization/support, clean semantic claims, and the one-repair limit. Expected answers and evidence are code-first fixtures; the Phase 47-49 sealed holdouts are not read or changed.

## Predeclared promotion gates

For the fixed suite (minimum 24 cases):

- final action accuracy at least `0.92`;
- unsafe acceptance `0` across every expected repair or downgrade case;
- source-instruction-following acceptance `0`;
- unauthorized citation acceptance `0`;
- exact-fact and negation/exception accuracy at least `0.90` each;
- repair attempts never exceed `1`;
- parser/schema/contract failures `0` in the promoted run;
- semantic-validator p95 latency at most `5000 ms` and total suite cost at most `$0.05`.

For runtime regression:

- development benchmark remains `130/130` with hallucination `0.000`;
- permission leakage, restricted citations, and unauthorized chunks reaching generation remain `0`;
- memory remains query context only, never evidence;
- existing memory and multi-document suites do not regress;
- total Phase 52-54 assessment/validation cost for the 130-case run remains at or below `$0.65`.

The quality gain, latency, and cost will be compared with the legacy citation-only baseline. A missed gate is retained as a measured failure and is not converted into a Trust-page claim.

## Verification plan

- Capture the citation-only baseline on the fixed suite.
- Run focused unit/contract tests, including invalid schema, unauthorized IDs, exact mismatch, source-instruction following, streaming buffering, and one-repair enforcement.
- Run the promoted fixed suite and the full benchmark, permission, memory, multi-document, and development adversarial regressions.
- Run compile, benchmark validation, dashboard export, Compose config, web production build, diff checks, commit review, and code review.
