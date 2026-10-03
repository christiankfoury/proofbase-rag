"""Windows-safe successor: identical measurement with batched committed-file custody."""
from contextlib import contextmanager
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import conversation_grader_v4 as grading
from scripts import conversation_environment as environment
from scripts.conversation_custody import verify_bindings
from scripts.bounded_redesign_run import read,write,digest,now,response_charge,request_hash
from scripts.current_eval_protocol import validate_suite,COUNTS
from scripts.phase73_v6_protocol import validate_gold_scope
from scripts.phase73_v6_capture import measure_case
from scripts.quality_inputs_v23 import build_inputs

FOLDER=grading.FOLDER/'final-v2'
BRIEFS=[ROOT/'docs/phase-73/conversation-final-v2-authoring-contract.md',ROOT/'docs/phase-73/conversation-final-v2-validation-contract.md']
APP_MODELS={'gpt-4.1-mini-2025-04-14':(Decimal('.4'),Decimal('1.6')),'gpt-5.4-2026-03-05':(Decimal('2.5'),Decimal('15'))}
APP_CALLS=32


def readiness():
    from scripts import conversation_confirmation_v4 as confirmation
    confirmation.custody()
    gate=grading.FOLDER/'grader-v28-confirmation-acceptance.json';value=read(gate)
    path=ROOT/value['report_path'];report=read(path)
    if (value['status']!='passed' or value['unresolved_findings'] or value['human_adjudication'] is not False
        or report['status']!='complete' or report['count']!=16 or report['matched']!=16
        or report['version']!=value['version'] or digest(path)!=value['report_sha256']
        or digest(ROOT/value['source_review_path'])!=value['source_review_sha256']):
        raise ValueError('Complete source-reviewed confirmation required')
    return value,digest(gate)


def freeze():
    if (FOLDER/'freeze.json').exists():raise ValueError('Preserve existing runtime freeze')
    ready,h=readiness();settings=environment.configure()
    files=list((ROOT/'apps/api/app').rglob('*.py'))+list((ROOT/'apps/api/app/prompts/versions').glob('*.md'))
    files+=list((ROOT/'scripts').glob('*.py'))+list((ROOT/'data/synthetic-documents').rglob('*.md'))
    files+=BRIEFS+[ROOT/'requirements.txt',grading.FOLDER/'application-selection-v2.json',grading.FOLDER/'grader-v28-confirmation-acceptance.json',grading.FOLDER/'rolling-authorization.json']
    verify_bindings(ROOT,subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        {p.relative_to(ROOT).as_posix():digest(p) for p in files})
    write(FOLDER/'freeze.json',dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),created_at=now(),
        grader_version=ready['version'],readiness_sha256=h,environment=environment.fingerprint(settings),
        bindings={p.relative_to(ROOT).as_posix():digest(p) for p in files}))


def custody(require_seal=True,require_current=True):
    _,ready=readiness();frozen=read(FOLDER/'freeze.json')
    if ready!=frozen['readiness_sha256']:raise ValueError('Qualification changed')
    if require_current and any(digest(ROOT/p)!=h for p,h in frozen['bindings'].items()):raise ValueError('Frozen runtime changed')
    verify_bindings(ROOT,frozen['commit'],frozen['bindings'])
    suite=read(FOLDER/'holdout.json');validation=read(FOLDER/'author-validation.json');cases=suite['cases']
    errors=validate_suite(suite)
    if errors or {c['case_id'] for c in cases}!={f'fresh-{i:03}' for i in range(1,61)}:raise ValueError(str(errors) or 'Case IDs changed')
    if (suite['authored_after_freeze']!=frozen['commit'] or validation['status']!='approved'
        or validation['human_adjudication'] is not False or validation['case_count']!=60 or validation['unresolved_findings']
        or validation['suite_sha256']!=digest(FOLDER/'holdout.json') or validation['freeze_sha256']!=digest(FOLDER/'freeze.json')):
        raise ValueError('Independent validation missing')
    reviews=validation['case_reviews']
    if (len(reviews)!=60 or {r['case_id']:r['expected_behavior'] for r in reviews}!={c['case_id']:c['expected_behavior'] for c in cases}
        or any(not r['accept'] or not r['reference_scope_reviewed'] or not r['reference_scope_reason'].strip() for r in reviews)):
        raise ValueError('Independent reference review incomplete')
    overlap=read(FOLDER/'overlap.json')
    if overlap['hits']:raise ValueError('Unresolved historical overlap')
    for case in cases:build_inputs(case,dict(raw_response={},authorized_evidence=[]))
    validate_gold_scope(suite,frozen['environment'])
    files={p.relative_to(ROOT).as_posix():digest(p) for p in [FOLDER/n for n in ('freeze.json','holdout.json','author-validation.json','overlap.json')]}
    if require_seal and read(FOLDER/'seal.json')['bindings']!=files:raise ValueError('Holdout seal changed')
    return frozen,suite,files


def overlap():
    from scripts.check_phase73_v6_overlap import questions,tokens
    old=[]
    for path in (ROOT/'data/evaluation').rglob('*.json'):
        if path.is_relative_to(FOLDER) or 'local-runs' in path.parts:continue
        try:old.extend(frozenset(tokens(q)) for q in questions(read(path)))
        except (ValueError,UnicodeError):continue
    old=[set(t) for t in set(old) if t];hits=[]
    for case in read(FOLDER/'holdout.json')['cases']:
        current=tokens(case['question']);score=max((len(current&p)/len(current|p) for p in old),default=0)
        if score>=.8:hits.append(dict(case_id=case['case_id'],max_token_jaccard=score))
    write(FOLDER/'overlap.json',dict(historical_unique_questions=len(old),threshold=.8,hits=hits,limitation='Lexical check cannot establish semantic independence'))
    print(json.dumps(dict(hits=hits,historical_unique_questions=len(old))))


def seal():
    if (FOLDER/'seal.json').exists():raise ValueError('Preserve existing seal')
    _,_,files=custody(False);write(FOLDER/'seal.json',dict(created_at=now(),bindings=files))


class MeasurementLedger(grading.RollingLedger):
    def __init__(self,folder,plan):
        self.mode='grading';self.case_id=None;self.case_calls={}
        super().__init__(folder,plan)

    def begin_case(self,cid):
        if cid in self.case_calls or cid not in self.plan['case_ids']:raise ValueError('No repeated or unsealed case')
        self.case_id=cid;self.case_calls[cid]={'application':0,'grading':0}

    def prepare_request(self,body):
        if not self.case_id:raise grading.transport.BudgetStop('No active case')
        maximum=APP_CALLS if self.mode=='application' else 3
        if self.case_calls[self.case_id][self.mode]>=maximum:raise grading.transport.BudgetStop('Case call allowance reached')
        if self.mode=='grading':return super().prepare_request(body)
        body=dict(body)
        if body.get('model')=='gpt-4.1-mini':body['model']='gpt-4.1-mini-2025-04-14'
        model=body.get('model')
        if body.get('stream') or body.get('tools') or body.get('functions') or body.get('n',1)!=1:
            raise grading.transport.BudgetStop('Unbounded application operation')
        if model=='text-embedding-3-small':
            if 'input' not in body:raise grading.transport.BudgetStop('Missing embedding input')
            cap=0;ri=Decimal('.02');ro=Decimal(0)
        else:
            if model not in APP_MODELS:raise grading.transport.BudgetStop('Unpriced application model')
            body.setdefault('max_completion_tokens',2048);body['service_tier']='default'
            cap=body['max_completion_tokens'];ri,ro=APP_MODELS[model]
            if type(cap)!=int or not 0<cap<=2048:raise grading.transport.BudgetStop('Application output allowance exceeded')
            if model=='gpt-5.4-2026-03-05' and body.get('reasoning_effort')!='low':raise grading.transport.BudgetStop('Unfrozen candidate profile')
        bound=len(json.dumps(body,ensure_ascii=False).encode('utf-8'))+2048
        if bound>131072:raise grading.transport.BudgetStop('Application input allowance exceeded')
        return body,dict(input_bound=bound,output_cap=cap,reserved_usd=(bound*ri+cap*ro)/1000000)

    def call(self,create,body,path):
        if (self.folder.parent/'stop-request.json').exists():
            self.data.update(stopped=True,stop_reason='Operator requested stop before submission');self.save()
            raise grading.transport.BudgetStop('Operator requested stop before submission')
        try:
            response=super().call(create,body,path)
            self.case_calls[self.case_id][self.mode]+=1
            return response
        except grading.transport.BudgetStop:
            self.data.update(stopped=True,budget_exhausted=True);self.save();raise

    @contextmanager
    def intercept(self):
        from openai import OpenAI
        from openai.resources.chat.completions import Completions
        from openai.resources.embeddings import Embeddings
        original_chat,original_embedding,init=Completions.create,Embeddings.create,OpenAI.__init__
        self.mode='application'
        def initialize(client,*args,**kwargs):
            kwargs.update(max_retries=0,timeout=180.0);return init(client,*args,**kwargs)
        def submit(original,resource,args,body):
            if args or str(resource._client.base_url)!='https://api.openai.com/v1/':raise grading.transport.BudgetStop('Unexpected endpoint')
            resource._client.max_retries=0
            path=self.folder/'raw/application'/self.case_id/f"call-{len(self.data['calls']):04}.json"
            return self.call(lambda **kw:original(resource,**kw),body,path)
        try:
            with patch.object(OpenAI,'__init__',initialize),patch.object(Completions,'create',lambda resource,*a,**b:submit(original_chat,resource,a,b)),patch.object(Embeddings,'create',lambda resource,*a,**b:submit(original_embedding,resource,a,b)):
                yield
        finally:self.mode='grading'


def prepare():
    frozen,suite,files=custody();settings=environment.configure()
    if environment.fingerprint(settings)!=frozen['environment']:raise ValueError('Frozen index/configuration changed')
    spending=grading.prefix()
    if grading.CEILING-Decimal(spending['spent_usd'])<Decimal('4.50'):raise grading.transport.BudgetStop('Final launch floor unavailable')
    path=FOLDER/'preflight.json'
    if path.exists():raise ValueError('Preserve existing final preflight')
    write(path,dict(stage='final',version=frozen['grader_version'],prefix=spending,maximum_calls=60*(APP_CALLS+3),
        case_ids=[c['case_id'] for c in suite['cases']],application_calls_per_case=APP_CALLS,grader_calls_per_case=3,
        total_ceiling_usd=str(grading.CEILING),reservation_policy='rolling complete-request reservations',provider_retries=0,
        application_input_cap=131072,application_output_cap=2048,grader_output_caps=grading.transport.CAPS,
        bindings={**frozen['bindings'],**files,(FOLDER/'seal.json').relative_to(ROOT).as_posix():digest(FOLDER/'seal.json')}))


def run():
    frozen,suite,_=custody();settings=environment.configure();plan=read(FOLDER/'preflight.json')
    if plan['prefix']!=grading.prefix() or environment.fingerprint(settings)!=frozen['environment']:raise ValueError('Frozen execution inputs changed')
    if grading.CEILING-Decimal(plan['prefix']['spent_usd'])<Decimal('4.50'):raise grading.transport.BudgetStop('Launch floor unavailable')
    verify_bindings(ROOT,subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),plan['bindings'])
    from fastapi.testclient import TestClient
    from apps.api.app.main import app
    from openai import OpenAI
    contract,transport=grading.versioned(plan['version'])
    grader=OpenAI(api_key=settings.openai_api_key,max_retries=0,timeout=180.0)
    if str(grader.base_url)!='https://api.openai.com/v1/':raise ValueError('Unexpected grader endpoint')
    out=FOLDER/'run';out.mkdir();ledger=MeasurementLedger(out,plan)
    manifest=dict(status='running',runtime_commit=frozen['commit'],expected_cases=60,rows={},started_at=now(),preflight_sha256=digest(FOLDER/'preflight.json'))
    write(out/'manifest.json',manifest)
    try:
        with TestClient(app) as client:
            for case in suite['cases']:
                ledger.begin_case(case['case_id']);path=out/(case['case_id']+'.json')
                with ledger.intercept():row=measure_case(client,settings,case,path,ledger)
                if ledger.data['stopped']:raise grading.transport.BudgetStop('Application transport stopped')
                if set(row['safety_flags'])-{'http_error'}:raise ValueError('Observed permission/scope failure')
                inputs=build_inputs(case,row);row['grader_inputs']=inputs;write(path,row)
                grade=review=error=None
                try:grade,review=transport.grade_case(grader.chat.completions.create,inputs,ledger,out/'raw/grader'/case['case_id'])
                except (ValueError,IndexError) as exc:
                    if ledger.data['unknown_outcome']:raise
                    error=type(exc).__name__
                dims=contract.dimensions(inputs,grade,row['raw_response'],row['authorized_evidence'],row['safety_flags'],review)
                row.update(grade=grade,review=review,grading_error=error,dimensions=dims,status='complete',grading_completed_at=now(),call_end=len(ledger.data['calls']))
                write(path,row);manifest['rows'][case['case_id']]=digest(path);write(out/'manifest.json',manifest)
                print(json.dumps(dict(case_id=case['case_id'],overall=dims['overall'],cumulative_usd=str(ledger.accounted))),flush=True)
                if dims['unmatched_citations'] or (case['category'] in {'permissions','uploaded_document_isolation'} and dims['forbidden_assertion']=='present'):
                    raise ValueError('Observed citation/disclosure failure')
        manifest['status']='complete'
    except BaseException as exc:
        manifest.update(status='stopped',exception_type=type(exc).__name__);raise
    finally:
        manifest.update(finished_at=now(),cumulative_usd=str(ledger.accounted),new_spend_usd=str(ledger.accounted-Decimal(plan['prefix']['spent_usd'])),ledger_sha256=digest(out/'api-ledger.json'))
        write(out/'manifest.json',manifest)


def report():
    from scripts.report_quality_calibration_v12 import replay_raw
    import statistics
    frozen,suite,_=custody(require_current=False);out=FOLDER/'run'
    manifest=read(out/'manifest.json');plan=read(FOLDER/'preflight.json');ledger=read(out/'api-ledger.json')
    if digest(FOLDER/'preflight.json')!=manifest['preflight_sha256'] or digest(out/'api-ledger.json')!=manifest['ledger_sha256']:
        raise ValueError('Run custody changed')
    spending=grading.prefix()
    for path,h in plan['prefix']['ledger_sha256'].items():
        if digest(ROOT/path)!=h:raise ValueError('Prefix changed')
    contract,transport=grading.versioned(plan['version']);rows=[];expected_requests={}
    for case in suite['cases']:
        cid=case['case_id']
        if cid not in manifest['rows']:continue
        path=out/(cid+'.json');row=read(path)
        if digest(path)!=manifest['rows'][cid]:raise ValueError('Captured answer changed')
        inputs=build_inputs(case,row)
        if inputs!=row['grader_inputs']:raise ValueError('Grader inputs changed')
        grade=review=error=None
        try:
            parts={}
            for purpose,body in transport.initial_requests(inputs):
                path=out/'raw/grader'/cid/(purpose+'.json');expected_requests[path.relative_to(out).as_posix()]=body
                parts.update(replay_raw(path,body))
            body=transport.review_request(inputs,parts);path=out/'raw/grader'/cid/'review.json';expected_requests[path.relative_to(out).as_posix()]=body
            review=replay_raw(path,body);grade=parts
        except (ValueError,IndexError) as exc:error=type(exc).__name__
        dims=contract.dimensions(inputs,grade,row['raw_response'],row['authorized_evidence'],row['safety_flags'],review)
        if dims!=row['dimensions'] or grade!=row['grade'] or review!=row['review'] or error!=row['grading_error']:
            raise ValueError('Grading replay differs')
        rows.append(dict(case_id=cid,category=case['category'],expected_behavior=case['expected_behavior'],http_status=row['http_status'],
            latency_ms=row['latency_ms'],**dims))
    for case in suite['cases']:
        cid=case['case_id']
        if cid in manifest['rows']:continue
        path=out/(cid+'.json')
        if not path.exists():continue
        row=read(path)
        if 'grader_inputs' not in row:continue
        inputs=build_inputs(case,row)
        if inputs!=row['grader_inputs']:raise ValueError('Partial grader inputs changed')
        parts={}
        for purpose,body in transport.initial_requests(inputs):
            raw=out/'raw/grader'/cid/(purpose+'.json')
            if raw.exists():
                expected_requests[raw.relative_to(out).as_posix()]=body
                try:parts.update(replay_raw(raw,body))
                except (ValueError,IndexError):pass
        raw=out/'raw/grader'/cid/'review.json'
        if raw.exists():expected_requests[raw.relative_to(out).as_posix()]=transport.review_request(inputs,parts)
    amount=Decimal(0);counts={}
    for call in ledger['calls']:
        path=call['raw_path'];raw=read(out/path);body=raw['request'];is_app=path.startswith('raw/application/')
        cid=path.split('/')[2]
        if cid not in plan['case_ids']:raise ValueError('Undeclared case call')
        key=(cid,is_app);counts[key]=counts.get(key,0)+1
        if counts[key]>(APP_CALLS if is_app else 3):raise ValueError('Case call allowance exceeded')
        if is_app:
            probe=MeasurementLedger.__new__(MeasurementLedger);probe.mode='application';probe.case_id=cid;probe.case_calls={cid:{'application':0}}
            canonical,limits=probe.prepare_request(body)
            if canonical!=body:raise ValueError('Application request was not canonical')
        else:
            if expected_requests.get(path)!=body:raise ValueError('Grader request changed')
            limits=transport.reserve(body)
        if request_hash(body)!=call['request_sha256'] or any(str(call[k])!=str(v) for k,v in limits.items()):raise ValueError('Reservation changed')
        usage=raw['response']['usage'];cost=response_charge(raw['response'],body['model'])
        if cost>Decimal(call['reserved_usd']) or usage['prompt_tokens']>limits['input_bound'] or usage.get('completion_tokens',0)>limits['output_cap']:
            raise ValueError('Receipt exceeds bounds')
        amount+=cost
    if amount!=Decimal(manifest['new_spend_usd']) or amount+Decimal(plan['prefix']['spent_usd'])!=Decimal(manifest['cumulative_usd']):raise ValueError('Cost total differs')
    complete=manifest['status']=='complete' and len(rows)==60
    passed=sum(r['target_credit'] for r in rows)
    unsafe=[r['case_id'] for r in rows if set(r['recorded_safety_flags'])-{'http_error'} or r['unmatched_citations'] or (r['category'] in {'permissions','uploaded_document_isolation'} and r['forbidden_assertion']=='present')]
    latency=sorted(r['latency_ms'] for r in rows)
    groups={k:dict(passed=sum(r['target_credit'] for r in rows if r['category']==k),total=n) for k,n in COUNTS.items()}
    answer_ids={c['case_id'] for c in suite['cases'] if c['expected_behavior']=='answer'}
    result=dict(status='complete' if complete else 'incomplete',expected_cases=60,completed_cases=len(rows),passed=passed,
        unresolved_or_unexecuted=60-len(rows)+sum(r['overall']=='unresolved' for r in rows),categories=groups,
        answer_expected=dict(passed=sum(r['target_credit'] for r in rows if r['case_id'] in answer_ids),total=len(answer_ids)),
        quotation_fidelity={s:sum(r['quotation_fidelity']==s for r in rows) for s in ('pass','fail','not_applicable')},
        latency_ms=dict(median=statistics.median(latency) if latency else None,p95=latency[min(len(latency)-1,int(len(latency)*.95))] if latency else None),
        observed_safety_failures=unsafe,measurement_gate_passed=complete and passed>=48 and not unsafe,
        source_inspection_pending=True,activation_allowed=False,rows=rows,calls=len(ledger['calls']),
        new_spend_usd=str(amount),cumulative_spend_usd=spending['spent_usd'],remaining_usd=str(grading.CEILING-Decimal(spending['spent_usd'])),
        limitation='Agent-authored synthetic suite; automated grading and separate agent source inspection, not human validation or population accuracy.')
    write(FOLDER/'report.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


if __name__=='__main__':
    action=sys.argv[1]
    if action=='freeze':freeze()
    elif action=='overlap':overlap()
    elif action=='seal':seal()
    elif action=='prepare':prepare()
    elif action=='run':run()
    elif action=='report':report()
    else:raise SystemExit('Use freeze, overlap, seal, prepare or run')
