"""V18: contextual task instructions do not invent a distinct responsible party."""
from scripts import quality_eval_contract_v17 as previous
VERSION = 'answer-dimensions.v18-candidate'
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
dimensions, validate, summarize = previous.dimensions, previous.validate, previous.summarize
candidate_judgments = previous.candidate_judgments
CONTEXT_RULES = """
Distinguish an assigned responsibility from instructions for the task the user is
already asking about. If a source imposes a deadline/condition on an action and the
question asks how/when the user performs that SAME action, addressing that task's
participant as 'you' is ordinary contextual paraphrase, not an additional duty.
For example, an object-must-be-submitted deadline can answer when I submit it as
'you must submit it by [the same deadline]'. This does not assert new authorization,
exclusive responsibility, or a separate obligation to carry out a different action.
A guessed topic still fails relevance and expected clarification independently;
its stated policy can still be factually supported. Do not manufacture a factual
actor failure just because an otherwise true policy answer guessed the topic.
This contextual rule does NOT permit adding another action or assigning a passive
inspection, approval, audit, recordkeeping or other separate duty to the requester,
a permitted user, owner or nearby named role. Mere permission for one action does
not identify who performs another. Explicit actor restrictions or prohibitions
always take precedence; a user's premise never proves access or policy permission.
Check action, object, conditions and named/exclusive role before accepting a
second-person paraphrase. Question/history resolve task participants, never policy.
"""
# Narrow the overbroad v16 sentence rather than retain conflicting instructions.
_old = "WHO must perform it. Do not infer a responsible actor from the question's speaker,\na nearby permission granted to a group, ownership of the object, or common practice."
_new = "WHO has a separately assigned duty. Do not infer a responsible actor from\na nearby permission, ownership, common practice or the mere identity of the speaker."
assert _old in previous.CLAIM_PROMPT and _old in previous.REVIEW_PROMPT
CLAIM_PROMPT = previous.CLAIM_PROMPT.replace(_old, _new) + CONTEXT_RULES
COVERAGE_PROMPT = previous.COVERAGE_PROMPT
REVIEW_PROMPT = previous.REVIEW_PROMPT.replace(_old, _new) + CONTEXT_RULES


def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]['prompt'], parts[1]['prompt'] = CLAIM_PROMPT, COVERAGE_PROMPT
    return parts
