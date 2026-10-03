"""Conversational context clarification; unchanged schema, witnesses and reducers."""
from scripts import quality_eval_contract_v23 as previous

VERSION = 'answer-dimensions.v24-candidate'
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
validate, summarize, dimensions = previous.validate, previous.summarize, previous.dimensions
candidate_judgments, metadata = previous.candidate_judgments, previous.metadata

CONTEXT = """
Read the whole answer in the question's conversational context before judging an
extracted span. Exact spans are witnesses anchored in that answer, not independent
sentences stripped of their antecedents. Several exact answer spans may jointly
communicate a required fact. Material scope and conditions must actually be
communicated by the answer (including explicit reference to the question's
scenario); neither the expected fact nor retrieved sources can fill an omission.
If a condition is missing, mark missing even when the remaining statement is true.

'I could not find/establish X in the available evidence' reports an inability to
answer, not a policy that X does not exist. Omit that speech act from claims even
when the supplied sources in fact contain X; assess the omission as completeness
and behavior, without treating the evidence caveat as a contradicted policy rule.
An affirmative assertion 'there is no X' about the policy itself remains a claim.
A response providing one requested policy fact and saying it cannot find another
is partial_answer, not a complete answer and not a pure not_found speech act.

Preserve ordinary scenario and attribution references, but do not promote them
into evidence. The question can identify the actor performing the requested task;
it cannot establish their authority, change permission, or add an obligation.
A paraphrase must retain the source's approval actor, modality and conditions.
Negated/rejected premises are not affirmed assertions. Still assess every actual
policy assertion, every required fact and every citation independently. Exact
contiguous source/answer witnesses and all existing reducers remain mandatory.
"""
CLAIM_PROMPT = previous.CLAIM_PROMPT + CONTEXT
COVERAGE_PROMPT = previous.COVERAGE_PROMPT + CONTEXT
REVIEW_PROMPT = previous.REVIEW_PROMPT + CONTEXT


def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]['prompt'], parts[1]['prompt'] = CLAIM_PROMPT, COVERAGE_PROMPT
    return parts
