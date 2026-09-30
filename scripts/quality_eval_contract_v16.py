"""V16: preserve the actor of an obligation; passive requirements do not assign duties."""
from scripts import quality_eval_contract_v15 as previous
VERSION = "answer-dimensions.v16-candidate"
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
dimensions, validate, summarize = previous.dimensions, previous.validate, previous.summarize
candidate_judgments = previous.candidate_judgments
AGENCY_RULES = """
Preserve the actor/responsible party of each asserted duty or permission.
A passive requirement that an action must occur does not by itself establish
WHO must perform it. Do not infer a responsible actor from the question's speaker,
a nearby permission granted to a group, ownership of the object, or common practice.
If an answer assigns an unspecified duty to a named actor, assess that added agency:
factual unknown and cited support missing unless authorized evidence supplies it.
If evidence explicitly makes that duty exclusive to a different actor, the assignment
is contradicted. A different named actor alone is not an exclusive prohibition.
Conversely, a passive paraphrase preserving the stated requirement is supported;
active wording is supported when evidence identifies that same responsible actor.
Pronouns may resolve to an explicit antecedent but cannot create a new obligation.
Inspect all parts of a compound claim; a supported permission does not establish
an adjoining unsupported assignment of responsibility. Enumerate distinct policy
assertions separately when their actors, support or source evidence differ.
Keep claim truth separate from required-fact coverage: an answer can communicate
a required passive requirement while also adding an unsupported responsible actor.
"""
CLAIM_PROMPT = previous.CLAIM_PROMPT + AGENCY_RULES
COVERAGE_PROMPT = previous.COVERAGE_PROMPT
REVIEW_PROMPT = previous.REVIEW_PROMPT + AGENCY_RULES


def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]["prompt"], parts[1]["prompt"] = CLAIM_PROMPT, COVERAGE_PROMPT
    return parts
