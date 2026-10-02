"""One frozen eight-call component experiment; no retrieval, generation or grading."""
import argparse
from dataclasses import asdict, fields
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.quality_cost_phase73_v2 import SpendJournal, live_policy
from scripts.reliability_payload_preparation import prepare_request
from scripts.phase73_v6_budget import response_charge, request_hash
from scripts.quality_eval_transport_v23 import exclusive_lock

FOLDER=ROOT/'data/evaluation/conversational-scenario'
INITIAL=Decimal('3.74777920')
CEILING=Decimal('.50')


def read(path):return json.loads(Path(path).read_bytes())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()


def configure():
    os.environ['EVIDENCE_ASSESSMENT_PROMPT_VERSION']='v5'
    os.environ['EXTERNAL_AI_MAX_RETRIES']='0'
    os.environ['PROOFBASE_TELEMETRY_ENABLED']='false'
    from apps.api.app.core.config import get_settings
    get_settings.cache_clear()
    settings=get_settings()
    if not settings.openai_api_key or settings.evidence_assessment_model!='gpt-4.1-mini':
        raise ValueError('Missing credential or unexpected model')
    return settings


def context():
    from apps.api.app.retrieval.types import RetrievedChunk
    from apps.api.app.permissions.access_control import unauthorized_chunks
    from apps.api.app.reasoning.request_assessment import RequestAssessment, _base_continue_decision
    suite=read(FOLDER/'cases.json')
    saved=read(ROOT/suite['source_capture'])
    sources={c['chunk_id']:c for c in saved['authorized_evidence']}
    chunks=[RetrievedChunk(**{k:v for k,v in {**c,**sources[c['chunk_id']]}.items()
        if k in {f.name for f in fields(RetrievedChunk)}}) for c in saved['raw_response']['retrieved_chunks']]
    scope=dict(effective_role='Employee',project_id=saved['request']['project_id'],department_id=None)
    if unauthorized_chunks(chunks,'Employee') or any(c.project_id!=scope['project_id'] for c in chunks):
        raise ValueError('Frozen source authorization differs')
    # Explicit test boundary: no live request assessment, retrieval or identity.
    assessment=RequestAssessment(**_base_continue_decision().model_dump(),route='deterministic_continue',status='skipped',
        response_reason=None,model=None,prompt_version=None,latency_ms=0,input_tokens=0,output_tokens=0,
        input_cost_usd=0,output_cost_usd=0,estimated_cost_usd=0,pricing_status='not_applicable')
    return suite,chunks,scope,assessment


def assess(case,chunks,request,create):
    from apps.api.app.reasoning.evidence_assessment import assess_evidence
    client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return assess_evidence(case['question'],original_question=case['question'],request_assessment=request,
        authorized_chunks=chunks,multi_document=False,mode='hybrid',client=client,emit_telemetry=False)


def prepare(body):
    body=dict(body,service_tier='default',max_completion_tokens=2048)
    if body['response_format']['json_schema']['name']!='evidence_assessment_v5':
        raise ValueError('Only existing evidence-assessment calls authorized')
    return prepare_request(body,'chat')


def budget():
    journal=SpendJournal().load();_,ceiling=live_policy()
    if any(r['status']!='settled' for r in journal['entries'].values()):
        raise ValueError('Unknown or unsettled historical charge')
    remainder=ceiling-sum((Decimal(r['accounted_usd']) for r in journal['entries'].values()),Decimal(0))
    if remainder!=INITIAL:raise ValueError('Predeclared remaining budget changed')
    return journal


def preflight():
    configure();journal=budget();suite,chunks,scope,request=context()
    if len(suite['cases'])!=8 or len({c['id'] for c in suite['cases']})!=8:
        raise ValueError('Exactly eight unique cases required')
    bodies=[]
    for case in suite['cases']:
        def capture(**body):
            bodies.append(prepare(body)[0])
            raise RuntimeError('Offline payload capture, no provider submission')
        assess(case,chunks,request,capture)
    if len(bodies)!=8:raise ValueError('Existing route did not construct exactly eight requests')
    bounds=[prepare_request(b,'chat')[1] for b in bodies]
    total=sum((b[2] for b in bounds),Decimal(0))
    if total>CEILING:raise ValueError('Payload preflight exceeds allocation')
    files=list((ROOT/'apps/api/app').rglob('*.py'))+list((ROOT/'apps/api/app/prompts/versions').glob('*.md'))
    files += [Path(__file__),FOLDER/'cases.json',ROOT/suite['source_capture'],ROOT/'requirements.txt',
        ROOT/'scripts/reliability_payload_preparation.py',ROOT/'scripts/reliability_payload_budget.py',
        ROOT/'scripts/phase73_v6_budget.py',ROOT/'scripts/quality_cost_phase73_v2.py']
    report=dict(created_at=now(),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        prices=dict(source='https://developers.openai.com/api/docs/models/gpt-4.1-mini',verified_on='2026-10-02',
                    input_per_million='.40',cached_input_per_million='.10',output_per_million='1.60'),
        initial_remainder_usd=str(INITIAL),allocation_usd=str(CEILING),maximum_calls=8,provider_retries=0,
        maximum_input_tokens=16384,maximum_output_tokens=2048,absolute_upper_bound_usd='0.07864320',
        prepared_upper_bound_usd=str(total),payload_input_bounds=[b[0] for b in bounds],
        bindings={p.relative_to(ROOT).as_posix():digest(p) for p in files},
        initial_journal=journal,requests=bodies)
    path=FOLDER/'preflight.json'
    if path.exists():raise ValueError('Preserve existing preflight; do not overwrite')
    write(path,report)
    print(json.dumps({k:report[k] for k in ['prepared_upper_bound_usd','payload_input_bounds','maximum_calls']}))


def run():
    settings=configure();journal=SpendJournal();initial=budget()
    plan=read(FOLDER/'preflight.json');suite,chunks,scope,request=context()
    if initial!=plan['initial_journal'] or any(digest(ROOT/p)!=h for p,h in plan['bindings'].items()):
        raise ValueError('Frozen evidence/runtime or accounting changed')
    if subprocess.check_output(['git','diff','HEAD','--',*plan['bindings']],cwd=ROOT,text=True).strip():
        raise ValueError('Commit frozen runtime before execution')
    from openai import OpenAI
    from apps.api.app.reasoning import scenario_calculation as sc
    from apps.api.app.reasoning.scenario_input import ScenarioExtraction
    api=OpenAI(api_key=settings.openai_api_key,max_retries=0,timeout=30)
    if str(api.base_url)!='https://api.openai.com/v1/':raise ValueError('Unexpected endpoint')
    folder=FOLDER/'run'
    folder.mkdir()  # One shot: existing output is never retried/resumed.
    manifest=dict(status='running',started_at=now(),runtime_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  preflight_sha256=digest(FOLDER/'preflight.json'),rows=[],charged_usd='0')
    write(folder/'manifest.json',manifest)
    try:
        for i,case in enumerate(suite['cases']):
            calls=[];raw_path=folder/(case['id']+'-raw.json')
            def create(**body):
                if calls or i>=8:raise ValueError('Additional call prohibited')
                calls.append(True)
                canonical,(bound,cap,reserved)=prepare(body)
                if canonical!=plan['requests'][i] or Decimal(manifest['charged_usd'])+reserved>CEILING:
                    raise ValueError('Payload or allocation differs')
                identity='conversational-scenario-v1-'+case['id']
                entry=dict(request=canonical,status='reserved',response=None,reserved_usd=str(reserved))
                journal.reserve(identity,reserved,request_hash(canonical));write(raw_path,entry)
                try:
                    response=api.chat.completions.create(**canonical)
                    raw=response.model_dump(mode='json');entry.update(response=raw,status='received');write(raw_path,entry)
                    cost=response_charge(raw,canonical['model'])
                    if not 0<=raw['usage']['prompt_tokens']<=bound or not 0<=raw['usage']['completion_tokens']<=cap or cost>reserved:
                        raise ValueError('Provider exceeded reserved bounds')
                    journal.finish(identity,cost,digest(raw_path))
                    manifest['charged_usd']=str(Decimal(manifest['charged_usd'])+cost)
                    write(folder/'manifest.json',manifest)
                    return response
                except BaseException as exc:
                    entry.update(status='unknown',exception_type=type(exc).__name__);write(raw_path,entry)
                    journal.finish(identity,Decimal(0),digest(raw_path),uncertain=True)
                    raise
            assessed=assess(case,chunks,request,create)
            if not calls or not raw_path.exists() or read(raw_path)['status']!='received':
                raise ValueError('Provider outcome unavailable; stop without retry')
            raw=read(raw_path)['response']
            answer=sc.prepare_conversational(case['question'],chunks,assessed,request_assessment=request,**scope)
            validation=sc.finalize(case['question'],answer,chunks,assessment=assessed,**scope) if answer else None
            accepted=bool(answer and validation.action=='accept')
            parsed=json.loads(raw['choices'][0]['message']['content'])
            proposal=ScenarioExtraction.model_validate(parsed['scenario'])
            binding=sc.calculate(case['question'],chunks,extraction=proposal,**scope)
            correct=(proposal.scope==case['scope'])
            if case['scope']=='row_comparison':
                correct=correct and proposal.complete_request and not proposal.unhandled_parts and binding is not None and (
                    proposal.amount_quote==case['amount'] and proposal.category_quote==case['category'] and binding.above_limit==case['above'])
            else:
                correct=correct and all(getattr(proposal,k) is None for k in ['amount_quote','category_quote','source_chunk_id'])
            row=dict(case_id=case['id'],question=case['question'],expected_scope=case['scope'],proposal=proposal.model_dump(),
                correct_interpretation=bool(correct),unsafe_acceptance=accepted and case['scope']!='row_comparison',
                unnecessary_rejection=not accepted and case['scope']=='row_comparison',accepted=accepted,
                assessment=assessed.model_dump(mode='json'),calculation=asdict(answer['_scenario_calculation']) if answer else None,
                answer=answer['answer'] if answer else None,citations=answer['citations'] if answer else [],
                validation=validation.model_dump(mode='json') if validation else None,raw_sha256=digest(raw_path))
            path=folder/(case['id']+'.json');write(path,row)
            manifest['rows'].append(dict(case_id=case['id'],sha256=digest(path)))
            write(folder/'manifest.json',manifest)
            print(f"{case['id']}: correct={correct}, accepted={accepted}, total USD {manifest['charged_usd']}",flush=True)
            if assessed.status=='failed_safe' or row['unsafe_acceptance']:
                raise ValueError('Assessment failure or unsafe acceptance; stop experiment')
        manifest['status']='complete'
    except BaseException as exc:
        manifest.update(status='stopped',exception_type=type(exc).__name__)
        raise
    finally:
        current=journal.load();_,ceiling=live_policy()
        manifest.update(finished_at=now(),remaining_usd=str(ceiling-sum((Decimal(r['accounted_usd']) for r in current['entries'].values()),Decimal(0))))
        write(folder/'additional-spend.json',current);write(folder/'manifest.json',manifest)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',action='store_true');parser.add_argument('--approve-live',action='store_true')
    args=parser.parse_args()
    if args.preflight and not args.approve_live:preflight()
    elif args.approve_live and not args.preflight:
        with exclusive_lock(FOLDER):run()
    else:parser.error('Choose offline --preflight or the explicitly authorized --approve-live')
