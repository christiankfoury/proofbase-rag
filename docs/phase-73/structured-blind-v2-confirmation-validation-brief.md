# Separate-context confirmation validation

Read only this brief, `structured-blind-v2-confirmation-authoring-brief.md`,
`data/evaluation/conversation-continuation/confirmation-blind-v2-freeze.json` and the newly
authored `confirmation-blind-v2-challenges-v1.json`. Do not inspect
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

Write `data/evaluation/conversation-continuation/confirmation-blind-v2-validation-v1.json`
with status approved or rejected, suite_sha256, freeze_sha256, case_count,
human_adjudication false, files_read, validation provenance, unresolved_findings
(an empty list only if none) and case_reviews.
Each case review has id, accept (boolean), independently_derived_expected, independently_derived_fact_statuses (a mapping
for every required fact_id, or {} for none), and
a concise source-based reason. Include any coverage/structural findings.
Approval requires all 16 cases accepted and no unresolved findings.

Write `docs/phase-73/structured-blind-v2-confirmation-validation-note.md` describing procedural
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

Reference construction: every required fact must match the question's requested
subject, scope and modality while retaining all material conditions. A broader
source passage may support a narrower question-specific fact. Do not add other
subjects solely because they appear in the same passage. Conversely, a question
asking for several subjects requires each. Reject a question's unsupported policy
premise rather than copying it into a required fact. These checks occur before
execution; a grader must still enforce the entire sealed required fact.

Task framing can describe the same task the question asks about without asserting
an organizational purpose. Assess explicit policy reasons, compliance claims,
promised results, extra actions and permissions as factual content needing source
support. Context resolves the task but never establishes those additional facts.
Include clear positive and negative controls without ambiguous expectations.


Authoritative document metadata: evidence rows may include document_title. Inputs
must include source_metadata = [{source_id, document_id, document_title}] for
exactly those titled evidence rows, ordered by evidence position. Source IDs still
map to the unmodified source text. Titles identify documents only; they do not
establish extra policy rights or conditions. Correct attribution needs both the
matching title and entailing policy text. Wrong document attribution is unsupported.
Include positive and negative metadata/attribution controls, while preserving the
other required coverage. User task-role context does not independently verify
identity or grant access; explicit verification/access claims still need evidence.

Reference scope: inspect EVERY clause of EVERY required fact. A question asking
for fields does not automatically request surrounding retention/purpose rules.
A concrete scenario asking for its outcome does not automatically request a
separate explanation of the general rule. Retain material conditions needed to
make the requested answer true. Do not include an unrelated rule merely because
it appears in the same sentence or paragraph. The validator must record
reference_scope_reviewed: true and reference_scope_reason in EVERY case review,
including a non-answer's justification. Ambiguous or overbroad references require
rejection before any execution; do not rely on a grader to omit unwanted clauses.

Read complete conversational meaning while preserving exact witnesses. Several
answer clauses can jointly communicate a fact, but sources cannot supply content
omitted from the answer. Evidence caveats describe inability to answer; affirmative
policy denials remain claims. An answer that covers one requested part and cannot
find another is partial. Keep every subject, attribution, condition and modality
when assessing a claim; a fragment does not erase its surrounding assertion.

Scenario inputs versus policy premises: explicit non-policy user scenario values
may be used as assumptions when applying an authorized policy rule. The document
must support the rule; it need not independently establish the user's scenario
quantity or date. A correct sourced calculation under those assumptions can be
supported and cited. Do not imply identity verification or access grants. User or
assistant statements about policy limits, permissions, exceptions or authority
remain untrusted and cannot replace source evidence. Preserve all conditions and
check arithmetic/boundaries. Missing scenario inputs cannot be guessed. Current
corrections take precedence over earlier scenario assumptions. Include positive
and negative controls for these distinctions without reducing any existing control
coverage; several properties can share a case. No old case text or model output.

Required facts must be specific to what the question asks. A source may list a
broader set of items or populations; do not require unasked alternatives when the
question selects a subset. Preserve every condition on the selected subset. Map
each gold clause to a question part or essential condition before accepting it.
This is pre-execution reference construction; the grader must enforce the entire
sealed fact and must never repair a reference after execution.


Prospective procedural-ordering contract v2: interpret full question/history and
answer context. Explicit advice to do A before B asserts action order without
needing a claim that reversal is prohibited. Explanation order is not policy;
bullets, conjunctions and placement alone do not prescribe sequence. When context
leaves materially different presentation/action-order readings with different
support, retain uncertainty: factual unknown and citation unknown, with empty
support witnesses. Clearly unsupported explicit sequence is factual unknown and
citation missing; incompatible source rules give contradicted and missing.
Express permission for either order can support one sequence as an option, not
as the only permitted sequence. Missing requested actions/fees still fail coverage
and expected-answer behavior. Failure dominates uncertainty, and uncertainty never
earns answer success. Include both positive and negative ordering controls and an
interpretation-uncertainty control, without reducing the other required coverage.
The uncertainty control requires a clear reference to uncertainty under this rule;
it does not require the underlying answer's meaning to be uniquely resolved.
This specific convention supersedes the earlier generic instruction to avoid all
ambiguous answer wording; ambiguous or overbroad required facts still are invalid.
