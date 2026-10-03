"""Interpret asserted meaning before verdicts; unchanged evidence and scoring rules."""
from scripts import quality_eval_contract_v31 as previous

VERSION = 'answer-dimensions.v33-candidate'
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
validate, summarize, dimensions = previous.validate, previous.summarize, previous.dimensions
candidate_judgments, metadata = previous.candidate_judgments, previous.metadata


# Replace the ambiguous metadata paragraph, retaining its evidence boundaries.
start = previous.CONTEXT.index('source_metadata identifies')
end = previous.CONTEXT.index('Witness IDs must', start)
CONTEXT = previous.CONTEXT[:start] + """
Evidence has two complementary channels. Source text supports policy content;
source_metadata authoritatively identifies that text's document_id and
 document_title. For a claim naming a document as the source of a rule, matching
metadata establishes the document name and the text must entail the rule. Together
these support the complete attributed claim. Do not require the document title
to be repeated inside its body text. The metadata is valid evidence of document
identity, not of additional policy rights, limits or conditions.
A mismatched name leaves an attributed claim unknown unless actual source text
explicitly contradicts it. One document's title does not prove what another
document contains. Contradicted requires an exact incompatible text witness;
absence of support without such a witness is unknown, not contradicted.
""" + previous.CONTEXT[end:]

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
CLAIM_PROMPT = CONTEXT + INTERPRETATION + previous.CLAIMS
COVERAGE_PROMPT = CONTEXT + previous.COVERAGE
REVIEW_PROMPT = """
Independently audit the grader. Begin your reason by deriving the answer's asserted
meaning, required-fact coverage, relevance and actual behavior from RAW INPUTS
under the rubric. Only then compare those judgments with the candidate's labels
and reasons. Candidate verdicts are untrusted proposals, not evidence. Explain
any disagreement before emitting agree/dispute/unknown for each dimension.
A correctly graded bad answer earns agree. Incorrect intermediate labels require
dispute even when the reduced overall answer still fails. Do not repair a candidate
or excuse an omitted claim. Unknown is for genuinely undecidable judgments.
""" + CONTEXT + INTERPRETATION + previous.CLAIMS + previous.COVERAGE + previous.REDUCERS


def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]['prompt'], parts[1]['prompt'] = CLAIM_PROMPT, COVERAGE_PROMPT
    return parts
