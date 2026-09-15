# Phase 67: context and retrieval coverage remediation

## Scope and evidence

Source inspection of Phase 65's wrong-topic response showed that the memory
selector collapsed a user correction to a keyword in an excluded phrase.
Separately, incomplete answers motivated inspection of multi-question routing
and evidence merging. These are development findings, not new holdout scores.
No sealed questions, answers, labels, grades, or source documents were changed.

The runtime now preserves corrections, exclusions and multiple named topics as
user context. The most recent user topic takes precedence over an older known
keyword; an explicit return to the first topic respects the actual first user
message. A bounded sequence of user messages anchors anaphoric follow-ups.
Existing simple positive-topic rewrites remain available. Memory still cannot
grant access or serve as cited source evidence.

Independent interrogative clauses now enter multi-document retrieval even if
they do not match existing domain pairs. For model-decomposed searches, merging
reserves one available result per subquery before filling the ten-chunk limit.
This prevents cross-query score differences from eliminating one subquestion.
The same role, project and department configuration reaches every search.

Historical dimension-report replay now checks the recorded runtime revision,
rather than requiring the current application to equal the old freeze. All
other evaluator, source-response and artifact hash checks remain enabled.

## Verification

Development tests use different questions and synthetic retrieval results;
they never call the sealed suite. Before implementation, the initial seven
test methods had six failing methods (seven failed assertions including two
subtests); only the existing positive-topic behavior passed. After the change,
all eight methods pass, including an additional follow-up chain check.

- Eight context/coverage tests and 15 dimension tests pass.
- Phase 39 and Phase 46 regression scripts pass with OpenAI chat and embedding
  entry points patched to reject external calls.
- Both historical Phase 65 and Phase 66 report checks pass unchanged.
- Additional final verification is recorded in the progress tracker.

No new API calls were made in this phase. Cumulative estimated API cost remains
USD 0.5687728 against the existing USD 0.75 ceiling.

## Limits and review

These checks establish the local failure mechanisms and their regression fixes.
They do not prove that all incomplete answers are repaired. Decomposition can
still miss an intent; existing source plans may be incomplete; retaining one
result does not guarantee it is relevant or sufficient. More questions may now
incur decomposition, embedding and generation cost. No factual-accuracy or
generalization improvement is claimed.

Self-review checked preservation of exclusions, first/latest-topic precedence,
existing positive-topic behavior, deduplication, the result cap, and propagation
of role/project/department scope. Retrieval permission enforcement and citation
validation were not changed. Live endpoint answer quality and broader permission
measurement remain pending under the next evaluation phase.

## Next phase

Follow `docs/roadmap/post-phase-66-evaluation-plan.md`. The current semantic grader
is diagnostic only. A new runtime measurement must follow development checks,
evaluator validation, runtime/evaluator freeze, separate fresh authoring and
validation, sealing, and one-shot execution. Do not rerun exposed held-out cases
and call that generalization.
