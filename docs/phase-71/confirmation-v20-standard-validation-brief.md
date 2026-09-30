# Separate-context confirmation validation

Read only this brief, `confirmation-v20-standard-authoring-brief.md`,
`data/evaluation/quality-completion-v1/v20-standard-freeze.json` and the newly
authored `confirmation-challenges-v11.json`. Do not inspect
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

Write `data/evaluation/quality-completion-v1/confirmation-validation-v11.json`
with status approved or rejected, suite_sha256, freeze_sha256, case_count,
human_adjudication false, files_read, validation provenance, unresolved_findings
(an empty list only if none) and case_reviews.
Each case review has id, accept (boolean), independently_derived_expected, independently_derived_fact_statuses (a mapping
for every required fact_id, or {} for none), and
a concise source-based reason. Include any coverage/structural findings.
Approval requires all 16 cases accepted and no unresolved findings.

Write `docs/phase-71/confirmation-v20-standard-validation-note.md` describing procedural
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

For every factual assertion, independently check its actor, action, object, scope,
conditions, quantity and modality against explicit source evidence. A passive
obligation does not assign its performance to a nearby actor. Distinguish a safe
passive paraphrase and an explicitly sourced actor from an invented responsible
party, and unsupported agency from an exclusive conflicting duty. Record that
check in the relevant case reasons; do not approve a full-support label merely
because the answer covers required passive facts.

Coverage is semantic: equivalent active/passive grammar and generic plural duties
can communicate per-item requirements without repeating the words each/every.
Preserve actual quantifiers and conditions; explicit some/most, exemptions or
optional wording do not establish an unconditional every-item duty. Validate
meaning in question context, never word overlap alone.

Task-context participant: when a source constrains an action and the question asks
how/when the user performs that SAME action, ordinary second-person instructions
can preserve the source meaning without a new responsibility assignment. This
does not grant permission or assign a separate action such as inspection, audit,
approval or recordkeeping to the user. Explicit actor restrictions/prohibitions
always prevail over a user premise. Guessed topic fails relevance/clarification
independently; it does not make a correctly stated policy fact unsupported. Check
action, object, conditions and actor limitations when deriving every reference.

Prerequisite and evidence-scope distinctions: judge the meaning communicated in
the explicit question context, preserving all actual conditions. Direct
prerequisite answers can use equivalent temporal wording without repeating
"only". A partial example, bypass, optional condition or omitted material condition
does not establish the whole prerequisite. A statement that an excerpt does not
identify an actor is missing evidence, not a prohibition. Explicit exclusions or
exclusive conflicting assignments are negative evidence. Keep these distinctions
independent of coverage, citations and response behavior. Include clear positive
and negative controls; avoid ambiguous references.

Actor nouns preserve their contextual referent, not literal word choice. Ordinary
occupational synonyms may denote the same workplace group when the supplied
context does not distinguish classes. Do not invent external employment classes
to reject equivalent wording. Explicit category definitions, department scope,
exclusions and separate duties remain binding. Compare the user-selected topic
from question/history with the topic actually answered; a true policy about a
guessed object fails relevance. History can resolve references, never policy truth.
