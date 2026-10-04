# Isolated pre-execution holdout validation

Read only this contract, conversation-final-v3-authoring-contract.md, the frozen corpus under
data/synthetic-documents, data/evaluation/conversation-continuation/final-v3/freeze.json and the
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

Write data/evaluation/conversation-continuation/final-v3/author-validation.json with status
approved/rejected, suite_sha256, freeze_sha256, case_count 60, human_adjudication
false, files_read, provenance, unresolved_findings (empty only if none), and
case_reviews. Every review has case_id, accept boolean, independently derived
expected_behavior, and a source-based reason covering facts, roles and scope.
Approval requires all 60 accepted and no unresolved findings. Preserve initial
suite and rejected validation before any pre-execution author revision; revalidate
the final artifact. Never change a case after the first application call.

Write docs/phase-73/conversation-final-v3-holdout-validation-note.md recording isolation and limitations.
This is agent validation, not expert human labeling. Return paths, hashes, counts,
status and issue IDs/categories only, without case text.

Every required fact must align with the question's requested subject, scope and modality while retaining all material source conditions. A source passage can be broader than the question: do not add facts about other subjects unless requested. Do not upgrade should or may to must, invent source purposes, or copy an unsupported question premise into a fact. Reject ambiguous reference construction before execution. Validate the entire required fact; do not rely on a grader to narrow it later.


Before accepting a required fact, map each clause to a requested question part or
an essential condition on that part. A request for specified fields does not ask
for adjacent purpose/retention statements. A concrete-outcome question need not
ask for the derivation or every general threshold. Broader source text is allowed;
gold facts must remain question-specific without losing necessary qualifications.
The validator must record reference_scope_reviewed: true and a nonempty
reference_scope_reason for every case, including non-answer justifications.
Reject unclear scope before sealing. Do not rely on later grading to narrow an
overspecified reference or alter it after execution.

Question-specific references: do not copy an entire source rule into a gold fact
when the question asks about only one of its alternatives or a specific scenario.
For a selected subject, require the requested outcome or rule and all conditions
on that subject, not unasked neighboring subjects. Separate a source quote (which
may be broad) from the gold fact (which must match the question). Record a
clause-to-question mapping in each reference_scope_reason, including why every
listed alternative is requested. Reject overbroad facts before sealing. Do not
rely on the grader to narrow any sealed fact after execution.
