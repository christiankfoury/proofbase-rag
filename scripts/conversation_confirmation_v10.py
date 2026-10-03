"""Fresh independently authored confirmation after immutable grader qualification."""
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import conversation_grader_v10 as runner
from scripts.conversation_custody import verify_bindings
from scripts.quality_confirmation_standard_v23 import check_references
from scripts.quality_completion_confirmation_v13 import load_suite
from scripts.bounded_redesign_run import read,digest,write,now

FOLDER=runner.FOLDER
FREEZE=FOLDER/'confirmation-v33-freeze.json'
SUITE=FOLDER/'confirmation-v33-challenges-v1.json'
VALIDATION=FOLDER/'confirmation-v33-validation-v1.json'
SEAL=FOLDER/'confirmation-v33-seal.json'
BRIEFS=[ROOT/'docs/phase-73/conversation-v33-confirmation-authoring-brief.md',ROOT/'docs/phase-73/conversation-v33-confirmation-validation-brief.md']


def readiness():
    gate=FOLDER/'grader-v33-calibration-acceptance.json';value=read(gate)
    for label,count in [('diagnostic',16),('calibration',24)]:
        path=ROOT/value[label+'_report_path'];report=read(path)
        if digest(path)!=value[label+'_report_sha256'] or report['count']!=count or report['matched']!=count or report['matching_probes']!=3 or report['status']!='complete':
            raise ValueError('Complete diagnostic/calibration required')
        if report['version']!=value['version']:raise ValueError('Grader version changed')
    if value['status']!='passed' or value['unresolved_findings'] or value['human_adjudication'] is not False:
        raise ValueError('Source inspection required')
    inspection=ROOT/value['source_review_path']
    if digest(inspection)!=value['source_review_sha256']:raise ValueError('Source review changed')
    return value,digest(gate)


def freeze():
    if FREEZE.exists():raise ValueError('Preserve existing freeze')
    ready,h=readiness()
    paths=list((ROOT/'scripts').glob('*.py'))+BRIEFS+[FOLDER/'authorization.json',FOLDER/'rolling-authorization.json',FOLDER/'grader-v33-calibration-acceptance.json']
    verify_bindings(ROOT,subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        {p.relative_to(ROOT).as_posix():digest(p) for p in paths})
    write(FREEZE,dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),created_at=now(),version=ready['version'],
        readiness_sha256=h,bindings={p.relative_to(ROOT).as_posix():digest(p) for p in paths}))


def custody(require_seal=True):
    ready,h=readiness();frozen=read(FREEZE)
    if h!=frozen['readiness_sha256']:raise ValueError('Readiness changed')
    if any(digest(ROOT/p)!=h for p,h in frozen['bindings'].items()):raise ValueError('Evaluator freeze changed')
    verify_bindings(ROOT,frozen['commit'],frozen['bindings'])
    suite=load_suite(SUITE);validation=read(VALIDATION)
    check_references(suite,validation,frozen)
    if validation['suite_sha256']!=digest(SUITE) or validation['freeze_sha256']!=digest(FREEZE):raise ValueError('Validation hash mismatch')
    files={p.relative_to(ROOT).as_posix():digest(p) for p in [FREEZE,SUITE,VALIDATION]}
    if require_seal and read(SEAL)['bindings']!=files:raise ValueError('Seal changed')
    return frozen,suite,files


def seal():
    if SEAL.exists():raise ValueError('Preserve existing seal')
    _,_,files=custody(False);write(SEAL,dict(created_at=now(),bindings=files))


def prepare(step):
    frozen,suite,files=custody();folder=FOLDER/step
    if folder.exists():raise ValueError('No repeated preparation')
    contract,transport=runner.versioned(frozen['version'])
    amount=sum((transport.case_bound(c['inputs']) for c in suite['cases']),Decimal(0))
    write(folder/'preflight.json',dict(stage='confirmation',step=step,version=contract.VERSION,prefix=runner.prefix(),maximum_calls=48,
        case_ids=[c['id'] for c in suite['cases']],probe_ids=[],total_ceiling_usd=str(runner.CEILING),
        whole_stage_conservative_reservation_usd=str(amount),reservation_policy='rolling per-request',provider_retries=0,output_caps=transport.CAPS,
        bindings={**frozen['bindings'],**files,SEAL.relative_to(ROOT).as_posix():digest(SEAL)}))
    print(json.dumps(dict(cases=16,maximum_calls=48,conservative_usd=str(amount),actual_prefix=runner.prefix()['spent_usd'])))


if __name__=='__main__':
    action=sys.argv[1]
    if action=='freeze':freeze()
    elif action=='seal':seal()
    elif action=='prepare':prepare(sys.argv[2])
    elif action in ('run','report'):
        _,suite,_=custody()
        fn=runner.execute if action=='run' else runner.report
        fn(sys.argv[2],case_loader=lambda stage:suite['cases'],probe_loader=lambda stage:[])
    else:raise SystemExit('Use freeze, seal, prepare, run or report')
