"""Keep attributed predicates attached to their subject during extraction."""
from scripts import quality_eval_contract_v24 as previous

VERSION='answer-dimensions.v25-candidate'
DIMENSIONS,BEHAVIORS=previous.DIMENSIONS,previous.BEHAVIORS
schema,review_schema=previous.schema,previous.review_schema
validate,summarize,dimensions=previous.validate,previous.summarize,previous.dimensions
candidate_judgments,metadata=previous.candidate_judgments,previous.metadata

EXTRACTION="""
Extract a whole original sentence once when its attribution, subject and policy
predicate belong together. Do not also extract an overlapping subjectless clause
and label it as if the attribution disappeared. A predicate inherits its actual
subject and attribution from the answer. If any part of the complete assertion
is unsupported, the whole assertion cannot be supported, even when its embedded
policy rule is true. This does not remove a claim or waive any condition; retain
every asserted fact and judge all parts of each exact contiguous witness together.
"""
CLAIM_PROMPT=previous.CLAIM_PROMPT+EXTRACTION
COVERAGE_PROMPT=previous.COVERAGE_PROMPT
REVIEW_PROMPT=previous.REVIEW_PROMPT+EXTRACTION


def request_parts(inputs):
    parts=previous.request_parts(inputs)
    parts[0]['prompt'],parts[1]['prompt']=CLAIM_PROMPT,COVERAGE_PROMPT
    return parts
