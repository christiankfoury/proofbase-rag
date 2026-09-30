"""Contextual prerequisites and lack of evidence versus explicit exclusion."""
from scripts import quality_eval_contract_v18 as previous

VERSION = 'answer-dimensions.v19-candidate'
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
dimensions, validate, summarize = previous.dimensions, previous.validate, previous.summarize
candidate_judgments = previous.candidate_judgments

CONDITION_RULES = """
Evaluate whether a prerequisite is communicated in the explicit question context,
not whether the answer repeats the word 'only'. When asked what condition applies
or when an action is permitted, a direct instruction to do that same action after
or once the required event can communicate that prerequisite. Equivalent before/
after formulations can also preserve it. Check the whole answer and question for
the same action, object, scope and ALL material conditions. Do not require a
redundant negative sentence forbidding the action before that event.
This is not a blanket equivalence between a necessary condition and a sufficient
example. An answer describing only one example/prerequisite, omitting another
material condition, making a condition optional, allowing a bypass, or explicitly
permitting action before the required event does not cover the full requirement.
Missing conditions are missing; explicit incompatible conditions are contradicted.
Question context resolves which relation the answer communicates; it never supplies
an omitted policy fact. Coverage remains separate from factual/citation entailment.
"""
ABSENCE_RULES = """
Distinguish a statement about the limits of this evidence from a negative policy
rule. 'This excerpt does not identify/assign a responsible actor' establishes that
the excerpt lacks that assignment, not that a particular actor is prohibited from
having the duty. An added actor remains unsupported/unknown unless evidence assigns
the duty; it is not contradicted solely because an excerpt is silent or expressly
notes that its information is incomplete. Conversely an explicit prohibition,
exclusive conflicting assignment, or statement that the duty does not exist can
contradict an asserted duty. Do not treat absence of evidence as negative evidence.
This never grants credit to an unsupported actor: factual support remains unresolved
and absent citation entailment fails citation support. Preserve explicit exclusions.
"""
CLAIM_PROMPT = previous.CLAIM_PROMPT + ABSENCE_RULES
COVERAGE_PROMPT = previous.COVERAGE_PROMPT + CONDITION_RULES
REVIEW_PROMPT = previous.REVIEW_PROMPT + CONDITION_RULES + ABSENCE_RULES


def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]['prompt'], parts[1]['prompt'] = CLAIM_PROMPT, COVERAGE_PROMPT
    return parts
