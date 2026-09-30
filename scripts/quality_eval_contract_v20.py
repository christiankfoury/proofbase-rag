"""Preserve sourced actor scope without inventing an unstated role taxonomy."""
from scripts import quality_eval_contract_v19 as previous

VERSION = 'answer-dimensions.v20-candidate'
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
dimensions, validate, summarize = previous.dimensions, previous.validate, previous.summarize
candidate_judgments = previous.candidate_judgments

ACTOR_PARAPHRASE_RULES = """
Preserving an actor means preserving its communicated referent and scope, not
requiring identical nouns. Judge ordinary occupational paraphrases in this policy
and question context. For example, staff/employees can denote the same identified
workplace group when no source or context distinguishes those categories. Do not
invent an external employment taxonomy or speculate about additional categories
such as contractors solely to reject an otherwise equivalent paraphrase.
This does NOT authorize broadening scope or substituting a different role. Retain
named teams, departments, restrictions, qualifiers and explicit category definitions.
If the source/context distinguishes staff from contractors/vendors, identifies a
restricted subgroup, or the answer explicitly includes an excluded class, preserve
that distinction. A real broader-scope claim remains unsupported or contradicted
as the source warrants. Do not infer responsibility for a separate action from a
synonym; all existing actor, permission, condition and citation rules still apply.
"""
TOPIC_CHECK_RULES = """
Before assigning relevance, identify the requested entity/policy from the question
and history, then compare it with the entity/policy actually answered. Name that
comparison in the relevance reason. A shared action such as booking, renewing or
returning does not identify its object. If no object is selected and multiple
policies fit, a substantive answer choosing one fails relevance even when its
policy is true. A direct clarifying question can pass relevance. Conversely, an
explicit question or unambiguous prior topic can resolve the object; do not reject
an ordinary contextual pronoun solely because its noun is omitted. History supplies
referents only, never truth or permission. Keep the behavior classification and
factual/citation judgments separate from this topic-selection check.
"""
CLAIM_PROMPT = previous.CLAIM_PROMPT + ACTOR_PARAPHRASE_RULES
COVERAGE_PROMPT = previous.COVERAGE_PROMPT + ACTOR_PARAPHRASE_RULES + TOPIC_CHECK_RULES
REVIEW_PROMPT = previous.REVIEW_PROMPT + ACTOR_PARAPHRASE_RULES + TOPIC_CHECK_RULES


def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]['prompt'], parts[1]['prompt'] = CLAIM_PROMPT, COVERAGE_PROMPT
    return parts
