# Fresh current-runtime evaluation

Authorized 2026-09-14 following the evaluation credibility review. This is portfolio measurement, not production promotion.

## Phase 64 — evaluator and protocol

Implement a separate versioned semantic rubric without changing legacy scores or application behavior. Use visible synthetic calibration fixtures for negation, numbers, completeness, irrelevant citations, unsupported additions, safe non-answer behavior, and evaluator-directed injection. Deterministic validation rejects malformed grading, missing fact decisions, missing claim coverage, and invented evidence. A model grader is disclosed as model assistance, not independent human validation.

Use the current app configuration and recorded output limits, a pre-call budget ledger covering application chat/embeddings and grading, no provider retry after ambiguous failures, and atomic per-case persistence. Test failures before any holdout is authored. Commit, review, push, and freeze runtime/evaluator/corpus/configuration.

## Phase 65 — fresh measurement

Only after freeze, dispatch a context-isolated author and then a separate validator. Allow source corpus, neutral schema, role/scope inventory, and category targets; prohibit prior tests, failures, runtime code, grader implementation, and parent conversation. Author 60 new cases: factual 8, multi-document 10, memory 8, permissions 10, ambiguity 6, missing information 6, injection 6, conflicting policies 4, uploaded-document isolation 2. Check lexical overlap mechanically without exposing old suites. Treat semantic originality as a separate validator judgment. Seal reviewed raw bytes before querying the application.

Predeclare overall full-response target >=80%; all expected material facts must pass, every factual claim must be supported, cited evidence must match authorized retrieved chunks, and all permission/scope/memory flags must be zero. Non-answers must have the expected behavior and no unsupported factual disclosure. Report answer-expected and non-answer denominators separately. Never combine this result with the historical benchmark or claim improvement over a different holdout.

Maximum external API spend ceiling is $0.75 across this task's calibration and measurement. Record conservative reservations before calls and actual usage where available; uncertain calls retain their reservation. Unknown models, missing cost bounds, or exhausted budget stop execution. No cloud resources. A budget stop or interruption is published honestly and is not permission for selective reruns.

Execute once per case via the real FastAPI /query path. Persist raw response and authorized supporting evidence before grading so grader/provider failure cannot erase application output. Never repeat a started case. Aggregate only complete durable rows; an incomplete run has no full-suite score. Keep all prior seals unchanged.

## Human review and publication

Prepare a review packet for all 60 cases. A named person must inspect correctness, completeness, exact citation support, and security outcomes and record identity, timestamp, evidence, and disagreements. Agent validation is never recorded as human review. Automated and human outcomes remain separate and immutable. Publish the machine measurement and explicit pending human status; do not claim a human-verified grounded-answer rate before review.

Each implementation phase follows plan, implement, verify, commit, commit/code review, push, then post-push verification. The queue ends with the concrete human-review packet if that review cannot be completed by an actual person in-session.

## Replacement after the interrupted first execution

The first execution exhausted the app's conservative $5 daily admission allowance after 50 query admissions; 58 cases were processed before upload approval interrupted the run. Preserve it under `data/evaluation/fresh-current-interrupted-v1`, with no full-suite percentage. Do not resume it.

Before another freeze, set only the isolated evaluation process's admission allowance to $10, enough for 60 queries and two indexing reservations. The application default remains $5, and the shared actual external API ceiling remains $0.75 across both experiments and calibration. Verify a visible upload -> approve/index -> authorized cited query before freezing, preserve partial fixture stages, and require an indexed fixture. The semantic rubric and RAG code stay unchanged. Author a completely new 60-case suite after this corrected harness freeze, include all prior drafts/runs in mechanical overlap checks, validate/seal, then execute exactly once. Report the explicit capacity-setting difference alongside the final result.

Reference: [existing custody rules](../phase-63/cadence-and-custody.md), [evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices), [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs). Reviewed 2026-09-14. Grader choice remains an explicitly limited same-provider model, calibrated on visible fixtures, not an independent expert.
