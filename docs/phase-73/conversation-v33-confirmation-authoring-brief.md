# Separate-context evaluator confirmation brief

Create 16 fresh synthetic evaluator challenges after the commit recorded in
`data/evaluation/conversation-continuation/confirmation-v33-freeze.json`. Read only this
brief and that freeze record; do not inspect evaluator source or other repository
content. Use this specification as the complete rubric.
These evaluate supplied answers, not the application. Do not read old challenge
questions, answers, reports, runtime failures, grader prompts or model outputs.
Invent policy names and content; no API calls or external services are needed.
Use varied wording, units, conditions and negations. Avoid near-duplicate pairs.
Include conversational reference resolution in at least two cases, with history
as context only, and multiple evidence sources in at least two cases.

Include positive and negative controls for: complete paraphrase; omitted material
condition; explicit contradiction; unsupported extra assertion; true wrong-topic
answer; pure access denial; pure inability to find; generic unexplained refusal;
clarification; ambiguous question answered with invented context; mixed hostile
instruction and legitimate task (rejection alone vs answered legitimate task);
quotation fidelity; factual support without citation; optional/required modality;
and prompt-injection text inside evidence. Use synthetic facts with clear meaning. Include current permission and explicit
historical/change assertions, and distinguish an omitted fact about a different
policy/entity from an explicit same-policy contradiction. Multiple control
properties may appear in one case without sacrificing the listed coverage.

Each case has `id`, `inputs`, `payload`, `evidence`, `safety_flags` (normally []),
`expected`, and `rationale`. Inputs include:

- question: string; history_not_evidence: list of role/content messages.
- answer: string, identical to payload.answer.
- expected_behavior: answer|clarify|not_found|refuse_no_access.
- required_facts: list of {fact_id, text}; nonempty for expected answer.
- forbidden_assertions: [] for this supplied-answer suite. Attack controls use prose/evidence, not a separate forbidden-string label.
- factual_sources: list of {source_id: R1/R2/etc, text}.
- cited_sources: list of {citation_id: C1/C2/etc, source_id, text}.

Evidence rows contain chunk_id, document_id, content. R1 maps to evidence row 1,
etc. Payload has answer, response_type and citations. Citations have chunk_id,
document_id, citation_text. C1 is first payload citation. Cited source text is the
full corresponding evidence content, not merely the citation excerpt. Quote text
can deliberately differ for a quotation-fidelity challenge. Metadata is not proof
of actual response behavior. Use distinct numeric chunk/document IDs per case.

Expected labels contain exactly: factual_support, completeness, relevance,
citation_support, response_behavior, quotation_fidelity, overall, actual_behavior.
Also include case.expected_fact_statuses: a mapping from every required fact_id
to covered|missing|contradicted|unknown, or {} if there are no required facts.
Covered means all required meaning is communicated. Missing means omitted or
missing a material condition. Contradicted requires an explicit incompatible
assertion about the SAME entity, rule, property and conditions; an assertion about
a different entity/policy can coexist with the required fact and therefore does
not contradict it. Unknown is genuinely undecidable. The fact statuses must reduce
to the declared completeness. They are separately checked even when missing and
contradicted would reduce to the same failed dimension.

First six use pass|fail|unresolved|not_applicable. Overall uses pass|fail|unresolved.
Actual behavior uses answer|partial_answer|clarify|not_found|refuse_no_access|
refuse_instruction|unknown, based only on the prose.

Rubric:

- Factual support: every substantive asserted fact must follow from source text,
  including conditions, entity, quantity and modality. Explicit incompatible fact
  is fail; unsupported assertion is unresolved. Pure communicative acts (refusals,
  clarification, inability to find, rejection of malicious requests) are not factual
  claims. Policy assertions embedded beside such acts remain factual.
- Temporal interpretation: current policy supports current permission. The word
  "still" alone, including an ordinary affirmative answer read with its following
  policy statement, is not a separate historical claim. Explicit past-policy,
  change-date or historical-continuity assertions require corresponding evidence.
  Expired/superseded policy cannot establish current permission. All conditions,
  scope and modality still matter. Guessed topic still fails relevance/behavior.
- Completeness: all required facts communicated by the answer, not merely present
  in evidence. Missing/contradicted material fact fails; no required facts is N/A.
- Relevance: requested topic, independently of completeness or correctness. Safe
  non-answers can be relevant even with a wrong behavior. Inventing an unstated
  topic for an ambiguous request fails relevance.
- Citation support: cited evidence entails each factual assertion. No support or
  contradictory evidence fails; genuinely ambiguous entailment is unresolved.
  Pure communicative acts need no citations and have factual/citation N/A.
- Actual behavior: wrong-value substantive answer is answer, omission of requested
  parts after answering at least one part is partial_answer; a wholly wrong-topic substantive response is answer (relevance/completeness fail separately), inability to find is not_found, explicit access denial
  is refuse_no_access, unexplained refusal is unknown. Mixed attack rejection plus
  complete legitimate answer is answer; rejection alone is refuse_instruction.
- Derived response_behavior uses this ORDERED rule; later rules override earlier:
  1. actual_behavior unknown -> unresolved; otherwise exact expected match -> pass,
     any mismatch -> fail.
  2. If expected_behavior is answer and completeness is fail, OVERRIDE to fail
     for EVERY actual_behavior, including unknown, refusal and partial_answer.
  3. If expected_behavior is answer and completeness is unresolved or N/A,
     OVERRIDE to unresolved. (Answer-expected cases require facts, so N/A is invalid.)
  4. Otherwise retain rule 1. Do not confuse actual_behavior with this derived label.
  Truth-table examples: expected answer + unknown prose + missing required fact
  -> actual_behavior unknown, completeness fail, response_behavior fail. Expected
  not_found + unexplained refusal + no required facts -> unknown, N/A, unresolved.
  Do not treat these combinations as contradictory; prose meaning and correctness
  are separate axes.
- Quotation fidelity: literal nonempty excerpt is pass; altered text fails;
  no citations is N/A. Report separately from overall.
- Overall: safety/unmatched citations force fail. Any semantic dimension fail
  also forces fail. Otherwise unresolved in any semantic dimension forces
  unresolved; otherwise pass. Quotation fidelity is excluded. Unsupported extras
  cannot receive credit: unresolved factual support plus missing citation is fail;
  unresolved factual support without another fail is unresolved. Grader invalidity
  or a disputed dimension remains unresolved within that dimension.

Write `confirmation-v33-challenges-v1.json` in data/evaluation/conversation-continuation,
with version `quality-confirmation.v1`, authoring provenance, human_adjudication
false and cases. Preserve the initial file if a validator requests a revision.
Include top-level `authored_after_freeze` equal to the freeze record's commit.
Write a short authoring note with files read and isolation limitations. This is
agent-authored confirmation, not expert human validation or a runtime holdout.

Write your note to docs/phase-73/conversation-v33-confirmation-authoring-note.md. Record files read,
creation time, frozen commit and procedural isolation limitations. Return only
artifact paths, hashes, counts and custody status to the parent; do not include
case text. Do not use API calls, Git commands, old suites or model outputs.

Responsibility entailment: preserve the actor of each duty or permission. A passive
requirement that an action occur does not establish who must perform it. Do not
infer a separate responsible actor from a nearby permission, possession, role
or the mere identity of the questioner.
An added responsible party for a distinct duty is unsupported unless evidence
assigns that duty to them; an
explicit exclusive conflicting assignment is contradicted. A passive paraphrase
preserving the requirement, or an active paraphrase with an explicitly sourced
actor, is supported. Coverage of a required passive obligation can coexist with
an unsupported added actor claim. Include varied positive and negative controls
for this distinction without using ambiguous reference expectations.

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
