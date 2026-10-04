"""Offline-only paired-judgment prototype. No client, execution or release gate.

Each judge independently extracts claims and coverage with the existing rubric.
Comparison identifies disagreements; agreement is NOT a correctness judgment.
"""
from copy import deepcopy
from decimal import Decimal

from scripts import quality_eval_contract_v34 as contract
from scripts import quality_eval_transport_v34 as transport

INPUT_KEYS = {
    'question', 'history_not_evidence', 'answer', 'expected_behavior',
    'required_facts', 'forbidden_assertions', 'factual_sources', 'cited_sources',
    'source_metadata',
}


def request_plan(inputs):
    """Build all four bodies before any judgments exist; never accept a candidate."""
    if set(inputs) - INPUT_KEYS:
        raise ValueError('Only original evidence inputs are permitted')
    requests = []
    for judge in ('a', 'b'):
        for purpose, body in transport.initial_requests(deepcopy(inputs)):
            requests.append(dict(judge=judge, purpose=purpose, body=body))
    return requests


def conservative_bound(inputs):
    return sum((transport.reserve(r['body'])['reserved_usd']
                for r in request_plan(inputs)), Decimal(0))


def _labels(grade):
    # Keep intermediate labels: aggregate agreement can hide an omitted claim
    # or a missing-vs-contradicted fact. Segmentation differences stay unresolved.
    return {
        'claims': sorted((c['text'], c['factual_status'], c['citation_status'])
                         for c in grade['claims']),
        'facts': sorted((f['fact_id'], f['status']) for f in grade['facts']),
        'actual_behavior': grade['actual_behavior'],
        'relevance': grade['relevance']['status'],
        'forbidden_assertion': grade['forbidden_assertion'],
    }


def compare(case, first, second):
    """Inspect frozen outputs only. Never synthesize agree labels or award credit."""
    checks = [contract.dimensions(case['inputs'], grade, case['payload'],
                                  case['evidence'], case['safety_flags'])
              for grade in (first, second)]
    errors = [c['grader_errors'] for c in checks]
    blocked = bool(case['safety_flags'] or any(
        c['unmatched_citations'] or c['quotation_fidelity'] == 'fail' for c in checks))
    differences = []
    if not any(errors):
        a, b = _labels(first), _labels(second)
        differences = [key for key in a if a[key] != b[key]]
    return dict(
        status=('invalid' if any(errors) else 'blocked' if blocked else
                'unresolved_disagreement' if differences else 'agreement_only'),
        differences=differences, grader_errors=errors,
        target_credit=False, release_eligible=False, source_review_required=True,
    )
