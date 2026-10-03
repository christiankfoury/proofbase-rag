"""Offline receipt/custody verification for the single frozen experiment."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from decimal import Decimal
from datetime import datetime
import json
from dataclasses import asdict
import hashlib
from scripts.conversational_scenario_diagnostic import FOLDER, read, digest, INITIAL, context
from scripts.phase73_v6_budget import response_charge, request_hash
from scripts.reliability_payload_preparation import prepare_request


def report():
    from apps.api.app.reasoning import scenario_calculation as sc
    from apps.api.app.reasoning.scenario_input import ScenarioExtraction
    from apps.api.app.reasoning.evidence_assessment import EvidenceAssessment
    _,chunks,scope,request=context()
    plan=read(FOLDER/'preflight.json');suite=read(FOLDER/'cases.json');folder=FOLDER/'run'
    manifest=read(folder/'manifest.json');journal=read(folder/'additional-spend.json')
    if manifest['status']!='complete' or manifest['preflight_sha256']!=digest(FOLDER/'preflight.json'):
        raise ValueError('Incomplete experiment or changed preflight')
    if any(digest(ROOT/p)!=sha for p,sha in plan['bindings'].items()):
        raise ValueError('Frozen inputs changed')
    old=plan['initial_journal']['entries'];new=journal['entries']
    if any(new.get(k)!=v for k,v in old.items()):raise ValueError('Historical accounting changed')
    expected={'conversational-scenario-v1-'+c['id'] for c in suite['cases']}
    if set(new)-set(old)!=expected:raise ValueError('Unexpected spending entries')
    rows=[];spent=Decimal(0);inputs=outputs=cached=0
    for i,case in enumerate(suite['cases']):
        p=folder/(case['id']+'.json');r=read(p);raw_path=folder/(case['id']+'-raw.json');raw=read(raw_path)
        m=manifest['rows'][i];entry=new['conversational-scenario-v1-'+case['id']]
        if (m['case_id']!=case['id'] or m['sha256']!=digest(p) or r['raw_sha256']!=digest(raw_path)
                or raw['status']!='received' or raw['request']!=plan['requests'][i]
                or entry['status']!='settled' or entry['result_sha256']!=digest(raw_path)
                or entry['evidence_sha256']!=request_hash(raw['request'])):
            raise ValueError('Receipt or result custody differs')
        _,(bound,cap,reserved)=prepare_request(raw['request'],'chat')
        usage=raw['response']['usage'];cost=response_charge(raw['response'],raw['request']['model'])
        if (usage['prompt_tokens']>bound or usage['completion_tokens']>cap or cost>reserved
                or Decimal(entry['reserved_usd'])!=reserved or Decimal(entry['accounted_usd'])!=cost):
            raise ValueError('Usage or settlement differs')
        spent+=cost;inputs+=usage['prompt_tokens'];outputs+=usage['completion_tokens']
        cached+=usage['prompt_tokens_details']['cached_tokens']
        proposal=json.loads(raw['response']['choices'][0]['message']['content'])['scenario']
        if proposal!=r['proposal']:raise ValueError('Saved extraction differs from receipt')
        extraction=ScenarioExtraction(**proposal)
        binding=sc.calculate(case['question'],chunks,extraction=extraction,**scope)
        correct=proposal['scope']==case['scope']
        if case['scope']=='row_comparison':
            correct=correct and proposal['complete_request'] and not proposal['unhandled_parts'] and binding is not None and (
                proposal['amount_quote']==case['amount'] and proposal['category_quote']==case['category'] and binding.above_limit==case['above'])
        else:
            correct=correct and all(proposal[k] is None for k in ['amount_quote','category_quote','source_chunk_id'])
        assessed=EvidenceAssessment(**r['assessment'],scenario=extraction,
            scenario_request_sha256=hashlib.sha256(case['question'].encode()).hexdigest())
        answer=sc.prepare_conversational(case['question'],chunks,assessed,request_assessment=request,**scope)
        validated=sc.finalize(case['question'],answer,chunks,assessment=assessed,**scope) if answer else None
        accepted=bool(answer and validated.action=='accept')
        calculated=json.loads(json.dumps(asdict(answer['_scenario_calculation']))) if answer else None
        if (r['correct_interpretation']!=bool(correct) or r['accepted']!=accepted
                or r['unsafe_acceptance']!=(accepted and case['scope']!='row_comparison')
                or r['unnecessary_rejection']!=(not accepted and case['scope']=='row_comparison')
                or r['calculation']!=calculated or r['answer']!=(answer['answer'] if answer else None)
                or r['citations']!=(answer['citations'] if answer else [])):
            raise ValueError('Interpretation metrics or deterministic replay differ')
        rows.append(dict(case_id=case['id'],scope_correct=proposal['scope']==case['scope'],
                         correct_interpretation=r['correct_interpretation'],accepted=r['accepted'],
                         unsafe_acceptance=r['unsafe_acceptance'],unnecessary_rejection=r['unnecessary_rejection'],
                         cost_usd=str(cost)))
    if Decimal(manifest['charged_usd'])!=spent or Decimal(manifest['remaining_usd'])!=INITIAL-spent:
        raise ValueError('Manifest accounting differs')
    return dict(runtime_commit=manifest['runtime_commit'],cases=8,live_calls=8,
        correct_interpretation={'numerator':sum(r['correct_interpretation'] for r in rows),'denominator':8},
        scope_classification={'numerator':sum(r['scope_correct'] for r in rows),'denominator':8},
        unsafe_calculator_acceptance={'numerator':sum(r['unsafe_acceptance'] for r in rows),'denominator':5},
        unnecessary_calculator_rejection={'numerator':sum(r['unnecessary_rejection'] for r in rows),'denominator':3},
        input_tokens=inputs,cached_input_tokens=cached,output_tokens=outputs,
        actual_cost_usd=str(spent),remaining_usd=str(INITIAL-spent),
        elapsed_seconds=(datetime.fromisoformat(manifest['finished_at'])-datetime.fromisoformat(manifest['started_at'])).total_seconds(),
        elapsed_note='Frozen run manifest wall time; includes local persistence.',
        history_unchanged=True,unknown_outcomes=0,rows=rows,
        interpretation_note='Predeclared complete extraction contract, including exact bindings and null fields for declined scopes; scope-only diagnostic shown separately.',
        limitation='Component diagnostic with frozen synthetic sources. Not live retrieval or final fallback-answer evaluation. Mocked tests excluded.')


if __name__=='__main__':
    result=report()
    if '--record' in sys.argv:
        with (FOLDER/'results.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
