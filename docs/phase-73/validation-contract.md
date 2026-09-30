# Isolated pre-execution holdout validation

Read only this contract, the Phase 73 authoring contract, the frozen corpus under
data/synthetic-documents, data/evaluation/current-runtime-v4/freeze.json and the
new holdout.json in that folder. No old questions, results, runtime/evaluator code,
parent conversation, model outputs, API calls or Git operations.

Independently check every case's requested behavior and every material required
fact against exact corpus quotations and document role frontmatter. History is
context only. Check scope, complementary multi-document evidence, actual policy
precedence, permitted/denied roles without assumed inheritance, missing-information
justifications, injection controls, and novel separate-project upload fixtures.
Review diversity, difficulty/rationale, all category counts and structural fields.
Reject unclear cases and unsupported expectations; do not simplify them for an
implementation. Mechanical historical overlap is performed separately by root.

Write data/evaluation/current-runtime-v4/author-validation.json with status
approved/rejected, suite_sha256, freeze_sha256, case_count 60, human_adjudication
false, files_read, provenance, unresolved_findings (empty only if none), and
case_reviews. Every review has case_id, accept boolean, independently derived
expected_behavior, and a source-based reason covering facts, roles and scope.
Approval requires all 60 accepted and no unresolved findings. Preserve initial
suite and rejected validation before any pre-execution author revision; revalidate
the final artifact. Never change a case after the first application call.

Write docs/phase-73/holdout-validation-note.md recording isolation and limitations.
This is agent validation, not expert human labeling. Return paths, hashes, counts,
status and issue IDs/categories only, without case text.
