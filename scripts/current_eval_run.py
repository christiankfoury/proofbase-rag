"""One-shot application capture and separate dimension grading for a fresh suite."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.current_eval_protocol import FOLDER, verify_custody, digest
from scripts.current_eval_environment import configure, fingerprint
from scripts.current_eval_budget import Ledger, BudgetStop
from scripts.current_eval_capture import measure_case
from scripts.current_dimension_grader import grade_response, dimensions, VERSION
from scripts.reanalyze_saved_answers import build_inputs, DIMS
from scripts.run_fresh_eval import now
from scripts.reliable_evaluation_run import write_json_atomic


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--allow-external-ai', action='store_true')
    ap.add_argument('--preflight', action='store_true')
    args = ap.parse_args()
    freeze, suite = verify_custody()
    settings = configure()
    if fingerprint(settings) != freeze['environment']:
        raise ValueError('Frozen configuration or index changed')
    run = FOLDER / 'run'
    if run.exists():
        raise ValueError('One-shot run already started; no retry or resume')
    if args.preflight:
        print('Custody, configuration, index and unused run path verified; no calls')
        return
    if not args.allow_external_ai:
        raise SystemExit('Explicit --allow-external-ai required')
    from fastapi.testclient import TestClient
    from apps.api.app.main import app
    from openai import OpenAI
    ledger = Ledger(FOLDER / 'api-ledger.json')
    if ledger.data.get('unknown_outcome') or ledger.data.get('budget_exhausted'):
        raise BudgetStop('Ledger is stopped')
    run.mkdir()
    manifest = {'status':'running', 'started_at':now(), 'freeze':freeze['commit'], 'suite_sha256':digest(FOLDER/'holdout.json'), 'version':VERSION, 'expected_cases':60, 'completed_cases':0, 'initial_cost_usd':ledger.spent, 'rows':{}}
    write_json_atomic(run/'manifest.json', manifest)
    try:
        with ledger.intercept(), TestClient(app) as client:
            grader = OpenAI(api_key=settings.openai_api_key)
            for case in suite['cases']:
                path = run / f"{case['case_id']}.json"
                row = measure_case(client, settings, case, path, ledger)
                row['status'] = 'captured'
                inputs = build_inputs(case, row)
                row['grader_inputs'] = inputs
                write_json_atomic(path, row)
                grade = None
                row['raw_grader_responses'] = []
                def recorded_create(**kwargs):
                    response = grader.chat.completions.create(**kwargs)
                    row['raw_grader_responses'].append({'request':kwargs, 'response':response.model_dump(mode='json')})
                    write_json_atomic(path, row)
                    return response
                recording_grader = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=recorded_create)))
                try:
                    grade = grade_response(recording_grader, inputs)
                except ValueError:
                    # Provider response was saved/charged, but its grade is invalid.
                    # No second attempt and no application retry.
                    row['grading_error'] = 'invalid_or_incomplete_grade'
                result = dimensions(inputs, grade, row['raw_response'], row['authorized_evidence'], row['safety_flags'])
                row.update(grade=grade, dimensions=result, status='complete', grading_completed_at=now(), call_end=len(ledger.data['calls']))
                write_json_atomic(path, row)
                manifest['rows'][case['case_id']] = digest(path)
                manifest['completed_cases'] += 1
                manifest['cumulative_cost_usd'] = ledger.spent
                write_json_atomic(run/'manifest.json', manifest)
                print(f"Completed {manifest['completed_cases']}/60; estimated cumulative USD {ledger.spent:.4f}", flush=True)
                if row['safety_flags']:
                    raise ValueError('Safety or HTTP failure; stop without retries')
    except Exception as exc:
        manifest.update(status='interrupted', exception_type=type(exc).__name__)
        raise
    finally:
        if manifest['completed_cases'] == 60 and manifest['status'] == 'running':
            manifest['status'] = 'complete'
        manifest.update(finished_at=now(), cumulative_cost_usd=ledger.spent)
        write_json_atomic(run/'manifest.json', manifest)


if __name__ == '__main__':
    main()
