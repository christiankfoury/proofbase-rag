"""Offline whole-stage payload reservation. Never submits provider calls."""
import json
import os
from pathlib import Path
import sys
from decimal import Decimal
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.quality_cost_phase73_v2 import SpendJournal, live_policy
from scripts.quality_cost_control import digest
from scripts.reliability_payload_budget import encoding
from apps.api.app.generation import conversational_candidate as c
from apps.api.app.core.config import get_settings

FOLDER=ROOT/'data/evaluation/bounded-redesign'
PROFILES=['v4','candidate-mini','candidate-challenger']


def configure(profile):
    os.environ.update(CONVERSATIONAL_CANDIDATE_ENABLED='false' if profile=='v4' else 'true',
        CONVERSATIONAL_CANDIDATE_MODEL=c.CHALLENGER if profile=='candidate-challenger' else c.MINI,
        OPENAI_CHAT_MODEL=c.MINI,REQUEST_ASSESSMENT_MODEL=c.MINI,EVIDENCE_ASSESSMENT_MODEL=c.MINI,
        POST_GENERATION_VALIDATION_MODEL=c.MINI,EVIDENCE_ASSESSMENT_PROMPT_VERSION='v4',
        POST_GENERATION_VALIDATION_PROMPT_VERSION='v4',REQUEST_ASSESSMENT_MODE='semantic_all_remaining',
        EXTERNAL_AI_MAX_RETRIES='0',PROOFBASE_TELEMETRY_ENABLED='false',
        OBSERVABILITY_LOG_PATH='data/observability/local-runs/bounded-redesign.jsonl')
    get_settings.cache_clear()


def prepare(body):
    body=dict(body,service_tier='default')
    if body['model']=='gpt-4.1-mini':body['model']=c.MINI
    if body.get('stream') or body.get('tools') or body.get('functions') or body.get('n',1)!=1 or body['model'] not in c.PRICES:
        raise ValueError('Unpriced application request')
    if 'max_completion_tokens' not in body:
        body['max_completion_tokens']=2048
    body=json.loads(json.dumps(body,ensure_ascii=False,sort_keys=True))
    cap=body['max_completion_tokens']
    if type(cap)!=int or not 0<cap<=2048:raise ValueError('Output allowance exceeded')
    # Exact serialized payload with a conservative framing margin. Any future
    # authorized runner must enforce these bounds; this script never submits.
    # Both fixed profiles use o200k_base; tiktoken 0.12 predates the 5.4 alias.
    bound=len(encoding(c.MINI).encode(json.dumps(body,ensure_ascii=False),disallowed_special=()))+2048
    if bound>16384:raise ValueError('Input bound exceeded')
    ri,_,ro=map(Decimal,c.PRICES[body['model']])
    return body,dict(input_bound=bound,output_cap=cap,reserved_usd=str((bound*ri+cap*ro)/1000000))


def preflight():
    if (FOLDER/'preflight-complete.json').exists():
        raise ValueError('Attempt already preflighted; preserve the stopped result')
    from scripts.bounded_redesign_support import invoke
    from openai.resources.chat.completions import Completions
    from openai.types.chat import ChatCompletion
    from apps.api.app.reasoning.request_assessment import _base_continue_decision
    suite=json.loads((FOLDER/'development.json').read_bytes())
    if len(suite['cases'])!=12 or sum(len(x['turns'])==2 for x in suite['cases'])!=3:raise ValueError('Task manifest differs')
    bodies=[];errors=[]
    # Offline plumbing responses only, deliberately not stored as quality scores.
    for profile in PROFILES:
        configure(profile)
        for case in suite['cases']:
            def create(resource,**body):
                try:body,limits=prepare(body)
                except Exception as exc:
                    errors.append(type(exc).__name__);raise
                name=body.get('response_format',{}).get('json_schema',{}).get('name','generation')
                bodies.append(dict(profile=profile,case_id=case['id'],stage=name,request=body,**limits))
                sources=[x for x in suite['sources'] if x['chunk_id'] in case['source_ids'] and 'Employee' in x['access_roles']]
                source=sources[0] if sources else None
                draft=dict(answer=source['content'] if source else 'The available sources do not establish the answer.',
                    response_type='answer' if source else 'not_found',citations=[dict(chunk_id=source['chunk_id'],citation_text=source['content'])] if source else [])
                if name.startswith('request_assessment'):
                    value=_base_continue_decision().model_dump()
                elif name.startswith('evidence_assessment'):
                    ids=[s['chunk_id'] for s in sources]
                    value=dict(answerability='sufficient',required_facts=[dict(fact_id='f1',description='Policy',support='supported',supporting_chunk_ids=ids)],conflicts=[],missing_information=[],supporting_chunk_ids=ids,assessment_confidence=.95)
                elif name=='conversational_producer':value=draft
                elif name=='conversational_checker':
                    value=dict(decision='accept',reason='Offline payload preparation only.',**{k:True for k in c.Check.model_fields if k not in {'decision','reason'}})
                elif name.startswith('post_generation_validation'):
                    payload=json.loads(body['messages'][1]['content']);units=payload['candidate_units'];cid=source['chunk_id']
                    value=dict(claims=[dict(**u,claim_type='semantic',support_status='supported',evidence_chunk_ids=[cid]) for u in units],
                        citation_checks=[dict(citation_chunk_id=cid,supports_claims=True,supported_claim_ids=[u['claim_id'] for u in units])],
                        source_instruction_followed=False,source_instruction_evidence_chunk_ids=[],unresolved_conflict=False,numeric_context=[],
                        scope_checks=[dict(claim_id=u['claim_id'],preserves_scope=True,explanation='Offline') for u in units])
                else:
                    value=dict(draft,supported_claims=[draft['answer']],unsupported_claims=[],validation_notes='Offline')
                    if source:value['citations']=[{k:source[k] for k in ['document_id','document_title','section_heading','chunk_id']}|dict(citation_text=source['content'])]
                return ChatCompletion(id='offline',object='chat.completion',created=0,model=body['model'],
                    choices=[dict(index=0,finish_reason='stop',message=dict(role='assistant',content=json.dumps(value)))],
                    usage=dict(prompt_tokens=100,completion_tokens=50,total_tokens=150))
            with patch.object(Completions,'create',create),patch('httpx.HTTPTransport.handle_request',side_effect=AssertionError('Offline only')):
                result=invoke(suite,case)
                if any(t['status_code']!=200 for t in result['turns']):
                    errors.append(profile+':'+case['id']+':offline_application_error')
    if errors:raise ValueError('Incomplete payload preparation: '+repr(errors))
    # Budget all declared turns even if an offline routing shortcut skipped one.
    # Legacy may repair once: reserve two generation and two validation calls.
    # Dynamic outputs/history receive additional input headroom per call.
    allocations={};templates={}
    for profile in PROFILES:
        selected=[b for b in bodies if b['profile']==profile]
        stages={b['stage'] for b in selected};total=Decimal(0);rows=[]
        required=({'request_assessment_v1','evidence_assessment_v1','generated_answer_v1','post_generation_validation_v1'}
                  if profile=='v4' else {'request_assessment_v1','conversational_producer','conversational_checker'})
        if not required<=stages:raise ValueError('Missing payload stages: '+repr(required-stages))
        for stage in sorted(stages):
            samples=[b for b in selected if b['stage']==stage]
            maximum=max(samples,key=lambda b:Decimal(b['reserved_usd']))
            ri,_,ro=map(Decimal,c.PRICES[maximum['request']['model']])
            bound=maximum['input_bound']+2048
            if bound>16384:raise ValueError('Insufficient dynamic payload headroom')
            count=15*(2 if profile=='v4' and (stage=='generated_answer_v1' or stage.startswith('post_generation_validation')) else 1)
            amount=(bound*ri+maximum['output_cap']*ro)/1000000
            total+=count*amount
            rows.append(dict(stage=stage,count=count,input_bound=bound,output_cap=maximum['output_cap'],model=maximum['request']['model'],reservation_usd=str(count*amount)))
        allocations[profile]=str(total);templates[profile]=rows
    total=sum(map(Decimal,allocations.values()),Decimal(0))
    journal=SpendJournal().load();_,ceiling=live_policy()
    remainder=ceiling-sum((Decimal(r['accounted_usd']) for r in journal['entries'].values()),Decimal(0))
    if remainder!=Decimal('3.73106560'):raise ValueError('Historical remainder changed')
    result=dict(status='ready' if total<=Decimal('1.30') else 'stopped_budget_preflight',
        application_stage_cap_usd='1.30',total_reservation_usd=str(total),profiles=allocations,
        bounds=templates,prepared_payloads=bodies,prior_journal=journal,prior_remainder_usd=str(remainder),
        attempt_total_usd='10.00',additional_allowance_usd='6.26893440',provider_retries=0,
        measurement_launch_floor_usd='4.50',suite_sha256=digest(FOLDER/'development.json'),
        method='Complete serialized payloads plus 2048 framing and 2048 dynamic input tokens; all 15 turns and baseline repair pair; no cache discount.')
    if (FOLDER/'preflight-complete.json').exists():raise ValueError('Preflight already declared; do not overwrite')
    write(FOLDER/'preflight-complete.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in {'prepared_payloads','prior_journal','bounds'}}))


if __name__=='__main__':preflight()
