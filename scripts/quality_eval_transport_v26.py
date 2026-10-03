"""V26 coherent prompts with unchanged pinned transport and allowances."""
from scripts import quality_eval_transport_v24 as base
from scripts import quality_eval_contract_v26 as contract
from scripts.quality_eval_transport_v24 import MODEL,CAPS,MAX_CANDIDATE_BYTES,INPUT_RATE,OUTPUT_RATE,BudgetStop,reserve,parsed,exclusive_lock,request
import json
from decimal import Decimal


def initial_requests(inputs):
    parts=contract.request_parts(inputs)
    requests=base.initial_requests(inputs)
    for (_,body),part in zip(requests,parts):body['messages'][0]['content']=part['prompt']
    return requests


def review_request(inputs,candidate):
    body=base.review_request(inputs,candidate)
    body['messages'][0]['content']=contract.REVIEW_PROMPT
    return body


def case_bound(inputs):
    value=sum((reserve(body)['reserved_usd'] for _,body in initial_requests(inputs)),Decimal(0))
    empty=request('review',contract.REVIEW_PROMPT,dict(inputs=inputs,candidate={},candidate_judgments={}),contract.review_schema())
    return value+reserve(empty)['reserved_usd']+Decimal(MAX_CANDIDATE_BYTES*2+1024)*INPUT_RATE/1000000


def grade_case(create,inputs,ledger,folder):
    grade={}
    for purpose,body in initial_requests(inputs):
        grade.update(parsed(ledger.call(create,body,folder/(purpose+'.json')),body['response_format']['json_schema']['schema']))
    body=review_request(inputs,grade)
    return grade,parsed(ledger.call(create,body,folder/'review.json'),contract.review_schema())
