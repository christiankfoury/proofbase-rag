"""Offline-buildable v35 requests with unchanged models, caps and review stages."""
from decimal import Decimal
from scripts import quality_eval_transport_v34 as previous
from scripts import quality_eval_contract_v35 as contract
from scripts.quality_eval_transport_v34 import (
    MODEL, CAPS, MAX_CANDIDATE_BYTES, INPUT_RATE, OUTPUT_RATE,
    BudgetStop, parsed, exclusive_lock, request, reserve,
)


def initial_requests(inputs):
    requests = previous.initial_requests(inputs)
    for (_, body), part in zip(requests, contract.request_parts(inputs)):
        body['messages'][0]['content'] = part['prompt']
    return requests


def review_request(inputs, candidate):
    body = previous.review_request(inputs, candidate)
    body['messages'][0]['content'] = contract.REVIEW_PROMPT
    return body


def case_bound(inputs):
    initial = sum((reserve(body)['reserved_usd'] for _, body in initial_requests(inputs)), Decimal(0))
    empty = request('review', contract.REVIEW_PROMPT,
                    dict(inputs=inputs, candidate={}, candidate_judgments={}), contract.review_schema())
    return initial + reserve(empty)['reserved_usd'] + Decimal(MAX_CANDIDATE_BYTES * 2 + 1024) * INPUT_RATE / 1000000


def grade_case(create, inputs, ledger, folder):
    grade = {}
    for purpose, body in initial_requests(inputs):
        response = ledger.call(create, body, folder / (purpose + '.json'))
        grade.update(parsed(response, body['response_format']['json_schema']['schema']))
    body = review_request(inputs, grade)
    return grade, parsed(ledger.call(create, body, folder / 'review.json'), contract.review_schema())
