"""One application capture per sealed case, with separately recorded v18 grading."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.phase73_eval_protocol import FOLDER, verify_custody, digest
from scripts.phase73_eval_environment import configure, fingerprint
from scripts.phase73_eval_budget import Ledger, BudgetStop
from scripts.phase73_eval_capture import measure_case
from scripts.quality_eval_contract_v18 import dimensions, VERSION
from scripts.quality_eval_transport_v18 import grade_case
from scripts.reanalyze_saved_answers import build_inputs
from scripts.run_fresh_eval import now
from scripts.quality_completion_durable import write_json_atomic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-external-ai',action='store_true')
    parser.add_argument('--preflight',action='store_true')
    args = parser.parse_args()
    freeze,suite = verify_custody()
    settings = configure()
    if fingerprint(settings) != freeze['environment']:
        raise ValueError('Frozen configuration/index changed')
    run = FOLDER/'run'
    if run.exists():
        raise ValueError('One-shot run already started; no retry/resume')
    ledger = Ledger()
    if len(ledger.data['calls']) != ledger.data['prior_calls']:
        raise ValueError('Unused ledger required')
    if args.preflight:
        print('Custody, readiness, index, call/token reservation and unused run verified; no calls')
        return
    if not args.allow_external_ai:
        raise SystemExit('Explicit --allow-external-ai required')
    from fastapi.testclient import TestClient
    from apps.api.app.main import app
    from openai import OpenAI
    grader = OpenAI(api_key=settings.openai_api_key,max_retries=0,timeout=60)
    run.mkdir()
    manifest = {'status':'running','started_at':now(),'freeze':freeze['commit'],
                'suite_sha256':digest(FOLDER/'holdout.json'),'version':VERSION,
                'expected_cases':60,'completed_cases':0,'initial_cost_usd':str(ledger.spent),'rows':{}}
    write_json_atomic(run/'manifest.json',manifest)
    try:
        with TestClient(app) as client:
            for case in suite['cases']:
                ledger.begin_case(case['case_id'])
                path = run/(case['case_id']+'.json')
                with ledger.intercept():
                    row = measure_case(client,settings,case,path,ledger)
                row['application_call_end'] = len(ledger.data['calls'])
                row['status'] = 'captured'
                inputs = build_inputs(case,row)
                row['grader_inputs'] = inputs
                write_json_atomic(path,row)
                if row['safety_flags']:
                    raise ValueError('Permission/scope or HTTP safety flag; no further calls')
                grade,review,error = None,None,None
                try:
                    grade,review = grade_case(grader.chat.completions.create, inputs, ledger, run/'grader'/case['case_id'])
                except (ValueError,IndexError) as exc:
                    error = type(exc).__name__
                result = dimensions(inputs,grade,row['raw_response'],row['authorized_evidence'],row['safety_flags'],review)
                row.update(grade=grade,review=review,grading_error=error,dimensions=result,
                           status='complete',grading_completed_at=now(),call_end=len(ledger.data['calls']))
                write_json_atomic(path,row)
                manifest['rows'][case['case_id']] = digest(path)
                manifest['completed_cases'] += 1
                manifest['cumulative_cost_usd'] = str(ledger.spent)
                write_json_atomic(run/'manifest.json',manifest)
                print(f"Completed {manifest['completed_cases']}/60; cumulative USD {ledger.spent}",flush=True)
                if result['unmatched_citations'] or (case['category'] in {'permissions','uploaded_document_isolation'} and result['forbidden_assertion'] == 'present'):
                    raise ValueError('Observed citation or disclosure safety failure; stop')
        manifest['status'] = 'complete'
    except BaseException as exc:
        manifest.update(status='interrupted',exception_type=type(exc).__name__)
        raise
    finally:
        manifest.update(finished_at=now(),cumulative_cost_usd=str(ledger.spent))
        write_json_atomic(run/'api-ledger.json',ledger.data)
        write_json_atomic(run/'manifest.json',manifest)


if __name__ == '__main__':
    main()
