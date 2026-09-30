# Separate-context confirmation validation

Read only this brief, `confirmation-v15-authoring-brief.md`, the v15 freeze
record and the newly authored `confirmation-challenges-v4.json`. Do not inspect
evaluator code, prompts, earlier suites, results or runtime failures. No external
calls or Git operations. This review occurs before evaluator execution.

Independently derive all eight expected labels for every case from the supplied
rubric and case text. Check entailment, completeness, relevance, speech act,
citations, literal quotations and the composite separately. Verify that required
facts follow from the synthetic policy, conversational history supplies only
reference context, and evidence/IDs/citations match. Check required control
coverage, at least two conversational cases and two multiple-source cases.
Reject unclear or incorrect expectations; do not accept them merely because
they are supplied. Do not simplify cases to favor a particular evaluator.

Write `data/evaluation/quality-completion-v1/confirmation-validation-v4.json`
with status approved or rejected, suite_sha256, freeze_sha256, case_count,
human_adjudication false, files_read, validation provenance, unresolved_findings
(an empty list only if none) and case_reviews.
Each case review has id, accept (boolean), independently_derived_expected, independently_derived_fact_statuses (a mapping
for every required fact_id, or {} for none), and
a concise source-based reason. Include any coverage/structural findings.
Approval requires all 16 cases accepted and no unresolved findings.

Write `docs/phase-71/confirmation-v15-validation-note.md` describing procedural
isolation and review limitations. This is agent review, not human adjudication.
Return only paths, hashes, count, approval status and issue IDs/categories to
the parent. Do not return case content. If revisions are needed, preserve the
initial suite and rejected validation artifact before author revision, and
revalidate the final artifact before execution. Never alter a case after the
first evaluator call.

Apply the ordered behavior rule explicitly in every case review: derive prose
behavior, then required-fact completeness, then its override, then overall.
Check that a failure dominates unresolved in the composite. Do not approve
unresolved behavior for an expected answer with failed completeness.

Independently audit fact statuses: other-topic/entity assertions do not contradict
the omitted requested fact. Same-policy explicit incompatible assertions do.
Do not accept a wrong intermediate status because it reduces to the same failure.
Apply the temporal rule to current permission versus explicit past/change claims.
