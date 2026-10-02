"""Closed purchase grammar and quoted-row arithmetic, never general policy advice.

Only the original request can supply an operand. A verified decision is separate
from model output; neither token counts nor a model-supplied label authorize it.
"""
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import re

from apps.api.app.citations.citation_formatter import citation_payload
from apps.api.app.citations.citation_validator import validate_citations
from apps.api.app.confidence.confidence_scorer import final_confidence
from apps.api.app.permissions.access_control import unauthorized_chunks
from apps.api.app.reasoning.evidence_assessment import EvidenceAssessment
from apps.api.app.reasoning.post_generation_validation import PostGenerationValidation
from apps.api.app.reasoning.restricted_intent import restricted_intent_allowed_roles
from apps.api.app.permissions.roles import role_variants
from apps.api.app.retrieval.types import RetrievedChunk


NUMBER = r"(?:\d{1,3}(?:,\d{3}){1,3}|\d{1,12})(?:\.\d{1,2})?"
MONEY = rf"(?P<money>(?P<currency>[A-Z]{{3}}) (?P<amount>{NUMBER}))"
CATEGORY = r"(?P<category>[a-z]+(?:[ -][a-z]+){0,5})"
ROLE = r"(?P<role>[a-z]+(?: [a-z]+){0,2})"
# Full matches only: no inferred context, trailing clauses or hidden second ask.
QUESTIONS = tuple(re.compile(p, re.IGNORECASE | re.ASCII) for p in (
    rf"My {CATEGORY} purchase (?:would cost|costs) {MONEY}\. Does that category's standard limit trigger {ROLE} approval for this purchase\?",
    rf"For my {CATEGORY} purchase of {MONEY}, does the category's standard limit require {ROLE} approval\?",
))
LIMIT = re.compile(rf"(?P<currency>[A-Z]{{3}}) (?P<amount>{NUMBER}) per purchase", re.I | re.ASCII)
APPROVAL = re.compile(rf"{ROLE} approval above limit", re.I | re.ASCII)
HEADER = ('category', 'standard limit', 'approval required')


@dataclass(frozen=True)
class ScenarioCalculation:
    question_sha256: str
    input_span: tuple[int, int]
    input_quote: str
    category_span: tuple[int, int]
    category: str
    currency: str
    amount: str
    chunk_id: str
    document_id: str
    source_sha256: str
    row_span: tuple[int, int]
    row_quote: str
    limit: str
    approver: str
    operator: str
    above_limit: bool
    effective_role: str
    project_id: str | None
    department_id: str | None


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _cells(line: str) -> tuple[str, ...] | None:
    value = line.strip()
    if not value.startswith('|') or not value.endswith('|'):
        return None
    return tuple(cell.strip() for cell in value[1:-1].split('|'))


def _source_row(category: str, chunks: list[RetrievedChunk]):
    """Require one exact row, its header, and no competing category statement.

    Other categories' rows/prose are not applied to the requested category.
    Recognized table qualifications or references to this category decline the
    fast path. This is not a semantic applicability checker: the rendered result
    only compares the quoted row, never grants approval.
    """
    matches = []
    category_pattern = re.compile(r'(?<!\w)' + re.escape(category) + r'(?!\w)', re.I | re.ASCII)
    for source in chunks:
        lines = source.content.splitlines(keepends=True)
        table = False
        offset = 0
        for index, line in enumerate(lines):
            cells = _cells(line)
            if cells and tuple(c.casefold() for c in cells) == HEADER:
                # A prose preamble could qualify/supersede the table. Headings only.
                prefix = ''.join(lines[:index]).strip().lstrip('#').strip()
                if prefix and prefix != source.section_heading:
                    return None
                if index + 1 >= len(lines):
                    return None
                separator = _cells(lines[index + 1])
                if not separator or len(separator) != 3 or not all(re.fullmatch(r':?-{3,}:?', c) for c in separator):
                    return None
                table = True
            elif cells and category_pattern.search(line):
                if not table or len(cells) != 3 or cells[0].casefold() != category.casefold():
                    return None
                limit, approval = LIMIT.fullmatch(cells[1]), APPROVAL.fullmatch(cells[2])
                if not limit or not approval:
                    return None
                row_start = offset + len(line) - len(line.lstrip())
                quote = line.strip()
                matches.append((source, (row_start, row_start + len(quote)), quote, limit, approval))
            elif not cells:
                table = False
                if category_pattern.search(line):
                    return None
                # A non-row statement about thresholds/precedence needs interpretation.
                if re.search(r'\b(limit\w*|threshold\w*|table\w*|categor\w*|supersed\w*|obsolete|expired|effective|override\w*|instructions?)\b', line, re.I):
                    if line.strip().lstrip('#').strip() != source.section_heading:
                        return None
            offset += len(line)
    return matches[0] if len(matches) == 1 else None


def calculate(question: str, chunks: list[RetrievedChunk], *, effective_role: str,
              project_id: str | None, department_id: str | None) -> ScenarioCalculation | None:
    match = next((m for p in QUESTIONS if (m := p.fullmatch(question))), None)
    if not match or not chunks or unauthorized_chunks(chunks, effective_role):
        return None
    restricted_roles = restricted_intent_allowed_roles(question)
    if restricted_roles and not set(role_variants(effective_role)).intersection(restricted_roles):
        return None
    if len({c.chunk_id for c in chunks}) != len(chunks):
        return None
    if len(match['category']) > 64 or len(match['role']) > 32:
        return None
    if any((project_id is not None and c.project_id != project_id) or
           (department_id is not None and c.department_id != department_id) for c in chunks):
        return None
    found = _source_row(match['category'], chunks)
    if found is None:
        return None
    source, span, quote, limit, approval = found
    if match['currency'].upper() != limit['currency'].upper() or match['role'].casefold() != approval['role'].casefold():
        return None
    amount = Decimal(match['amount'].replace(',', ''))
    threshold = Decimal(limit['amount'].replace(',', ''))
    return ScenarioCalculation(
        _digest(question), match.span('money'), match['money'], match.span('category'), match['category'],
        match['currency'].upper(), str(amount), source.chunk_id, source.document_id,
        _digest(source.content), span, quote, str(threshold), approval['role'], '>', amount > threshold,
        effective_role, project_id, department_id,
    )


def render(record: ScenarioCalculation, chunks: list[RetrievedChunk]) -> dict:
    source = next(c for c in chunks if c.chunk_id == record.chunk_id)
    threshold = f'{record.currency} {record.limit}'
    comparison = 'exceeds' if record.above_limit else 'does not exceed'
    triggered = 'is triggered' if record.above_limit else 'is not triggered'
    policy_claim = f'{record.category}: {threshold} per purchase; {record.approver} approval above limit.'
    citations = [citation_payload(source, citation_type='fallback', citation_text=record.row_quote)]
    citation_check = validate_citations(policy_claim, citations, [source])
    return {
        '_scenario_calculation': record,
        '_answer_origin': 'scenario_calculation',
        'answer': (f'Your stated purchase amount, {record.input_quote}, {comparison} the {threshold} per purchase '
                   f'limit in the retrieved {record.category} row. That row\'s {record.approver.lower()}-approval-above-limit '
                   f'condition {triggered}. This comparison does not grant purchase approval or waive other requirements.'),
        'response_type': 'answer', 'behavior': 'answer',
        'citations': citation_check['citations'],
        'supported_claims': [policy_claim], 'unsupported_claims': [],
        'validation_notes': 'Verified row calculation. Purchase amount is supplied by the current user, not by the cited document.',
        'input_tokens': 0, 'output_tokens': 0, 'input_cost_usd': 0.0, 'output_cost_usd': 0.0,
        'estimated_cost_usd': 0.0, 'pricing_status': 'not_applicable',
        'model': None, 'prompt_name': None, 'prompt_version': None, 'temperature': None,
        **final_confidence('answer', [source], citation_check['citation_confidence'], []),
    }


def prepare(question: str, chunks: list[RetrievedChunk], *, request_assessment, effective_role: str,
            project_id: str | None, department_id: str | None):
    if request_assessment.recommended_action != 'continue' or request_assessment.injection_risk != 'none':
        return None
    record = calculate(question, chunks, effective_role=effective_role, project_id=project_id, department_id=department_id)
    if record is None:
        return None
    answer = render(record, chunks)
    assessment = EvidenceAssessment(
        answerability='sufficient', required_facts=[dict(fact_id='category_threshold',
            description=answer['supported_claims'][0], support='supported', supporting_chunk_ids=[record.chunk_id])],
        required_source_coverage=[], conflicts=[], missing_information=[], recommended_action='answer',
        supporting_chunk_ids=[record.chunk_id], reason_codes=['scenario_rule_available'], assessment_confidence=1.0,
        schema_version='evidence_assessment.v1', route='deterministic_scenario', status='succeeded',
        model=None, prompt_version=None, latency_ms=0, input_tokens=0, output_tokens=0,
        input_cost_usd=0.0, output_cost_usd=0.0, estimated_cost_usd=0.0, pricing_status='not_applicable',
    )
    return answer, assessment


def finalize(question: str, answer: dict, chunks: list[RetrievedChunk], *, effective_role: str,
             project_id: str | None, department_id: str | None) -> PostGenerationValidation:
    record = calculate(question, chunks, effective_role=effective_role, project_id=project_id, department_id=department_id)
    valid = record is not None and isinstance(answer.get('_scenario_calculation'), ScenarioCalculation)
    valid = valid and answer == render(record, chunks)
    return PostGenerationValidation(
        action='accept' if valid else 'downgrade', claims=[], citation_checks=[], exact_literals=[],
        unsupported_exact_literals=[], source_instruction_followed=False,
        reason_codes=['scenario_calculation_verified' if valid else 'scenario_calculation_invalid'],
        repair_count=0, schema_version='post_generation_validation.v1', route='deterministic_guard',
        status='succeeded' if valid else 'failed_safe', model=None, prompt_version=None, latency_ms=0,
        input_tokens=0, output_tokens=0, input_cost_usd=0.0, output_cost_usd=0.0,
        estimated_cost_usd=0.0, pricing_status='not_applicable',
    )
