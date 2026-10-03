"""Interpret asserted meaning before verdicts; unchanged evidence and scoring rules."""
from scripts import quality_eval_contract_v31 as previous

VERSION = 'answer-dimensions.v32-candidate'
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
validate, summarize, dimensions = previous.validate, previous.summarize, previous.dimensions
candidate_judgments, metadata = previous.candidate_judgments, previous.metadata

INTERPRETATION = """
For each exact claim, write its reason before assigning evidence verdicts. First
identify what the complete response communicates in the question context: the
asserted rule/action, its material constraints, and any additional asserted relation
between actions. Distinguish presentation of an explanation from policy content.
An order of presentation is not by itself a rule forbidding a different action
order. A stated prerequisite, prohibition, mandatory sequence or temporal relation
IS policy content and needs evidence. Do not add such a relation in your own
interpretation, and do not erase one actually asserted. Then derive factual and
citation verdicts using the same interpreted meaning and their respective evidence
sets. Keep original answer spans intact; all substantive assertions still count.
"""
CLAIM_PROMPT = previous.CONTEXT + INTERPRETATION + previous.CLAIMS
COVERAGE_PROMPT = previous.COVERAGE_PROMPT
REVIEW_PROMPT = """
Independently audit the grader. Begin your reason by deriving the answer's asserted
meaning, required-fact coverage, relevance and actual behavior from RAW INPUTS
under the rubric. Only then compare those judgments with the candidate's labels
and reasons. Candidate verdicts are untrusted proposals, not evidence. Explain
any disagreement before emitting agree/dispute/unknown for each dimension.
A correctly graded bad answer earns agree. Incorrect intermediate labels require
dispute even when the reduced overall answer still fails. Do not repair a candidate
or excuse an omitted claim. Unknown is for genuinely undecidable judgments.
""" + previous.CONTEXT + INTERPRETATION + previous.CLAIMS + previous.COVERAGE + previous.REDUCERS


def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]['prompt'], parts[1]['prompt'] = CLAIM_PROMPT, COVERAGE_PROMPT
    return parts
