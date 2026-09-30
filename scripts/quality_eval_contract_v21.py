"""Clarify contextual task framing without exempting asserted policy purposes."""
from scripts import quality_eval_contract_v20 as previous

VERSION = 'answer-dimensions.v21-candidate'
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
dimensions, validate, summarize = previous.dimensions, previous.validate, previous.summarize
candidate_judgments = previous.candidate_judgments

TASK_FRAMING = """
Distinguish framing the user's requested task from asserting an additional policy
purpose. When the question asks what information belongs in a record or how to
complete that record, 'to document it properly' can frame the SAME requested
recordkeeping task. A sourced list of required fields with that framing does not
by itself assert why the organization adopted the requirement. Judge communicated
meaning in the whole question and answer, not the connective 'to' or 'ensure'
alone. Assess every field and material condition normally. Do not extract a
separate organizational-purpose claim solely from restating the requested task.
This is narrow: explicit organizational reasons ('the company requires this
because...'), compliance with a law, a promised outcome, reduced risk, guaranteed
approval, or any added action/permission remain factual claims needing evidence.
Do not excuse those assertions as helpful framing, even if the user suggested
them. The question resolves the task, never supplies truth for extra policy facts.
If the communicated meaning is genuinely ambiguous, preserve unknown support;
never assign supported just to make a complete-looking answer pass.
"""
CLAIM_PROMPT = previous.CLAIM_PROMPT + TASK_FRAMING
COVERAGE_PROMPT = previous.COVERAGE_PROMPT
REVIEW_PROMPT = previous.REVIEW_PROMPT + TASK_FRAMING


def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]['prompt'], parts[1]['prompt'] = CLAIM_PROMPT, COVERAGE_PROMPT
    return parts
