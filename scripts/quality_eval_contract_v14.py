"""One user-authorized correction: distinguish current permission from history."""
from scripts import quality_eval_contract_v13 as previous

VERSION = "answer-dimensions.v14-candidate"
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
dimensions, validate, summarize = previous.dimensions, previous.validate, previous.summarize
candidate_judgments = previous.candidate_judgments

TEMPORAL_RULES = """
Current permission versus historical claims (approved rubric clarification):
Current policy evidence supports current permission. The word 'still' alone,
whether in the question or an ordinary affirmative answer, does not introduce
a separate claim about historical policy. Interpret an elliptical 'Yes.' together
with the following policy statement: it confirms that current permission, not
an independently asserted policy history. Keep exact answer spans; do not create
an unsupported history claim from this discourse alone.
Explicit assertions about past policy, a policy change, an effective date, or
continuity across a stated historical interval DO require corresponding evidence.
For example, 'has always been allowed', 'unchanged since 2019', and 'the rule was
changed last month' cannot be supported merely by a current permission.
A source explicitly marked expired/superseded is not evidence of current permission.
Preserve every stated condition, scope, entity, quantity, prerequisite and modality.
This clarification does not supply missing user intent: guessing the topic of an
ambiguous question still fails relevance and the intended clarification behavior,
even when the invented-topic policy statement is factually and citation-supported.
"""
CLAIM_PROMPT = previous.CLAIM_PROMPT + TEMPORAL_RULES
COVERAGE_PROMPT = previous.COVERAGE_PROMPT
REVIEW_PROMPT = previous.REVIEW_PROMPT + TEMPORAL_RULES


def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]["prompt"] = CLAIM_PROMPT
    parts[1]["prompt"] = COVERAGE_PROMPT
    return parts
