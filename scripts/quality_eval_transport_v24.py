"""Pinned medium-reasoning grader; approved claims cap includes reasoning tokens."""
from decimal import Decimal
import json
from scripts import quality_eval_contract_v24 as contract
from scripts.quality_eval_transport_v18 import MODEL, MAX_CANDIDATE_BYTES, INPUT_RATE, OUTPUT_RATE, BudgetStop, parsed, exclusive_lock

CAPS = {'claims': 8192, 'coverage': 4096, 'review': 4096}


def request(purpose, prompt, data, schema):
    return dict(model=MODEL, reasoning_effort='medium', max_completion_tokens=CAPS[purpose],
        messages=[dict(role='system', content=prompt), dict(role='user', content=json.dumps(data, ensure_ascii=False))],
        response_format=dict(type='json_schema', json_schema=dict(name='quality_'+purpose, strict=True, schema=schema)))


def reserve(body):
    purpose=body.get('response_format',{}).get('json_schema',{}).get('name','').removeprefix('quality_')
    if (body.get('model') != MODEL or body.get('reasoning_effort') != 'medium' or body.get('stream')
            or body.get('tools') or purpose not in CAPS or body.get('max_completion_tokens') != CAPS[purpose]):
        raise BudgetStop('Unapproved grader request or output allowance')
    bound=len(json.dumps(body,ensure_ascii=False).encode('utf-8'))+2048
    if bound>272000:raise BudgetStop('Unpriced long context')
    cap=CAPS[purpose]
    return dict(input_bound=bound,output_cap=cap,reserved_usd=(bound*INPUT_RATE+cap*OUTPUT_RATE)/1000000)


def initial_requests(inputs):
    full=contract.schema(); result=[]
    keys={'claims':('claims','all_claims_assessed'), 'coverage':('facts','actual_behavior','behavior_span','behavior_reason','relevance','forbidden_assertion')}
    for part in contract.request_parts(inputs):
        names=keys[part['purpose']]
        schema=dict(type='object',additionalProperties=False,required=list(names),properties={k:full['properties'][k] for k in names})
        result.append((part['purpose'],request(part['purpose'],part['prompt'],part['input'],schema)))
    return result


def review_request(inputs,candidate):
    if len(json.dumps(candidate,ensure_ascii=False).encode('utf-8'))>MAX_CANDIDATE_BYTES:
        raise ValueError('Candidate exceeds unchanged review size bound')
    return request('review',contract.REVIEW_PROMPT,dict(inputs=inputs,candidate=candidate,
        candidate_judgments=contract.candidate_judgments(inputs,candidate)),contract.review_schema())


def case_bound(inputs):
    initial=sum((reserve(body)['reserved_usd'] for _,body in initial_requests(inputs)),Decimal(0))
    empty=request('review',contract.REVIEW_PROMPT,dict(inputs=inputs,candidate={},candidate_judgments={}),contract.review_schema())
    return initial+reserve(empty)['reserved_usd']+Decimal(MAX_CANDIDATE_BYTES*2+1024)*INPUT_RATE/1000000


def grade_case(create,inputs,ledger,folder):
    grade={}
    for purpose,body in initial_requests(inputs):
        response=ledger.call(create,body,folder/(purpose+'.json'))
        grade.update(parsed(response,body['response_format']['json_schema']['schema']))
    body=review_request(inputs,grade)
    return grade,parsed(ledger.call(create,body,folder/'review.json'),contract.review_schema())
