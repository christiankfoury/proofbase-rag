# Phase 72: confirmed runtime defects

Development investigation started on main at `c240cd1` while Phase 71 calibration
is running, as permitted by the active plan. No sealed case or failed grader label
defines expected application behavior. The prior Phase 70 generation handoff and
authorized citation-ID fixes are present and must not be reimplemented.

Goal: preserve complete user requests through memory and multi-question retrieval,
and keep numeric validation accurate. Scope: backend query context, decomposition
fallback and deterministic literal validation; no App/API schema changes.

Predeclared development checks reproduce on current runtime before editing:

- Memory follow-ups with conditions or a second question must retain the current
  user's exact request; canonical search expansions must not replace it. Assistant
  claims remain excluded from user-context anchors, and memory is not evidence.
- Empty/blank decomposition must fall back to the original question and still
  perform role/project/department-filtered retrieval. Invalid output must not
  turn into a successful empty search.
- Numeric support cannot be established by a substring of a different amount or
  duration. Correct formatting variants stay supported. Citation-ID metadata
  handling and semantic/fail-closed validation stay active.
- Clarification for unresolved intent, no-evidence abstention and permission
  refusal remain controls. Do not change attack-handling policy speculatively.

Required artifacts: comparable offline before/after traces on newly authored
development cases, focused regressions, relevant memory/multi-document/permission/
citation checks and honest limitations. Passing these is not overall accuracy or
fresh generalization evidence. Live development checks, if needed, require their
own complete cost/call preflight after evaluator calls settle.

Acceptance: source-confirmed defects above fixed with negative controls passing;
no benchmark expectation changes. Stop at that bounded scope. Additional numeric
negation/formatting hypotheses need separate evidence and must not weaken guards.

## Results and review

The pre-change runtime reproduced eight failures in 14 boundary probes (six
controls passed). The final reviewed runtime passes all 14. These are deterministic
development checks with mocked provider output and retrieval; **not an accuracy
score, live model comparison or a fresh generalization result**.

| Root cause | Change | Negative controls |
| --- | --- | --- |
| Canonical memory rewrite replaces the current request | Keep the complete original follow-up before the canonical search expansion. Conditions, exceptions and second questions survive into retrieval. | Assistant assertions excluded from user anchors; attack text retained for assessment; no memory evidence/citation changes. |
| Empty/blank JSON query list accepted as success | Treat empty sanitized decomposition as invalid and fall back to the original query. Trim valid subqueries and retain the three-query bound. | Invalid JSON shapes use the same fallback; role/project/department parameters stay intact. |
| Numeric support uses substring matching | Require numeric boundaries; preserve word/sentence boundaries while normalizing grouping commas, whitespace and currency spacing. | 50 versus 500, 20 days versus 120 days, and 25 versus 25.5 rejected before semantic calls; valid currency/duration formatting remains supported; semantic/citation failures and timeouts still fail closed. |

Evidence: `data/evaluation/quality-completion-v1/runtime-before.json` and
`runtime-after-reviewed.json`, with runtime commit/source hashes and each observed
result. `runtime-after.json` preserves the first passing implementation before
review found that removing whitespace could mistake sentence punctuation for a
decimal boundary. The reviewed trace supersedes it; no old trace was rewritten.

Commands/results:

- `python scripts/quality_runtime_development.py --write before`: 6/14 passing.
- `python scripts/quality_runtime_development.py --write after-reviewed`: 14/14 passing.
- `python -m unittest scripts.test_quality_runtime scripts.test_phase67_context_coverage scripts.test_portfolio_finish`: 23 tests passed; the subsequently added durable shared-regression wrapper passed separately with `python -m unittest scripts.test_quality_runtime.RuntimeQualityTests.test_shared_memory_multidocument_and_citation_regressions_offline` (one test running all four existing suites).
- `python scripts/test_phase54_post_generation_validation.py`: passed, including citation authorization, semantic rejection and timeout fail-safe.
- `python scripts/test_phase52_request_assessment.py` and `python scripts/test_phase53_evidence_assessment.py`: passed, including strict ambiguity, permission-filter-before-evidence-before-generation, and shared streaming/non-streaming guards.
- Existing Phase 39/46/48 and Phase 35 citation checks passed under an offline wrapper mocking audit writes and forbidding AI clients; the same wrapper is preserved in `test_quality_runtime.py`.
- Changed Python compilation and Git whitespace checks passed. Historical Phase 65/66/68 replay and benchmark v1.1 validation from Phase 71 reused: no sealed artifacts, benchmark expectations or evaluator reducers changed.

The first direct Phase 46 invocation waited on audit database I/O; it was stopped
and rerun with that unrelated side effect mocked. Existing local Postgres/Redis
containers were started without resetting data. No Docker image, frontend build,
full live RAG suite or external AI call was needed for these backend-only boundary
fixes. No API/data-model contract changed. Remaining negative-number/premise
interpretation, numeric words, answer omissions and broader routing quality are
not claimed solved. The full semantic validator still decides claim meaning;
numeric presence alone never establishes entailment.

Compact handoff: source-confirmed fixes, focused verification and semantic diff
review complete; no unresolved blocking finding. Commit reference is the commit
containing this note (recorded in the next tracker update). Phase 73 still requires evaluator
readiness and the full runtime/corpus/config/index freeze. External calls in this
phase: zero. Unrelated request logs preserved. Initial implementation/review took
approximately 15 minutes, overlapping Phase 71 provider time; not an SLA.
