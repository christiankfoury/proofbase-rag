"""One-shot model reanalysis of saved responses, with offline replay and immutable inputs."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.fresh_eval_protocol import FOLDER,digest,verify_custody
from scripts.fresh_eval_budget import Ledger
from scripts.reliable_evaluation_run import write_json_atomic
from scripts.dimension_grader import VERSION,grade_response,dimensions
OUT=ROOT/'data/evaluation/dimension-reanalysis-v1'
CODE=['scripts/dimension_grader.py','scripts/reanalyze_saved_answers.py','scripts/dimension_calibration.py','scripts/fresh_eval_budget.py']
DIMS=['factual_support','completeness','relevance','citation_support','quotation_fidelity','response_behavior']


def code_hashes():
    return {p:hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in CODE}


def build_inputs(case,row):
    import yaml
    from apps.api.app.permissions.access_control import role_can_access
    payload=row['raw_response'];sources=[];cited=[];allowed={}
    tenant='00000000-0000-0000-0000-000000002801'
    for i,e in enumerate(row['authorized_evidence'],1):
        if (not role_can_access(e['access_roles'],case['user_role']) or e['project_id']!=case['project_id']
            or e['tenant_id']!=tenant or (case.get('department_id') and e['department_id']!=case['department_id'])):raise ValueError('Saved evidence access mismatch')
        sid=f'R{i}';sources.append({'source_id':sid,'text':e['content']});allowed[str(e['chunk_id'])]=(sid,e)
    for i,f in enumerate(case['required_facts'],1):
        path=(ROOT/f['source_path']).resolve()
        if not path.is_relative_to(ROOT/'data/synthetic-documents'):raise ValueError('Invalid gold source')
        raw=path.read_text(encoding='utf-8');meta=yaml.safe_load(raw.split('---',2)[1])
        if not role_can_access(meta['access_roles'],case['user_role']):raise ValueError('Unauthorized gold source')
        if ' '.join(f['source_quote'].split()) not in ' '.join(raw.split()):raise ValueError('Gold quote mismatch')
        sources.append({'source_id':f'G{i}','text':f['source_quote']})
    for i,c in enumerate(payload.get('citations',[]),1):
        pair=allowed.get(str(c.get('chunk_id')))
        if pair and pair[1]['document_id']==c.get('document_id'):
            cited.append({'citation_id':f'C{i}','source_id':pair[0],'text':pair[1]['content']})
    return {'question':case['question'],'history_not_evidence':case.get('previous_turns',[]),
        'answer':payload.get('answer',''),'expected_behavior':case['expected_behavior'],
        'required_facts':[{'fact_id':f['fact_id'],'text':f['text']} for f in case['required_facts']],
        'forbidden_assertions':case.get('forbidden_assertions',[]),'factual_sources':sources,'cited_sources':cited}


def initialize():
    if OUT.exists():raise ValueError('Reanalysis folder already exists')
    _,suite=verify_custody()
    OUT.mkdir(parents=True)
    shutil.copyfile(FOLDER/'api-ledger.json',OUT/'api-ledger.json')
    rows={c['case_id']:digest(FOLDER/'run-v2'/f"{c['case_id']}.json") for c in suite['cases']}
    manifest={'version':VERSION,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'source_suite_sha256':digest(FOLDER/'holdout.json'),'original_report_sha256':digest(FOLDER/'public-report.json'),
        'original_ledger_sha256':digest(FOLDER/'api-ledger.json'),'original_cost_usd':Ledger(OUT/'api-ledger.json').spent,
        'source_records':rows,'initialized_at':datetime.now(timezone.utc).isoformat(),'human_review':'not_completed',
        'user_agreement':'User accepted agent observations; no individual human decisions inferred.'}
    write_json_atomic(OUT/'manifest.json',manifest)


def check_inputs():
    _,suite=verify_custody()
    m=json.loads((OUT/'manifest.json').read_text())
    assert m['source_suite_sha256']==digest(FOLDER/'holdout.json')
    assert m['original_report_sha256']==digest(FOLDER/'public-report.json')
    assert m['original_ledger_sha256']==digest(FOLDER/'api-ledger.json')
    original=json.loads((FOLDER/'api-ledger.json').read_text())
    continued=json.loads((OUT/'api-ledger.json').read_text())
    assert continued['calls'][:len(original['calls'])]==original['calls'], 'Original ledger prefix changed'
    assert continued['limit_usd']==original['limit_usd']==0.75
    assert all(h==digest(FOLDER/'run-v2'/f'{cid}.json') for cid,h in m['source_records'].items())
    return suite,m


def freeze():
    check_inputs()
    cal=json.loads((OUT/'calibration.json').read_text())
    assert cal['passed']==cal['total'] and cal['total']>=10
    assert all(cal['code_hashes'][p]==code_hashes()[p] for p in CODE if p!='scripts/reanalyze_saved_answers.py')
    assert not (OUT/'freeze.json').exists()
    write_json_atomic(OUT/'freeze.json',{'code_hashes':code_hashes(),'calibration_sha256':digest(OUT/'calibration.json'),
        'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'frozen_at':datetime.now(timezone.utc).isoformat()})


def replay():
    suite,m=check_inputs();f=json.loads((OUT/'freeze.json').read_text())
    assert f['code_hashes']==code_hashes() and f['calibration_sha256']==digest(OUT/'calibration.json')
    results=[]
    for c in suite['cases']:
        path=OUT/'rows'/f"{c['case_id']}.json"
        if not path.exists():continue
        saved=json.loads(path.read_text());row=json.loads((FOLDER/'run-v2'/path.name).read_text());inputs=build_inputs(c,row)
        assert saved['inputs']==inputs and saved['source_sha256']==m['source_records'][c['case_id']]
        d=dimensions(inputs,saved.get('grade'),row['raw_response'],row['authorized_evidence'],row['safety_flags'])
        assert saved['dimensions']==d
        results.append({'case_id':c['case_id'],'original_passed':row['passed'],'dimensions':d,'record_sha256':digest(path)})
    ledger=Ledger(OUT/'api-ledger.json')
    return {'version':VERSION,'kind':'saved_response_evaluator_reanalysis','cases_expected':60,'cases_processed':len(results),
        'complete':len(results)==60,'original_protocol_passes':33,'original_protocol_total':60,
        'human_review':'not_completed','dimensions':{k:dict(Counter(r['dimensions'][k] for r in results)) for k in DIMS},
        'invalid_grades':sum(bool(r['dimensions']['grader_errors']) for r in results),
        'cumulative_cost_usd':ledger.spent,'reanalysis_cost_usd':ledger.spent-m['original_cost_usd'],
        'cases':results,'limitation':'Model judgments on available authorized evidence; not human accuracy or runtime improvement. No composite pass rate.'}


def run():
    suite,m=check_inputs();f=json.loads((OUT/'freeze.json').read_text())
    assert f['code_hashes']==code_hashes() and f['calibration_sha256']==digest(OUT/'calibration.json')
    rows=OUT/'rows'
    if rows.exists():raise ValueError('Reanalysis already started; no retry')
    rows.mkdir()
    from apps.api.app.core.config import get_settings
    from openai import OpenAI
    ledger=Ledger(OUT/'api-ledger.json')
    with ledger.intercept():
        client=OpenAI(api_key=get_settings().openai_api_key)
        for case in suite['cases']:
            cid=case['case_id'];row=json.loads((FOLDER/'run-v2'/f'{cid}.json').read_text());inputs=build_inputs(case,row)
            saved={'case_id':cid,'source_sha256':m['source_records'][cid],'inputs':inputs,'status':'started'}
            path=rows/f'{cid}.json';write_json_atomic(path,saved)
            try:
                saved['grade']=grade_response(client,inputs);saved['status']='graded'
            except Exception as exc:
                saved['status']='interrupted';saved['exception_type']=type(exc).__name__
                saved['dimensions']=dimensions(inputs,None,row['raw_response'],row['authorized_evidence'],row['safety_flags'])
                write_json_atomic(path,saved);raise
            saved['dimensions']=dimensions(inputs,saved['grade'],row['raw_response'],row['authorized_evidence'],row['safety_flags'])
            write_json_atomic(path,saved);print(f'Graded {cid}',flush=True)
    write_json_atomic(OUT/'report.json',replay())


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--initialize',action='store_true');ap.add_argument('--freeze',action='store_true');ap.add_argument('--allow-external-ai',action='store_true');ap.add_argument('--check',action='store_true');args=ap.parse_args()
    if args.initialize:initialize()
    elif args.freeze:freeze()
    elif args.allow_external_ai:run()
    else:
        report=replay()
        if args.check:
            assert json.loads((OUT/'report.json').read_text())==report;print('Reanalysis records, input hashes and dimension aggregates verified offline')
        else:write_json_atomic(OUT/'report.json',report)

if __name__=='__main__':main()
