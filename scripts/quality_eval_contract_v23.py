"""Keep attribution metadata out of the exact source-text witness fields."""
from scripts import quality_eval_contract_v22 as previous

VERSION = 'answer-dimensions.v23-candidate'
DIMENSIONS, BEHAVIORS = previous.DIMENSIONS, previous.BEHAVIORS
schema, review_schema = previous.schema, previous.review_schema
validate, summarize, dimensions = previous.validate, previous.summarize, previous.dimensions
candidate_judgments, metadata = previous.candidate_judgments, previous.metadata

WITNESS_FIELDS = """
Output contract for source_metadata: explain document-title attribution in the
claim's reason only. source_spans entries may use ONLY a source_id present in
factual_sources and a verbatim substring of THAT entry's text. citation_spans
entries may use ONLY a citation_id present in cited_sources and a verbatim
substring of THAT entry's text. Never use a document_id as either witness ID.
Never put a document title into a witness span unless those literal words occur
in that identified source's text. Metadata is contextual attribution information,
not an additional text source or citation. Policy text still needs valid source
and citation witnesses; do not invent witness IDs or text to represent metadata.
"""
CLAIM_PROMPT = previous.CLAIM_PROMPT + WITNESS_FIELDS
COVERAGE_PROMPT = previous.COVERAGE_PROMPT
REVIEW_PROMPT = previous.REVIEW_PROMPT + WITNESS_FIELDS


def request_parts(inputs):
    parts = previous.request_parts(inputs)
    parts[0]['prompt'], parts[1]['prompt'] = CLAIM_PROMPT, COVERAGE_PROMPT
    return parts
