"""Structured blind one-shot qualification under the replacement USD10 balance."""
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.structured_blind_execution_budget_v2 import FOLDER, CEILING, FINAL_FLOOR, prefix, AUTHORIZATION, stage_budget
from scripts.bounded_redesign_run import read,digest,write,now,response_charge
from scripts.phase73_v6_budget import request_hash
from scripts import structured_blind_live_v2 as contract
from scripts import structured_blind_live_v2 as transport
from scripts import quality_development_v23 as existing
from scripts import conversation_ordering_v2 as references


class RollingLedger:
    def __init__(self,folder,plan):
        self.root=ROOT;self.folder=Path(folder);self.plan=plan
        self.data=dict(calls=[],unknown_outcome=False,stopped=False,prefix=plan['prefix'])
        if (self.folder/'api-ledger.json').exists():raise ValueError('Preserve existing ledger')
        self.save()

    def save(self):write(self.folder/'api-ledger.json',self.data)

    @property
    def accounted(self):
        return Decimal(self.plan['prefix']['spent_usd'])+sum((Decimal(r['accounted_usd']) for r in self.data['calls']),Decimal(0))

    def prepare_request(self,body):return body,transport.reserve(body)

    def call(self,create,body,path):
        with transport.exclusive_lock(FOLDER):
            if self.data['stopped'] or len(self.data['calls'])>=self.plan['maximum_calls']:
                raise transport.BudgetStop('Stopped or call allowance exhausted')
            # Include every historical and current receipt; forbid another writer.
            current=prefix()
            expected=dict(self.plan['prefix']['ledger_sha256'])
            expected[(self.folder/'api-ledger.json').relative_to(ROOT).as_posix()]=digest(self.folder/'api-ledger.json')
            if current['ledger_sha256']!=expected or Decimal(current['spent_usd'])!=self.accounted:
                raise transport.BudgetStop('Spending prefix changed')
            body,limits=self.prepare_request(body); amount=limits['reserved_usd'];path=Path(path)
            relative=path.resolve().relative_to(self.folder.resolve()).as_posix()
            if path.exists():raise transport.BudgetStop('No repeated request')
            protected = FINAL_FLOOR if self.plan['stage'] != 'final' else Decimal(0)
            if self.accounted+amount>CEILING-protected:
                self.data.update(stopped=True,stop_reason='Insufficient per-request headroom');self.save()
                raise transport.BudgetStop('Ceiling prevents submission')
            row=dict(status='reserved',raw_path=relative,request_sha256=request_hash(body),
                accounted_usd=str(amount),**{k:str(v) if isinstance(v,Decimal) else v for k,v in limits.items()})
            raw=dict(request=body,response=None,status='reserved')
            write(path,raw);self.data['calls'].append(row);self.save()
            try:
                response=create(**body);raw.update(status='received',response=response.model_dump(mode='json'));write(path,raw)
                usage=raw['response']['usage'];cost=response_charge(raw['response'],body['model'])
                if not(0<=usage['prompt_tokens']<=limits['input_bound'] and 0<=usage.get('completion_tokens',0)<=limits['output_cap'] and 0<=cost<=amount):
                    raise ValueError('Receipt exceeds reservation')
                row.update(status='completed',accounted_usd=str(cost),raw_sha256=digest(path));self.save()
                return response
            except BaseException as exc:
                raw['exception_type']=type(exc).__name__;write(path,raw)
                row.update(status='unknown',raw_sha256=digest(path))
                self.data.update(stopped=True,unknown_outcome=True);self.save();raise


cases, probes = references.cases, references.probes
BASELINE = FOLDER / 'structured-blind-v1/offline-assessment.json'


def versioned(version):
    if version != contract.VERSION: raise ValueError('Unfrozen evaluator version')
    return contract, transport


def judged(case, first, second, error=None):
    dims = contract.dimensions(case['inputs'], first, case['payload'], case['evidence'], case['safety_flags'], second)
    projected, invalid = contract.evaluator.project(case['inputs'], first)
    mismatch = existing.compare(case, projected, dims)
    expected = references.suite()['intermediate_expectations'].get(case['id'])
    if expected:
        for label, packet in (('a', first), ('b', second)):
            grade, errors = contract.evaluator.project(case['inputs'], packet)
            actual = None if errors else dict(
                facts={f['fact_id']: f['status'] for f in grade['facts']},
                claims=[{k:c[k] for k in ('text','factual_status','citation_status')} for c in grade['claims']])
            if actual != expected: mismatch['intermediate_'+label] = dict(expected=expected, actual=actual)
            if grade and any(c['source_spans'] or c['citation_spans'] for c in grade['claims']):
                mismatch['uncertainty_witnesses_'+label] = 'Unknown claims cannot gain support witnesses'
    return dict(grade=first, review=second, error=error, dimensions=dims, mismatches=mismatch,
        matched=not error and not mismatch and not dims['grader_errors'] and not dims['disputed_dimensions'])


def probe_result(case, first, second, error=None):
    review = contract.evaluator.probe_review(case['inputs'], case['payload'], case['evidence'],
        case['safety_flags'], first, second, case['candidate'])
    matched = not error and review['blind_status']=='agreement_only' and all(
        review[k] == ('dispute' if k in case['expected_disputes'] else 'agree')
        for k in contract.evaluator.KEYS)
    return dict(grade=first, second=second, review=review, error=error, matched=matched)


def reuse_for(stage, selected):
    saved = read(BASELINE)
    if digest(BASELINE) != read(AUTHORIZATION)['baseline_assessment_sha256']:
        raise ValueError('Reuse assessment changed')
    ids = {c['id'] for c in selected}
    return {r['case_id']: r for r in saved['reusable_components'] if r['stage']==stage and r['case_id'] in ids}


def require_gate(stage, count):
    path = FOLDER / ('structured-blind-v2-'+stage+'-acceptance.json')
    gate = read(path); report_path = ROOT / gate['report_path']; report = read(report_path)
    if (gate['version'] != contract.VERSION or gate['status'] != 'passed' or gate['unresolved_findings']
        or gate['human_adjudication'] is not False or digest(report_path) != gate['report_sha256']
        or digest(ROOT/gate['source_review_path']) != gate['source_review_sha256']
        or report['status'] != 'complete' or report['count'] != count or report['matched'] != count
        or report['matching_probes'] != (0 if stage=='confirmation' else 3)
        or report['version'] != contract.VERSION): raise ValueError('Complete source-reviewed gate required')
    return [path, report_path, ROOT/gate['source_review_path']]


def prepare(stage):
    if stage not in ('diagnostic','calibration'): raise ValueError('Full declared stage only')
    step='structured-blind-v2-'+stage; folder=FOLDER/step
    if folder.exists(): raise ValueError('Preserve prior preparation')
    funding=stage_budget(stage); selection=read(FOLDER/'application-selection-v2.json')
    if (selection['status']!='passed' or selection['tasks']!=14 or selection['original_completed']<10
        or selection['original_completed']<selection['completed']['v4'] or selection['recipient_controls_completed']!=2
        or not selection['all_candidate_safety_controls_passed'] or selection['unresolved_selected_candidate_findings']):
        raise ValueError('Application selection required')
    selected=cases(stage); selected_probes=probes(stage); reused=reuse_for(stage,selected)
    paths=[AUTHORIZATION,BASELINE,references.PATH,FOLDER/'application-selection-v2.json']
    paths += [ROOT/p for p in selection['inspection_hashes']]
    if stage=='calibration': paths += require_gate('diagnostic',16)
    paths += list((ROOT/'scripts').glob('*.py'))
    paths += [ROOT/r['raw_path'] for r in reused.values()]
    for p,h in selection['inspection_hashes'].items():
        if digest(ROOT/p)!=h: raise ValueError('Application evidence changed')
    # Frozen original inputs/rubric and all negative controls remain mandatory.
    value=dict(stage=stage,step=step,version=contract.VERSION,prefix=prefix(),funding=funding,
        maximum_calls=4*(len(selected)+len(selected_probes))-len(reused),reuse=reused,
        case_ids=[c['id'] for c in selected],probe_ids=[c['id'] for c in selected_probes],
        total_ceiling_usd=str(CEILING),output_caps=transport.CAPS,provider_retries=0,
        whole_stage_conservative_reservation_usd=str(sum((transport.case_bound(c['inputs'])
            for c in selected+selected_probes),Decimal(0))),
        reservation_policy='rolling full-request reservation; final floor protected',
        bindings={p.relative_to(ROOT).as_posix():digest(p) for p in paths})
    write(folder/'preflight.json',value)
    print(json.dumps({k:v for k,v in value.items() if k not in ('bindings','prefix','reuse')},indent=2))


def validate_plan(step,plan,case_loader,probe_loader):
    stage=plan['stage']
    if stage not in ('diagnostic','calibration','confirmation') or step!='structured-blind-v2-'+stage:
        raise ValueError('Fixed full-stage path required')
    selected,selected_probes=case_loader(stage),probe_loader(stage)
    expected_reuse={} if stage=='confirmation' else reuse_for(stage,selected)
    if (plan['case_ids'] != [c['id'] for c in selected] or plan['probe_ids'] != [c['id'] for c in selected_probes]
        or plan['reuse'] != expected_reuse or plan['maximum_calls'] != 4*(len(selected)+len(selected_probes))-len(expected_reuse)
        or plan['provider_retries'] != 0 or plan['output_caps'] != transport.CAPS
        or plan['total_ceiling_usd'] != str(CEILING) or plan['version'] != contract.VERSION):
        raise ValueError('Coverage, reuse or paid limits changed')


def execute(step,*,case_loader=cases,probe_loader=probes):
    from scripts.conversation_custody import verify_bindings
    folder=FOLDER/step; plan=read(folder/'preflight.json')
    validate_plan(step,plan,case_loader,probe_loader)
    if plan['stage']=='calibration': require_gate('diagnostic',16)
    if plan['funding']!=stage_budget(plan['stage']) or plan['prefix']!=prefix(): raise ValueError('Funding changed')
    if any(digest(ROOT/p)!=h for p,h in plan['bindings'].items()): raise ValueError('Frozen inputs changed')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    verify_bindings(ROOT,commit,{**plan['bindings'],(folder/'preflight.json').relative_to(ROOT).as_posix():digest(folder/'preflight.json')})
    from apps.api.app.core.config import get_settings
    from openai import OpenAI
    settings=get_settings()
    if not settings.openai_api_key: raise ValueError('Existing credential unavailable')
    client=OpenAI(api_key=settings.openai_api_key,max_retries=0,timeout=180.0)
    if str(client.base_url)!='https://api.openai.com/v1/': raise ValueError('Unexpected endpoint')
    out=folder/'run';out.mkdir();ledger=RollingLedger(out,plan)
    manifest=dict(status='running',runtime_commit=commit,started_at=now(),
        preflight_sha256=digest(folder/'preflight.json'),rows={},probes={})
    write(out/'manifest.json',manifest)
    try:
        work=[(c,False) for c in case_loader(plan['stage'])]+[(c,True) for c in probe_loader(plan['stage'])]
        for case,is_probe in work:
            first=second=error=None
            try:
                first,second=transport.grade_case(client.chat.completions.create,case['inputs'],ledger,
                    out/'raw'/case['id'],plan['reuse'].get(case['id']) if not is_probe else None)
            except (ValueError,IndexError) as exc:
                if ledger.data['unknown_outcome']: raise
                error=type(exc).__name__
            row=(probe_result if is_probe else judged)(case,first,second,error)
            path=out/(case['id']+('-probe' if is_probe else '')+'.json');write(path,row)
            manifest['probes' if is_probe else 'rows'][case['id']]=digest(path);write(out/'manifest.json',manifest)
            print(json.dumps(dict(case_id=case['id'],matched=row['matched'],cumulative_usd=str(ledger.accounted))),flush=True)
            if not row['matched']:
                manifest['status']='early_stopped';break
        else: manifest['status']='complete'
    except BaseException as exc:
        manifest.update(status='stopped',exception_type=type(exc).__name__);raise
    finally:
        manifest.update(finished_at=now(),new_spend_usd=str(ledger.accounted-Decimal(plan['prefix']['spent_usd'])),
            cumulative_usd=str(ledger.accounted),ledger_sha256=digest(out/'api-ledger.json'))
        write(out/'manifest.json',manifest)


def report(step,*,case_loader=cases,probe_loader=probes):
    from scripts.conversation_custody import verify_bindings
    out=FOLDER/step/'run';manifest=read(out/'manifest.json');plan=read(out.parent/'preflight.json')
    validate_plan(step,plan,case_loader,probe_loader)
    if digest(out.parent/'preflight.json')!=manifest['preflight_sha256']: raise ValueError('Preflight changed')
    verify_bindings(ROOT,manifest['runtime_commit'],plan['bindings'])
    for p,h in plan['prefix']['ledger_sha256'].items():
        if digest(ROOT/p)!=h: raise ValueError('Spending prefix changed')
    prefix();ledger=read(out/'api-ledger.json')
    if digest(out/'api-ledger.json')!=manifest['ledger_sha256']: raise ValueError('Ledger changed')
    rows=[];reviews=[];bodies={};reused_paths=set()
    for case,is_probe in ([(c,False) for c in case_loader(plan['stage'])]+[(c,True) for c in probe_loader(plan['stage'])]):
        if case['id'] not in manifest['probes' if is_probe else 'rows']: continue
        raw_folder=out/'raw'/case['id'];first=second=error=None
        for name,body in transport.initial_requests(case['inputs']):
            path=raw_folder/(name+'.json')
            if not path.exists(): continue
            rel=path.relative_to(out).as_posix();bodies[rel]=body
            if read(path)['request']!=body: raise ValueError('Saved request changed')
            reused=plan['reuse'].get(case['id']) if not is_probe else None
            if name=='a-coverage' and reused:
                if digest(ROOT/reused['raw_path'])!=reused['raw_sha256'] or read(path)!=read(ROOT/reused['raw_path']):
                    raise ValueError('Reused receipt changed')
                reused_paths.add(rel)
        try: first,second=transport.replay(case['inputs'],raw_folder)
        except (ValueError,IndexError) as exc: error=type(exc).__name__
        row=(probe_result if is_probe else judged)(case,first,second,error)
        path=out/(case['id']+('-probe' if is_probe else '')+'.json')
        if digest(path)!=manifest['probes' if is_probe else 'rows'][case['id']] or read(path)!=row:
            raise ValueError('Judgment replay differs')
        (reviews if is_probe else rows).append(dict(id=case['id'],**row))
    if {c['raw_path'] for c in ledger['calls']} != set(bodies)-reused_paths:
        raise ValueError('Paid/reused receipt inventory differs')
    for call in ledger['calls']:
        body=bodies[call['raw_path']];limits=transport.reserve(body)
        if request_hash(body)!=call['request_sha256'] or any(str(call[k])!=str(v) for k,v in limits.items()):
            raise ValueError('Request reservation changed')
        usage=read(out/call['raw_path'])['response']['usage']
        if usage['prompt_tokens']>limits['input_bound'] or usage['completion_tokens']>limits['output_cap']:
            raise ValueError('Receipt exceeds request bounds')
    cost=sum((Decimal(c['accounted_usd']) for c in ledger['calls']),Decimal(0))
    if (Decimal(manifest['new_spend_usd'])!=cost
        or Decimal(manifest['cumulative_usd'])!=Decimal(plan['prefix']['spent_usd'])+cost):
        raise ValueError('Reported spending differs from receipts')
    result=dict(status=manifest['status'],version=contract.VERSION,count=len(rows),matched=sum(r['matched'] for r in rows),
        matching_probes=sum(r['matched'] for r in reviews),calls=len(ledger['calls']),reused_components=len(reused_paths),
        cost_usd=manifest['new_spend_usd'],cumulative_usd=manifest['cumulative_usd'],rows=rows,probes=reviews,
        source_review_pending=True)
    write(out.parent/'report.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','probes')},indent=2))


if __name__=='__main__':
    if sys.argv[1]=='prepare': prepare(sys.argv[2])
    elif sys.argv[1]=='run': execute(sys.argv[2])
    elif sys.argv[1]=='report': report(sys.argv[2])
    else: raise SystemExit('Use prepare, run or report')
