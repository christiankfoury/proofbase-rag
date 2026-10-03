"""Bounded application iterations; historical attempts and receipts are immutable."""
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.bounded_redesign_run import Ledger as ApplicationLedger, read, digest, now, write, response_charge
from scripts.bounded_redesign_preflight import FOLDER as PREVIOUS, PROFILES, prepare as prepare_body, configure, c

FOLDER=ROOT/'data/evaluation/conversation-continuation'
CEILING=Decimal('12.50')
ORIGINAL=PREVIOUS/'cad20-comparison/api-ledger.json'
SUITE=FOLDER/'development-v2.json'


def prefix():
    if digest(ORIGINAL)!=read(FOLDER/'authorization.json')['prior_ledger_sha256']:
        raise ValueError('Authorized initial ledger changed')
    paths=[ORIGINAL]+sorted(FOLDER.glob('*/run/api-ledger.json'))
    total=Decimal(0);files={}
    for path in paths:
        ledger=read(path)
        if ledger['unknown_outcome'] or any(r['status']!='completed' for r in ledger['calls']):
            raise ValueError('Unsettled prior call; no continuation')
        for row in ledger['calls']:
            raw_path=path.parent/row['raw_path'];raw=read(raw_path)
            if digest(raw_path)!=row['raw_sha256'] or raw['status']!='received':raise ValueError('Historical receipt changed')
            amount=response_charge(raw['response'],raw['request']['model'])
            if amount!=Decimal(row['accounted_usd']):raise ValueError('Historical cost differs')
            total+=amount
        files[path.relative_to(ROOT).as_posix()]=digest(path)
    if total>CEILING:raise ValueError('Budget already exceeded')
    return dict(spent_usd=str(total),ledger_sha256=files)


class Ledger(ApplicationLedger):
    def __init__(self, folder, plan):
        self.prefix=plan['prefix']
        self.allowed={(plan['profile'],row['case_id'],row['turn']) for row in plan['turns']}
        super().__init__(folder,dict(total_ceiling_usd=str(CEILING),stage_caps_usd=dict(application=str(CEILING))),plan)
        self.data['prefix']=self.prefix;self.save()

    @property
    def accounted(self):return Decimal(self.prefix['spent_usd'])+super().accounted

    def begin(self,profile,case_id,turn):
        if (profile,case_id,turn) not in self.allowed:self.stop('Undeclared task/turn')
        super().begin(profile,case_id,turn)


def prepare(step,profile,ids):
    if profile not in PROFILES or not step.replace('-','').isalnum():raise ValueError('Invalid experiment identity')
    folder=FOLDER/step
    if folder.exists():raise ValueError('Preserve existing preparation and run')
    suite=read(SUITE);selected=[x for x in suite['cases'] if x['id'] in ids]
    if len(selected)!=len(set(ids)) or not selected:raise ValueError('Unknown or duplicate tasks')
    old=read(PREVIOUS/'preflight-complete.json');samples=[]
    # Reuse complete prepared payloads; replace only the revised prompts/schema.
    # Dynamic output/history headroom and every output allowance remain unchanged.
    for item in old['prepared_payloads']:
        if item['profile']!=profile:continue
        body=item['request'];stage=item['stage']
        if stage in {'conversational_producer','conversational_checker'}:
            payload=json.loads(body['messages'][1]['content'])
            for source in payload['authorized_sources']:
                source['content']=next(s['content'] for s in suite['sources'] if s['chunk_id']==source['chunk_id'])
            body=c.request_body(stage.split('_')[1],payload,body['model'])
        body,bound=prepare_body(body);samples.append(dict(stage=stage,body=body,**bound))
    turns=[dict(case_id=x['id'],turn=i) for x in selected for i in range(len(x['turns']))]
    bounds=[];amount=Decimal(0)
    for stage in sorted({x['stage'] for x in samples}):
        maximum=max((s for s in samples if s['stage']==stage),key=lambda x:Decimal(x['reserved_usd']))
        extra=maximum['input_bound']+2048
        if extra>16384:raise ValueError('Dynamic input bound exceeded')
        ri,_,ro=map(Decimal,c.PRICES[maximum['body']['model']])
        each=(extra*ri+maximum['output_cap']*ro)/1000000
        per_turn=2 if profile=='v4' and stage in {'generated_answer_v1','post_generation_validation_v1'} else 1
        amount+=each*len(turns)*per_turn
        bounds.append(dict(stage=stage,count=15*per_turn,input_bound=extra,output_cap=maximum['output_cap'],model=maximum['body']['model']))
    spending=prefix()
    files=list((ROOT/'apps/api/app').rglob('*.py'))+list((ROOT/'apps/api/app/prompts/versions').glob('*.md'))+list((ROOT/'scripts').glob('*.py'))
    files+=[ROOT/'requirements.txt',PREVIOUS/'development.json',SUITE,FOLDER/'authorization.json']
    plan=dict(step=step,profile=profile,suite_path=SUITE.relative_to(ROOT).as_posix(),case_ids=ids,turns=turns,bounds={profile:bounds},prefix=spending,
        total_ceiling_usd=str(CEILING),whole_stage_reservation_usd=str(amount),provider_retries=0,
        status='ready' if Decimal(spending['spent_usd'])+amount<=CEILING else 'budget_stop',
        bindings={p.relative_to(ROOT).as_posix():digest(p) for p in files})
    write(folder/'preflight.json',plan)
    print(json.dumps({k:v for k,v in plan.items() if k not in {'bindings','bounds','turns'}},indent=2))


def run(step):
    plan=read(FOLDER/step/'preflight.json')
    if plan['status']!='ready' or prefix()!=plan['prefix']:raise ValueError('Budget or prefix changed')
    if any(digest(ROOT/p)!=h for p,h in plan['bindings'].items()):raise ValueError('Frozen input changed')
    if subprocess.check_output(['git','diff','HEAD','--',*plan['bindings']],cwd=ROOT,text=True).strip():raise ValueError('Commit freeze first')
    if Decimal(plan['prefix']['spent_usd'])+Decimal(plan['whole_stage_reservation_usd'])>CEILING:raise ValueError('Whole stage does not fit')
    from scripts.bounded_redesign_support import invoke
    from openai import OpenAI
    from openai.resources.chat.completions import Completions
    from openai.resources.embeddings import Embeddings
    from apps.api.app.core.config import get_settings
    configure(plan['profile'])
    if not get_settings().openai_api_key:raise ValueError('Existing credential unavailable')
    folder=FOLDER/step/'run';folder.mkdir()
    ledger=Ledger(folder,plan);suite=read(ROOT/plan['suite_path'])
    manifest=dict(status='running',started_at=now(),runtime_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        preflight_sha256=digest(folder.parent/'preflight.json'),rows=[])
    write(folder/'manifest.json',manifest)
    original,init=Completions.create,OpenAI.__init__
    def initialize(client,*args,**kwargs):kwargs.update(max_retries=0,timeout=30.0);return init(client,*args,**kwargs)
    def create(resource,*args,**body):
        if args or str(resource._client.base_url)!='https://api.openai.com/v1/':ledger.stop('Unapproved endpoint')
        resource._client.max_retries=0
        return ledger.call(lambda **kw:original(resource,**kw),body)
    try:
        with patch.object(OpenAI,'__init__',initialize),patch.object(Completions,'create',create),\
             patch.object(Embeddings,'create',side_effect=lambda *a,**kw:ledger.stop('Unexpected embedding call')):
            for case in [x for x in suite['cases'] if x['id'] in plan['case_ids']]:
                def before(turn):ledger.begin(plan['profile'],case['id'],turn)
                def after(turn,evidence):
                    write(folder/f"{case['id']}-turn-{turn['turn']}.json",dict(turn,authorized_evidence=evidence))
                    if ledger.data['stopped']:raise ValueError('Transport stopped')
                    result=turn['final_response'];allowed={s['chunk_id'] for s in evidence}
                    if any(x['chunk_id'] not in allowed for x in result.get('citations',[])):ledger.stop('Unauthorized citation')
                    if case['id']=='dev-10' and '720' in json.dumps(result):ledger.stop('Private fixture disclosure')
                result=invoke(suite,case,before_turn=before,after_turn=after)
                path=folder/(case['id']+'.json');write(path,result)
                manifest['rows'].append(dict(case_id=case['id'],path=path.name,sha256=digest(path)))
                write(folder/'manifest.json',manifest)
                print(json.dumps(dict(case_id=case['id'],http=[t['status_code'] for t in result['turns']],cumulative_usd=str(ledger.accounted))),flush=True)
        manifest['status']='complete'
    except BaseException as exc:
        manifest.update(status='stopped',exception_type=type(exc).__name__);raise
    finally:
        manifest.update(finished_at=now(),cumulative_usd=str(ledger.accounted),new_spend_usd=str(ledger.accounted-Decimal(plan['prefix']['spent_usd'])),
            ledger_sha256=digest(folder/'api-ledger.json'))
        write(folder/'manifest.json',manifest)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(sys.argv[2],sys.argv[3],sys.argv[4:])
    elif sys.argv[1]=='run':run(sys.argv[2])
    else:raise SystemExit('Use prepare or run')
