"""V15: distinguish omitted policy facts from explicit incompatible assertions."""
from scripts import quality_eval_contract_v14 as previous
VERSION = "answer-dimensions.v15-candidate"
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
dimensions, validate, summarize = previous.dimensions, previous.validate, previous.summarize
candidate_judgments = previous.candidate_judgments
CLAIM_PROMPT = previous.CLAIM_PROMPT
COVERAGE_RULES = """
Before labeling a required fact contradicted, align the answer's assertion with
that required fact's entity, policy, property, scope and conditions. Contradicted
requires two assertions that cannot both hold for the SAME entity/rule/property
under the stated conditions. A different amount about a DIFFERENT policy/entity
is NOT a contradiction of the requested fact: that requested fact is missing.
Do not silently replace the named subject of the answer with the requested subject.
A wrong-topic answer may contain true facts while required coverage is missing.
A wrong value for the SAME requested policy does contradict it. Keep this
separate from factual truth, relevance and actual response form. For missing,
answer_spans must be empty; for contradiction, cite the exact incompatible span.
Material condition omission remains missing, not covered or contradicted.
Do not add policy sequencing to a coverage explanation just because an answer
uses a discourse list marker such as 'First'. Describe only the supported step.
"""
COVERAGE_PROMPT = previous.COVERAGE_PROMPT + COVERAGE_RULES
REVIEW_PROMPT = previous.REVIEW_PROMPT + COVERAGE_RULES + """
Audit intermediate statuses as well as reduced dimension labels. An incorrect
fact status is a completeness dispute even if its replacement would reduce to
the SAME failed completeness label. For example, a missing required fact wrongly
labeled contradicted still requires dispute for completeness. Do not silently
repair the candidate and agree with the repaired reduction. Apply the same rule
to incorrect claim factual/citation statuses in their respective dimensions.
Dispute only affected dimensions; a correct independent actual_behavior or
response_behavior label does not become incorrect merely from this status error.
"""

def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]["prompt"], parts[1]["prompt"] = CLAIM_PROMPT, COVERAGE_PROMPT
    return parts
