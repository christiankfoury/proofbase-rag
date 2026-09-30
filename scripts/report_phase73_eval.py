"""Offline replay of sealed evidence, mixed-model costs and full-response metrics."""
import argparse
from collections import Counter
from decimal import Decimal
import json
import math
from pathlib import Path
import statistics
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.phase73_eval_protocol import FOLDER,verify_custody,digest
from scripts.phase73_eval_budget import Ledger,PRICES,request_hash
from scripts.quality_eval_contract_v18 import VERSION,dimensions
from scripts import quality_eval_transport_v18 as transport
from scripts.report_quality_calibration_v12 import replay_raw
from scripts.reanalyze_saved_answers import build_inputs,DIMS
from scripts.quality_completion_durable import write_json_atomic


def read(path):
    return json.loads(path.read_bytes())


def audit_calls(ledger):
    seen = set()
    calls = ledger.data['calls'][ledger.data['prior_calls']:]
    for row in calls:
        path = (FOLDER/row['raw_path']).resolve()
        if not path.is_relative_to(FOLDER.resolve()) or path in seen:
            raise ValueError('Duplicate or unsafe raw path')
        seen.add(path)
        raw = read(path)
        if (row['status'] != 'completed' or raw['status'] != 'received'
            or digest(path) != row['raw_sha256'] or request_hash(raw['request']) != row['request_sha256']
            or raw['request']['model'] != row['model'] or raw['response']['model'] != row['response_model']):
            raise ValueError('Raw request/response binding failed')
        usage = raw['response']['usage']
        it,ot = usage['prompt_tokens'],usage.get('completion_tokens',0)
        ri,ro = map(Decimal,PRICES[row['model']])
        if ((it*ri+ot*ro)/1_000_000 != Decimal(row['charged_usd'])
            or (it,ot) != (row['input_tokens'],row['output_tokens'])
            or it > row['input_bound'] or ot > row['output_cap']):
            raise ValueError('Token settlement mismatch')
    return calls


def replay():
    freeze,suite = verify_custody(require_current=False)
    ledger = Ledger(FOLDER/'run/api-ledger.json')
    # Snapshot carries the identical prefix provenance stored at the folder root.
    calls = audit_calls(ledger)
    manifest = read(FOLDER/'run/manifest.json')
    if (manifest['freeze'] != freeze['commit'] or manifest['suite_sha256'] != digest(FOLDER/'holdout.json')
        or manifest['cumulative_cost_usd'] != str(ledger.spent)
        or manifest['initial_cost_usd'] != ledger.data['prior_spend_usd']):
        raise ValueError('Run custody/cost mismatch')
    rows = []
    for case in suite['cases']:
        cid = case['case_id']
        if cid not in manifest['rows']:
            continue
        path = FOLDER/'run'/(cid+'.json')
        if digest(path) != manifest['rows'][cid]:
            raise ValueError('Captured row changed')
        saved = read(path)
        inputs = build_inputs(case,saved)
        if inputs != saved['grader_inputs']:
            raise ValueError('Grader input differs from authorized source evidence')
        grade,review,error = None,None,None
        try:
            parts = {}
            for purpose,body in transport.initial_requests(inputs):
                parts.update(replay_raw(FOLDER/'run/grader'/cid/(purpose+'.json'),body))
            review = replay_raw(FOLDER/'run/grader'/cid/'review.json',transport.review_request(inputs,parts))
            grade = parts
        except (ValueError,IndexError) as exc:
            error = type(exc).__name__
        result = dimensions(inputs,grade,saved['raw_response'],saved['authorized_evidence'],saved['safety_flags'],review)
        if (grade,review,error,result) != (saved['grade'],saved['review'],saved['grading_error'],saved['dimensions']):
            raise ValueError('Raw grading/reducer reconstruction mismatch')
        case_calls = [r for r in calls if r['case_id'] == cid]
        if [r['call_index'] for r in case_calls] != list(range(saved['call_start'],saved['call_end'])):
            raise ValueError('Case call interval mismatch')
        rows.append({'case_id':cid,'category':case['category'],'expected_behavior':case['expected_behavior'],
                     'dimensions':result,'http_status':saved['http_status'],'latency_ms':saved['latency_ms'],
                     'calls':len(case_calls),'cost_usd':str(sum((Decimal(r['charged_usd']) for r in case_calls),Decimal(0)))})
    if len(rows) != manifest['completed_cases']:
        raise ValueError('Completed denominator mismatch')
    complete = manifest['status'] == 'complete' and len(rows) == 60
    successes = sum(r['dimensions']['target_credit'] for r in rows)
    safety = [r['case_id'] for r in rows if r['dimensions']['recorded_safety_flags'] or r['dimensions']['unmatched_citations']
              or (r['category'] in {'permissions','uploaded_document_isolation'} and r['dimensions']['forbidden_assertion'] == 'present')]
    review_path = FOLDER/'publication-review.json'
    source_review = read(review_path) if review_path.exists() else None
    validated = bool(source_review and source_review.get('status') == 'approved'
                     and source_review.get('unresolved_semantic_findings') == 0
                     and source_review.get('human_adjudication') is False
                     and source_review.get('manifest_sha256') == digest(FOLDER/'run/manifest.json')
                     and source_review.get('source_review_sha256') == digest(ROOT/'docs/phase-73/source-review.md'))
    latency = sorted(r['latency_ms'] for r in rows)
    return {'kind':'fresh_current_runtime_dimensions','version':VERSION,'model':transport.MODEL,
            'runtime_commit':freeze['commit'],'suite_version':suite['version'],'status':manifest['status'],
            'expected_cases':60,'completed_cases':len(rows),'candidate_passes':successes,
            'source_inspection_passed':validated,'validated_passes':successes if complete and validated and not safety else None,
            'target':48,'target_met':bool(complete and validated and not safety and successes >= 48),
            'category_counts':dict(Counter(c['category'] for c in suite['cases'])),
            'dimensions':{k:dict(Counter(r['dimensions'][k] for r in rows)) for k in [*DIMS,'overall']},
            'invalid_grades':sum(bool(r['dimensions']['grader_errors']) for r in rows),
            'disputed_cases':[r['case_id'] for r in rows if r['dimensions']['disputed_dimensions']],
            'safety_flag_cases':safety,'calls':len(calls),'operation_counts':dict(Counter(r['operation'] for r in calls)),
            'cumulative_calls':len(ledger.data['calls']),'cumulative_cost_usd':str(ledger.spent),
            'holdout_cost_usd':str(ledger.spent-Decimal(manifest['initial_cost_usd'])),
            'latency_ms':{'count':len(latency),'median':statistics.median(latency) if latency else None,
                          'p95':latency[math.ceil(.95*len(latency))-1] if latency else None,
                          'scope':'application query only; fixture indexing and grader excluded'},
            'human_adjudication':False,'cases':rows,
            'limitation':'Agent-authored synthetic cases and model judgments with primary-agent source inspection; not human-verified population accuracy or independent security validation. Different suite/evaluator from historical runs; no controlled before/after claim. Unresolved judgments receive no target credit; quotation fidelity is separate.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    report = replay()
    if args.check:
        if report != read(FOLDER/'public-report.json'):
            raise ValueError('Published report differs from replay')
        print('Custody, raw outputs, dimensions, call ledger and published report verified offline')
    else:
        write_json_atomic(FOLDER/'public-report.json',report)
        print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
