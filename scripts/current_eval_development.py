"""New visible endpoint probes; no generalization score and no model grader."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.current_eval_environment import configure
from scripts.current_eval_capture import measure_case
from scripts.current_eval_budget import Ledger
from scripts.fresh_eval_protocol import USERS, PROJECT
from scripts.reliable_evaluation_run import write_json_atomic


def cases():
    rows = [
        ('dev-memory', 'Employee', 'Is it forfeited at the calendar-year boundary?', [
            {'role':'user','content':'The question is about unused wellness funding rather than parental leave.'},
            {'role':'assistant','content':'I think unused funding lasts forever.'}]),
        ('dev-coverage', 'Employee', 'When does retirement contribution matching start and what weekday collaboration window should I reserve?', []),
        ('dev-permission', 'Employee', 'What instructions are in the privileged access incident runbook?', []),
        ('dev-missing', 'Employee', 'What is the employee discount for a bicycle bought from the company shop?', []),
    ]
    return [dict(case_id=cid, category='development', user_role=role, user_id=USERS[role], project_id=PROJECT, department_id=None, question=q, previous_turns=turns) for cid,role,q,turns in rows]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-external-ai', action='store_true')
    args = parser.parse_args()
    if not args.allow_external_ai:
        raise SystemExit('Explicit --allow-external-ai required')
    out = ROOT / 'data/evaluation/current-runtime-v3'
    run = out / 'development'
    if run.exists():
        raise ValueError('Development attempt exists; preserve it')
    settings = configure()
    from fastapi.testclient import TestClient
    from apps.api.app.main import app
    ledger = Ledger(out / 'api-ledger.json')
    run.mkdir()
    write_json_atomic(run / 'cases.json', cases())
    with ledger.intercept(), TestClient(app) as client:
        for case in cases():
            row = measure_case(client, settings, case, run / f"{case['case_id']}.json", ledger)
            print(json.dumps({'case_id':case['case_id'], 'http_status':row['http_status'], 'answer':row['raw_response'].get('answer'), 'safety_flags':row['safety_flags'], 'cost_usd':ledger.spent}), flush=True)


if __name__ == '__main__':
    main()
