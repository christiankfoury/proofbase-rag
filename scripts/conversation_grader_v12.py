"""V35 one-shot qualification under the replacement USD7.60 balance."""
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.conversation_v35_budget import FOLDER, CEILING, FINAL_FLOOR, prefix, AUTHORIZATION, stage_budget
from scripts.bounded_redesign_run import read,digest,write,now,response_charge
from scripts.phase73_v6_budget import request_hash
from scripts import quality_eval_contract_v35 as contract
from scripts import quality_eval_transport_v35 as transport
from scripts import quality_development_v23 as existing
from scripts import conversation_ordering_v2 as references


class RollingLedger:
    def __init__(self,folder,plan):
        self.folder=Path(folder);self.plan=plan
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


def versioned(version):
    if version==contract.VERSION:return contract,transport
    raise ValueError('Unfrozen grader version')


def prepare(step,stage,ids=None):
    contract,transport=versioned('answer-dimensions.v35-candidate')
    if stage not in ('diagnostic','calibration') or ids:raise ValueError('Only complete one-shot qualification stages allowed')
    if step != 'grader-v35-' + stage:raise ValueError('Fixed one-shot stage path required')
    funding = stage_budget(stage)
    folder=FOLDER/step
    if folder.exists():raise ValueError('Preserve prior preparation')
    selection=read(FOLDER/'application-selection-v2.json')
    selected=selection['completed'][selection['profile']]
    if (selection['status']!='passed' or selection['tasks']!=14 or selection['original_completed']<10
            or selection['original_completed']<selection['completed']['v4'] or selection['recipient_controls_completed']!=2 or not selection['all_candidate_safety_controls_passed']
            or selection['unresolved_selected_candidate_findings']):raise ValueError('Application gate required')
    for path,h in selection['inspection_hashes'].items():
        if digest(ROOT/path)!=h:raise ValueError('Application inspection changed')
    paths=[AUTHORIZATION,FOLDER/'authorization.json',FOLDER/'rolling-authorization.json',FOLDER/'application-selection-v2.json',existing.CONTROLS,
        existing.old_development.baseline.SUITE,existing.old_development.baseline.AUDITS,existing.old_development.baseline.VALIDATION]
    paths += [ROOT/p for p in selection['inspection_hashes']]
    if stage=='calibration' and not ids:
        gate=FOLDER/'grader-v35-diagnostic-acceptance.json';value=read(gate)
        report_path=ROOT/value['report_path']
        if value['status']!='passed' or value['unresolved_findings'] or digest(report_path)!=value['report_sha256']:
            raise ValueError('Source-reviewed diagnostic required')
        if value['human_adjudication'] is not False or digest(ROOT/value['source_review_path']) != value['source_review_sha256']:
            raise ValueError('Diagnostic source inspection changed')
        report=read(report_path)
        if report['matched']!=16 or report['matching_probes']!=3 or report['status']!='complete' or report['version']!=contract.VERSION:raise ValueError('Diagnostic incomplete or stale version')
        paths.extend([gate,report_path,ROOT/value['source_review_path']])
    paths += [FOLDER/'grader-v26-scenario-controls.json',FOLDER/'grader-v32-interpretation-controls.json']
    paths += [references.PATH]
    paths+=list((ROOT/'scripts').glob('*.py'))
    selected=[c for c in cases(stage) if not ids or c['id'] in ids]
    selected_probes=[c for c in probes(stage) if not ids or c['id'] in ids]
    if ids and (len(ids)!=len(set(ids)) or len(selected)+len(selected_probes)!=len(ids)):raise ValueError('Invalid focus')
    bound=sum((transport.case_bound(c['inputs']) for c in selected),Decimal(0))
    bound+=sum((transport.reserve(transport.review_request(c['inputs'],c['candidate']))['reserved_usd'] for c in selected_probes),Decimal(0))
    value=dict(stage=stage,step=step,version=contract.VERSION,prefix=prefix(),funding=funding,maximum_calls=len(selected)*3+len(selected_probes),
        case_ids=[c['id'] for c in selected],probe_ids=[c['id'] for c in selected_probes],
        whole_stage_conservative_reservation_usd=str(bound),reservation_policy='rolling per-request; not whole-stage funded',
        total_ceiling_usd=str(CEILING),output_caps=transport.CAPS,provider_retries=0,
        bindings={p.relative_to(ROOT).as_posix():digest(p) for p in paths})
    write(folder/'preflight.json',value)
    print(json.dumps({k:v for k,v in value.items() if k not in ('bindings','prefix')},indent=2))


def execute(step,*,case_loader=cases,probe_loader=probes):
    folder=FOLDER/step;plan=read(folder/'preflight.json')
    contract,transport=versioned(plan['version'])
    validate_plan(step, plan, case_loader, probe_loader)
    if stage_budget(plan['stage']) != plan['funding']:raise ValueError('Whole-path funding changed')
    if plan['prefix']!=prefix() or any(digest(ROOT/p)!=h for p,h in plan['bindings'].items()):raise ValueError('Frozen inputs changed')
    from scripts.conversation_custody import verify_bindings
    verify_bindings(ROOT,subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),plan['bindings'])
    from apps.api.app.core.config import get_settings
    from openai import OpenAI
    settings=get_settings()
    if not settings.openai_api_key:raise ValueError('Existing credential unavailable')
    client=OpenAI(api_key=settings.openai_api_key,max_retries=0,timeout=180.0)
    if str(client.base_url)!='https://api.openai.com/v1/':raise ValueError('Unexpected endpoint')
    out=folder/'run';out.mkdir();ledger=RollingLedger(out,plan)
    manifest=dict(status='running',runtime_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        started_at=now(),preflight_sha256=digest(folder/'preflight.json'),rows={},probes={})
    write(out/'manifest.json',manifest)
    try:
        for case in [c for c in case_loader(plan['stage']) if c['id'] in plan['case_ids']]:
            grade=review=error=None
            try:grade,review=transport.grade_case(client.chat.completions.create,case['inputs'],ledger,out/'raw'/case['id'])
            except (ValueError,IndexError) as exc:
                if ledger.data['unknown_outcome']:raise
                error=type(exc).__name__
            row=references.judged(case,grade,review,error);path=out/(case['id']+'.json');write(path,row)
            manifest['rows'][case['id']]=digest(path);write(out/'manifest.json',manifest)
            print(json.dumps(dict(case_id=case['id'],matched=row['matched'],cumulative_usd=str(ledger.accounted))),flush=True)
            if not row['matched']:
                manifest['status']='early_stopped';break
        else:
            for case in [c for c in probe_loader(plan['stage']) if c['id'] in plan['probe_ids']]:
                review=error=None;body=transport.review_request(case['inputs'],case['candidate'])
                try:review=transport.parsed(ledger.call(client.chat.completions.create,body,out/'raw'/(case['id']+'.json')),contract.review_schema())
                except (ValueError,IndexError) as exc:
                    if ledger.data['unknown_outcome']:raise
                    error=type(exc).__name__
                path=out/(case['id']+'-probe.json');write(path,existing.probe_result(case,review,error))
                manifest['probes'][case['id']]=digest(path);write(out/'manifest.json',manifest)
            manifest['status']='complete'
    except BaseException as exc:
        manifest.update(status='stopped',exception_type=type(exc).__name__);raise
    finally:
        manifest.update(finished_at=now(),new_spend_usd=str(ledger.accounted-Decimal(plan['prefix']['spent_usd'])),cumulative_usd=str(ledger.accounted),ledger_sha256=digest(out/'api-ledger.json'))
        write(out/'manifest.json',manifest)


def validate_plan(step, plan, case_loader, probe_loader):
    if plan['stage'] not in ('diagnostic','calibration','confirmation') or step != 'grader-v35-' + plan['stage']:
        raise ValueError('One complete declared stage only')
    case_ids = [c['id'] for c in case_loader(plan['stage'])]
    probe_ids = [c['id'] for c in probe_loader(plan['stage'])]
    if (plan['case_ids'] != case_ids or plan['probe_ids'] != probe_ids
            or plan['maximum_calls'] != 3 * len(case_ids) + len(probe_ids)
            or plan['provider_retries'] != 0 or plan['output_caps'] != transport.CAPS
            or plan['total_ceiling_usd'] != str(CEILING)):
        raise ValueError('Stage coverage or paid limits changed')


def report(step,*,case_loader=cases,probe_loader=probes):
    from scripts.report_quality_calibration_v12 import replay_raw
    from scripts.conversation_custody import verify_bindings
    out=FOLDER/step/'run';manifest=read(out/'manifest.json');plan=read(out.parent/'preflight.json')
    contract,transport=versioned(plan['version'])
    if digest(out.parent/'preflight.json')!=manifest['preflight_sha256']:raise ValueError('Preflight changed')
    verify_bindings(ROOT,manifest['runtime_commit'],plan['bindings'])
    for path,h in plan['prefix']['ledger_sha256'].items():
        if digest(ROOT/path)!=h:raise ValueError('Spending prefix changed')
    prefix() # Full cache-aware receipt replay, no silent unknown outcome.
    ledger=read(out/'api-ledger.json')
    if digest(out/'api-ledger.json')!=manifest['ledger_sha256']:raise ValueError('Ledger changed')
    rows=[];reviews=[];bodies={}
    for case in case_loader(plan['stage']):
        if case['id'] not in manifest['rows']:continue
        grade=review=error=None
        try:
            parts={}
            for purpose,body in transport.initial_requests(case['inputs']):
                path=out/'raw'/case['id']/(purpose+'.json');bodies[path.relative_to(out).as_posix()]=body
                parts.update(replay_raw(path,body))
            body=transport.review_request(case['inputs'],parts);path=out/'raw'/case['id']/'review.json';bodies[path.relative_to(out).as_posix()]=body
            review=replay_raw(path,body);grade=parts
        except (ValueError,IndexError) as exc:error=type(exc).__name__
        row=references.judged(case,grade,review,error);path=out/(case['id']+'.json')
        if digest(path)!=manifest['rows'][case['id']] or read(path)!=row:raise ValueError('Judgment changed')
        rows.append(dict(id=case['id'],**row))
    for case in probe_loader(plan['stage']):
        if case['id'] not in manifest['probes']:continue
        body=transport.review_request(case['inputs'],case['candidate']);path=out/'raw'/(case['id']+'.json');bodies[path.relative_to(out).as_posix()]=body
        review=error=None
        try:review=replay_raw(path,body)
        except (ValueError,IndexError) as exc:error=type(exc).__name__
        row=existing.probe_result(case,review,error);path=out/(case['id']+'-probe.json')
        if digest(path)!=manifest['probes'][case['id']] or read(path)!=row:raise ValueError('Probe changed')
        reviews.append(dict(id=case['id'],**row))
    for row in ledger['calls']:
        body=bodies[row['raw_path']]
        if read(out/row['raw_path'])['request']!=body or row['request_sha256']!=request_hash(body):raise ValueError('Request changed')
        limits=transport.reserve(body)
        if any(str(row[k])!=str(v) for k,v in limits.items()):raise ValueError('Reservation changed')
    result=dict(status=manifest['status'],version=contract.VERSION,count=len(rows),matched=sum(r['matched'] for r in rows),
        matching_probes=sum(r['matched'] for r in reviews),calls=len(ledger['calls']),cost_usd=manifest['new_spend_usd'],
        cumulative_usd=manifest['cumulative_usd'],rows=rows,probes=reviews,source_review_pending=True)
    write(out.parent/'report.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','probes')},indent=2))


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(sys.argv[2],sys.argv[3],sys.argv[4:])
    elif sys.argv[1]=='run':execute(sys.argv[2])
    elif sys.argv[1]=='report':report(sys.argv[2])
    else:raise SystemExit('Choose prepare, run or report')
