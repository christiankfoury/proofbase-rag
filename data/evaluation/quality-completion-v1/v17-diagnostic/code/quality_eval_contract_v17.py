"""V17: semantic coverage of generic obligations, without relaxing quantifiers."""
from scripts import quality_eval_contract_v16 as previous
VERSION = 'answer-dimensions.v17-candidate'
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
dimensions, validate, summarize = previous.dimensions, previous.validate, previous.summarize
candidate_judgments = previous.candidate_judgments
CLAIM_PROMPT = previous.CLAIM_PROMPT
PARAPHRASE_RULES = """
Judge communicated meaning, not whether the answer repeats a required fact's words.
A generic plural obligation (the named role must perform the action on the named
items) normally communicates the policy for each such item in its stated scope.
Do not mark it missing solely because a reference uses 'each' or 'every', the
answer uses an equivalent generic plural, or active/passive grammar differs.
Read the answer in the explicit question/topic context; this resolves references,
not new policy facts. Preserve the same actor, action, object, scope and conditions.
This is not a license to remove real quantifiers or conditions. 'Some', 'usually',
'when convenient', optional language, exclusions, or a narrowed subset do not
communicate an unconditional all-item duty. Explicit incompatible quantification
is contradicted; a material scope/condition omitted without an incompatible claim
is missing. Distinguish a changed obligation from harmless grammatical form.
"""
COVERAGE_PROMPT = previous.COVERAGE_PROMPT + PARAPHRASE_RULES
REVIEW_PROMPT = previous.REVIEW_PROMPT + PARAPHRASE_RULES


def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]['prompt'], parts[1]['prompt'] = CLAIM_PROMPT, COVERAGE_PROMPT
    return parts
