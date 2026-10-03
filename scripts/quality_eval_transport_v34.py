"""V34 coherent prompts with unchanged pinned transport and allowances."""
from scripts import quality_eval_transport_v24 as base
from scripts import quality_eval_contract_v34 as contract
from scripts.quality_eval_transport_v24 import MODEL,CAPS,MAX_CANDIDATE_BYTES,INPUT_RATE,OUTPUT_RATE,BudgetStop,parsed,exclusive_lock
import json
from decimal import Decimal


def request(purpose,prompt,data,schema):
    body=base.request(purpose,prompt,data,schema)
    body['reasoning_effort']='medium' if purpose=='review' else 'high'
    return body


def reserve(body):
    purpose=body.get('response_format',{}).get('json_schema',{}).get('name','').removeprefix('quality_')
    if (body.get('model')!=MODEL or body.get('reasoning_effort')!=('medium' if purpose=='review' else 'high') or body.get('stream')
            or body.get('tools') or purpose not in CAPS or body.get('max_completion_tokens')!=CAPS[purpose]):
        raise BudgetStop('Unapproved grader request or output allowance')
    bound=len(json.dumps(body,ensure_ascii=False).encode('utf-8'))+2048
    if bound>272000:raise BudgetStop('Unpriced long context')
    cap=CAPS[purpose]
    return dict(input_bound=bound,output_cap=cap,reserved_usd=(bound*INPUT_RATE+cap*OUTPUT_RATE)/1000000)


def initial_requests(inputs):
    parts=contract.request_parts(inputs)
    requests=base.initial_requests(inputs)
    for (purpose,body),part in zip(requests,parts):
        body['messages'][0]['content']=part['prompt']
        body['reasoning_effort']='medium' if purpose=='review' else 'high'
        if purpose=='claims':
            item=body['response_format']['json_schema']['schema']['properties']['claims']['items']
            order=['text','reason','factual_status','citation_status','source_spans','citation_spans']
            item['required']=order
            item['properties']={k:item['properties'][k] for k in order}
        if purpose=='coverage':
            # Generate request interpretation before facts; identical fields/types.
            schema=body['response_format']['json_schema']['schema']
            order=['relevance','actual_behavior','behavior_span','behavior_reason','facts','forbidden_assertion']
            schema['required']=order
            schema['properties']={k:schema['properties'][k] for k in order}
            relevance=schema['properties']['relevance']
            relevance['required']=['reason','status']
            relevance['properties']={k:relevance['properties'][k] for k in ['reason','status']}
    return requests


def review_request(inputs,candidate):
    body=base.review_request(inputs,candidate)
    body['messages'][0]['content']=contract.REVIEW_PROMPT
    body['reasoning_effort']='medium'
    schema=body['response_format']['json_schema']['schema']
    order=['reason']+[k for k in schema['properties'] if k!='reason']
    schema['required']=order
    schema['properties']={k:schema['properties'][k] for k in order}
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
