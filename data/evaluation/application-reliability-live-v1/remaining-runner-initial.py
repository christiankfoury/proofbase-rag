"""Continue only untouched diagnostic cases after a settled local token rejection.

The interrupted case is retained, never replayed. No provider call is retried.
This is a separate evidence segment within the original USD 1 authorization.
"""
from decimal import Decimal
import sys

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import application_reliability_live as diagnostic
from scripts.phase73_v6_environment import fingerprint
from scripts.quality_cost_phase73_v2 import SpendJournal
from scripts.phase73_v6_capture import measure_case


def prepare():
    folder = diagnostic.FOLDER
    original = diagnostic.read(folder/'preflight.json')
    authorization = diagnostic.read(folder/'authorization.json')
    assert authorization['preflight_sha256'] == diagnostic.digest(folder/'preflight.json')
    assert original['suite_sha256'] == diagnostic.digest(folder/'cases.json')
    assert original['runner_sha256'] == diagnostic.digest(diagnostic.__file__)
    assert all(diagnostic.digest(ROOT/p) == sha for p,sha in original['runtime_files_sha256'].items())
    ledger = diagnostic.read(folder/'run/api-ledger.json')
    manifest = diagnostic.read(folder/'run/manifest.json')
    assert manifest['status'] == 'interrupted' and ledger['stopped'] and not ledger['unknown_outcome']
    assert ledger['stop_reason'] == 'Chat token bound exceeded'
    assert all(r['status'] == 'completed' for r in ledger['calls'])
    journal = SpendJournal().load()
    assert journal == diagnostic.read(folder/'run/additional-spend.json')
    spent = sum((Decimal(r['charged_usd']) for r in ledger['calls']), Decimal(0))
    assert spent == Decimal(manifest['charged_usd'])
    cases = diagnostic.read(folder/'cases.json')['cases']
    attempted = set(manifest['rows']) | {r['case_id'] for r in ledger['calls']}
    remaining = [c for c in cases if c['case_id'] not in attempted]
    assert [c['case_id'] for c in remaining] == [f'diag-{i:02}' for i in range(8,13)]
    assert len(ledger['calls']) + len(remaining)*10 <= 124
    assert sum(r['operation']=='chat' for r in ledger['calls']) + len(remaining)*7 <= 84
    settings = diagnostic.configure()
    state = fingerprint(settings)
    state.update(database=diagnostic.DBNAME, temperature_note='Unchanged application prompts; no evaluator')
    assert state == original['environment'], 'Indexed evidence or application configuration changed'
    plan = {'kind':'Remaining untouched cases only; no replay or provider retry', 'checked_at':diagnostic.now(),
            'original_manifest_sha256':diagnostic.digest(folder/'run/manifest.json'),
            'original_ledger_sha256':diagnostic.digest(folder/'run/api-ledger.json'),
            'case_ids':[c['case_id'] for c in remaining], 'already_charged_usd':str(spent),
            'remaining_allocation_usd':str(Decimal('1')-spent),
            'continuation_runner_sha256':diagnostic.digest(__file__),
            'reason':'Conservative serialized-byte input bound rejected question 7 before evidence assessment. Preserve that blocked result and execute only five untouched cases under unchanged per-call caps.'}
    return settings, remaining, plan


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-external-ai', action='store_true')
    args = parser.parse_args()
    settings, cases, plan = prepare()
    folder = diagnostic.FOLDER
    if not args.allow_external_ai:
        diagnostic.write(folder/'remaining-preflight.json',plan)
        print('Untouched-case continuation preflight passed; no API calls')
        return
    previous = diagnostic.read(folder/'remaining-preflight.json')
    assert all(previous[k] == plan[k] for k in plan if k != 'checked_at')
    diagnostic.ALLOCATION = Decimal(plan['remaining_allocation_usd'])
    run = folder/'remaining'
    with diagnostic.exclusive_lock(folder):
        if run.exists():
            raise diagnostic.Stop('Remaining-case segment already attempted')
        run.mkdir()
        ledger = diagnostic.Ledger(run, SpendJournal())
        # Separate identities retain the first segment's spending entries exactly.
        original_reserve = ledger.journal.reserve
        original_finish = ledger.journal.finish
        ledger.journal.reserve = lambda identity,*a,**kw: original_reserve('remaining-'+identity,*a,**kw)
        ledger.journal.finish = lambda identity,*a,**kw: original_finish('remaining-'+identity,*a,**kw)
        manifest = {'status':'running','started_at':diagnostic.now(),'rows':{}}
        diagnostic.write(run/'manifest.json', manifest)
        from fastapi.testclient import TestClient
        from apps.api.app.main import app
        try:
            with ledger.intercept(), TestClient(app) as client:
                for case in cases:
                    ledger.begin_case(case['case_id'])
                    path = run/(case['case_id']+'.json')
                    row = measure_case(client,settings,case,path,ledger)
                    manifest['rows'][case['case_id']] = diagnostic.digest(path)
                    diagnostic.write(run/'manifest.json',manifest)
                    if ledger.data['stopped'] or row['safety_flags']:
                        raise diagnostic.Stop('Budget, provider or safety stop')
                    print(f"Captured {case['case_id']}; segment USD {ledger.spent}",flush=True)
            manifest['status'] = 'complete'
        except BaseException as exc:
            manifest.update(status='interrupted',exception_type=type(exc).__name__)
            raise
        finally:
            manifest.update(finished_at=diagnostic.now(),charged_usd=str(ledger.spent),
                            total_diagnostic_usd=str(Decimal(plan['already_charged_usd'])+ledger.spent))
            diagnostic.write(run/'additional-spend.json',ledger.journal.load())
            diagnostic.write(run/'manifest.json',manifest)


if __name__ == '__main__':
    main()
