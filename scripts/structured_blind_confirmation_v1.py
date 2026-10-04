"""Fresh independently authored confirmation after immutable grader qualification."""
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import structured_blind_execution_v1 as runner
from scripts.conversation_custody import verify_bindings
from scripts.quality_confirmation_standard_v23 import check_references
from scripts.quality_completion_confirmation_v13 import load_suite
from scripts.bounded_redesign_run import read,digest,write,now

FOLDER=runner.FOLDER
FREEZE=FOLDER/'confirmation-blind-v1-freeze.json'
SUITE=FOLDER/'confirmation-blind-v1-challenges-v1.json'
VALIDATION=FOLDER/'confirmation-blind-v1-validation-v1.json'
SEAL=FOLDER/'confirmation-blind-v1-seal.json'
BRIEFS=[ROOT/'docs/phase-73/structured-blind-confirmation-authoring-brief.md',ROOT/'docs/phase-73/structured-blind-confirmation-validation-brief.md']


def readiness():
    gate=FOLDER/'structured-blind-calibration-acceptance.json';value=read(gate)
    if value['version'] != runner.contract.VERSION:raise ValueError('Structured blind qualification required')
    for label,count in [('diagnostic',16),('calibration',32)]:
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
    paths=list((ROOT/'scripts').glob('*.py'))+[runner.AUTHORIZATION, runner.references.PATH]+BRIEFS+[FOLDER/'authorization.json',FOLDER/'rolling-authorization.json',FOLDER/'structured-blind-calibration-acceptance.json']
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
    if step != 'structured-blind-confirmation':raise ValueError('One-shot confirmation only')
    funding=runner.stage_budget('confirmation')
    if folder.exists():raise ValueError('No repeated preparation')
    contract,transport=runner.versioned(frozen['version'])
    amount=sum((transport.case_bound(c['inputs']) for c in suite['cases']),Decimal(0))
    write(folder/'preflight.json',dict(stage='confirmation',step=step,version=contract.VERSION,prefix=runner.prefix(),funding=funding,maximum_calls=64,reuse={},
        case_ids=[c['id'] for c in suite['cases']],probe_ids=[],total_ceiling_usd=str(runner.CEILING),
        whole_stage_conservative_reservation_usd=str(amount),reservation_policy='rolling per-request',provider_retries=0,output_caps=transport.CAPS,
        bindings={**frozen['bindings'],**files,SEAL.relative_to(ROOT).as_posix():digest(SEAL)}))
    print(json.dumps(dict(cases=16,maximum_calls=64,reuse={},conservative_usd=str(amount),actual_prefix=runner.prefix()['spent_usd'])))


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
