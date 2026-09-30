"""V19 prompts with unchanged pinned request format, parser and token limits."""
from decimal import Decimal
import json
from scripts import quality_eval_contract_v19 as contract
from scripts.quality_eval_transport_v18 import (
    MODEL, CAPS, MAX_CANDIDATE_BYTES, INPUT_RATE, OUTPUT_RATE, BudgetStop,
    request, reserve, parsed, exclusive_lock,
)


def initial_requests(inputs):
    full = contract.schema()
    keys = {'claims': ('claims', 'all_claims_assessed'),
            'coverage': ('facts', 'actual_behavior', 'behavior_span', 'behavior_reason', 'relevance', 'forbidden_assertion')}
    result = []
    for part in contract.request_parts(inputs):
        names = keys[part['purpose']]
        schema = {'type': 'object', 'additionalProperties': False, 'required': list(names),
                  'properties': {key: full['properties'][key] for key in names}}
        result.append((part['purpose'], request(part['purpose'], part['prompt'], part['input'], schema)))
    return result


def review_request(inputs, candidate):
    if len(json.dumps(candidate, ensure_ascii=False).encode('utf-8')) > MAX_CANDIDATE_BYTES:
        raise ValueError('Candidate exceeds predeclared review size bound')
    return request('review', contract.REVIEW_PROMPT,
                   {'inputs': inputs, 'candidate': candidate,
                    'candidate_judgments': contract.candidate_judgments(inputs, candidate)}, contract.review_schema())


def case_bound(inputs):
    total = sum((reserve(body)['reserved_usd'] for _, body in initial_requests(inputs)), Decimal(0))
    empty = request('review', contract.REVIEW_PROMPT,
                    {'inputs': inputs, 'candidate': {}, 'candidate_judgments': {}}, contract.review_schema())
    return total + reserve(empty)['reserved_usd'] + Decimal(MAX_CANDIDATE_BYTES * 2 + 1024) * INPUT_RATE / 1_000_000


def grade_case(create, inputs, ledger, folder):
    grade = {}
    for purpose, body in initial_requests(inputs):
        response = ledger.call(create, body, folder / (purpose + '.json'))
        grade.update(parsed(response, body['response_format']['json_schema']['schema']))
    body = review_request(inputs, grade)
    response = ledger.call(create, body, folder / 'review.json')
    return grade, parsed(response, contract.review_schema())
