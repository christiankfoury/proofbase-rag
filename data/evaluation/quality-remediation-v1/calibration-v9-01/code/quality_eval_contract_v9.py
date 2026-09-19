"""V9: factual-only claims and explicit behavior/review semantics.

Evaluation-only development candidate. Frozen v7/v8 artifacts stay unchanged.
"""
from scripts import quality_eval_contract as v7
from scripts import quality_eval_contract_v8 as v8

VERSION = "answer-dimensions.v9-candidate"
DIMENSIONS, BEHAVIORS = v7.DIMENSIONS, v7.BEHAVIORS
schema, review_schema = v7.schema, v7.review_schema
validate, dimensions, summarize = v7.validate, v7.dimensions, v7.summarize
candidate_judgments = v8.candidate_judgments

CLAIM_PROMPT = v7.CLAIM_PROMPT + """
Return ONLY factual assertions in claims. A pure speech act has an empty claims
array and all_claims_assessed=true; do not create a record for it at all. This
includes access refusals, inability-to-find statements, requests for clarification
and rejection of malicious instructions. A policy assertion appended to any such
act MUST still be included. Never copy a source statement absent from the answer.

Contradiction requires an incompatible statement about the same rule/entity;
irrelevant evidence is not contradiction. Unfounded additions are factual unknown.
Citation support is missing when no cited source entails the whole assertion,
including when citations contradict it. Citation unknown is reserved for ambiguous
entailment. Preserve modality: permission to do something does not entail that it
is required. Exact answer/source spans are necessary but do not prove entailment.
"""

BEHAVIOR_RULES = """
actual_behavior classifies ONLY the response's prose, not the expected behavior,
reference policy, metadata, or inferred reason for refusal. Distinguish:
- not_found: cannot find/confirm information in available evidence;
- refuse_no_access: explicitly denies disclosure for lack of access/authorization;
- refuse_instruction: explicitly rejects the requested instruction;
- unknown: generic 'cannot help' without explaining which reason applies;
- clarify: asks for context needed to resolve the request;
- answer: a direct substantive answer, even with an incorrect asserted value;
- partial_answer: a requested part is omitted while another part is answered.
Never turn inability to find information into access denial. Never infer an access
denial from the nature of the question or from expected_behavior. If an ambiguous
request receives an invented-topic answer, actual_behavior=answer and relevance=fail.
Relevance is topical responsiveness, independent of completeness and correctness.
A wrong behavior can still be relevant; unknown refusal reason does not alone
make topical relevance unknown. Optional policy language cannot support a duty.
"""
COVERAGE_PROMPT = v8.COVERAGE_PROMPT + BEHAVIOR_RULES
REVIEW_PROMPT = v8.REVIEW_PROMPT + BEHAVIOR_RULES + """
IMPORTANT RUBRIC: response_behavior is a DERIVED correctness label, distinct from
actual_behavior (prose form). First check actual_behavior under the definitions.
Then match it against expected_behavior. Unknown actual behavior is unresolved.
When expected_behavior=answer, missing OR contradicted required facts force the
DERIVED response_behavior to fail, even if actual_behavior correctly says answer.
Agree with that fail; do not dispute merely because the prose attempts an answer.
Required-fact unknown forces unresolved. This is the rubric, not an invitation to
redefine response_behavior as response form. All required facts must be covered.
For non-answer expectations, completeness can be not_applicable; do not invent
required facts. A correct unknown label for unsupported claims is an agreement.
Return dispute only for the dimensions actually judged incorrectly. Do not add
disputes to unrelated, correct dimensions merely because another dimension fails.
"""


def request_parts(inputs):
    result = v7.request_parts(inputs)
    result[0]["prompt"] = CLAIM_PROMPT
    result[1]["prompt"] = COVERAGE_PROMPT
    return result
