"""Audit the stopped Phase 73 attempt without releasing or retrying its unknown call.

This post-run publication supplement never changes the frozen runner or its ledger.
It cannot produce a validated full-suite score, including with an approval file.
"""
import argparse
from collections import Counter
from decimal import Decimal
import json
import math
from pathlib import Path
import statistics
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.phase73_eval_protocol import FOLDER, verify_custody, digest
from scripts.phase73_eval_budget import bounds, request_hash, reserve
from scripts.phase73_eval_history import PriorLedger
from scripts.report_phase73_eval import (read, audit_calls, build_inputs, dimensions,
    transport, replay_raw, DIMS, VERSION, POLICY, CONFIRMATION)
from scripts.quality_completion_durable import write_json_atomic


def validate_unknown(row, raw):
    """Only explain the observed timeout; do not turn it into a settled receipt."""
    limits = reserve(raw['request'])
    if (row['status'] != 'unknown' or row['operation'] != 'grader'
            or raw.get('status') != 'started' or raw.get('response') is not None
            or raw.get('exception_type') != 'APITimeoutError'
            or row['model'] != transport.MODEL
            or row['request_sha256'] != request_hash(raw['request'])
            or row['input_bound'] != limits['input_bound']
            or row['output_cap'] != limits['output_cap']
            or Decimal(row['reserved_usd']) != limits['reserved_usd']
            or row['charged_usd'] != row['reserved_usd']
            or row['input_tokens'] is not None or row['output_tokens'] is not None
            or row.get('raw_sha256') is not None):
        raise ValueError('Unknown outcome or its full reservation changed')


def audit_spend(calls):
    baseline = read(CONFIRMATION/'additional-spend.json')
    snapshot = read(FOLDER/'run/additional-spend.json')
    if baseline['policy_sha256'] != snapshot['policy_sha256'] or snapshot['policy_sha256'] != digest(POLICY):
        raise ValueError('Spending policy changed')
    expected = dict(baseline['entries'])
    for row in calls:
        identity = row['additional_spend_identity']
        if identity in expected:
            raise ValueError('Duplicate spending identity')
        expected[identity] = {
            'status': 'settled' if row['status'] == 'completed' else 'unknown',
            'reserved_usd': row['reserved_usd'], 'accounted_usd': row['charged_usd'],
            'evidence_sha256': row['request_sha256'],
            'result_sha256': digest(FOLDER/row['raw_path'])}
    if expected != snapshot['entries']:
        raise ValueError('Spending snapshot differs from complete history')
    total = sum((Decimal(r['accounted_usd']) for r in expected.values()), Decimal(0))
    if total > Decimal(read(POLICY)['additional_ceiling_usd']):
        raise ValueError('Spending ceiling exceeded')
    return total


def replay():
    freeze, suite = verify_custody(require_current=False)
    seal = read(FOLDER/'interruption-seal.json')
    actual_paths = {p.relative_to(ROOT).as_posix() for p in (FOLDER/'run').rglob('*.json')}
    if set(seal['run_files_sha256']) != actual_paths:
        raise ValueError('Interrupted artifact inventory changed')
    for name, expected in seal['run_files_sha256'].items():
        if digest(ROOT/name) != expected:
            raise ValueError('Interrupted evidence changed: '+name)
    data = read(FOLDER/'run/api-ledger.json')
    prior = PriorLedger(FOLDER/'prior-ledger.json')
    count = len(prior.data['calls'])
    if (data != read(FOLDER/'api-ledger.json') or digest(FOLDER/'api-ledger.json') != seal['root_ledger_sha256']
            or data['prior_calls'] != count or data['prior_sha256'] != digest(FOLDER/'prior-ledger.json')
            or data['prior_spend_usd'] != str(prior.spent)
            or data['calls'][:count] != prior.data['calls'] or data['bounds'] != bounds()
            or data['authorization_sha256'] != digest(ROOT/'data/evaluation/quality-completion-v1/autonomous-authorization.json')
            or data['unknown_outcome'] is not True or data['budget_exhausted'] is not False):
        raise ValueError('Stopped ledger or historical prefix changed')
    calls = data['calls'][count:]
    if (not calls or [r['call_index'] for r in calls] != list(range(count, len(data['calls'])))
            or any(r['status'] != 'completed' for r in calls[:-1]) or calls[-1]['status'] != 'unknown'):
        raise ValueError('Expected one final unknown call and no subsequent requests')
    paths = [(FOLDER/r['raw_path']).resolve() for r in calls]
    if len(set(paths)) != len(paths) or any(not p.is_relative_to((FOLDER/'run').resolve()) for p in paths):
        raise ValueError('Unsafe or duplicated call path')
    audit_calls(SimpleNamespace(data={'prior_calls': 0, 'calls': calls[:-1]}))
    unknown = calls[-1]
    validate_unknown(unknown, read(paths[-1]))
    additional = audit_spend(calls)
    manifest = read(FOLDER/'run/manifest.json')
    total = prior.spent + sum((Decimal(r['charged_usd']) for r in calls), Decimal(0))
    n = manifest['completed_cases']
    expected_ids = [c['case_id'] for c in suite['cases'][:n]]
    if (manifest['status'] != 'interrupted' or manifest['exception_type'] != 'APITimeoutError'
            or manifest['freeze'] != freeze['commit'] or manifest['suite_sha256'] != digest(FOLDER/'holdout.json')
            or manifest['expected_cases'] != 60 or not 0 <= n < 60
            or list(manifest['rows']) != expected_ids or manifest['initial_cost_usd'] != str(prior.spent)
            or manifest['cumulative_cost_usd'] != str(total)):
        raise ValueError('Interrupted manifest changed')
    rows, captures = [], []
    for index, case in enumerate(suite['cases'][:n+1]):
        cid = case['case_id']; path = FOLDER/'run'/(cid+'.json'); saved = read(path)
        inputs = build_inputs(case, saved)
        case_calls = [r for r in calls if r['case_id'] == cid]
        if (saved['case_id'] != cid or saved['category'] != case['category']
                or inputs != saved['grader_inputs'] or saved['http_status'] != 200 or saved['safety_flags']
                or not case_calls or case_calls[0]['call_index'] != saved['call_start']):
            raise ValueError('Captured response or call binding changed')
        app_calls = [r for r in case_calls if r['operation'] != 'grader']
        grader_calls = [r for r in case_calls if r['operation'] == 'grader']
        if ([r['call_index'] for r in app_calls] != list(range(saved['call_start'], saved['application_call_end']))
                or len(grader_calls) != 3
                or [r['call_index'] for r in case_calls] != list(range(saved['call_start'], saved['application_call_end']+3))):
            raise ValueError('Noncontiguous application/grader interval')
        captures.append({'case_id': cid, 'latency_ms': saved['latency_ms'],
                         'http_status': saved['http_status'], 'safety_flags': saved['safety_flags']})
        parts = {}
        for purpose, body in transport.initial_requests(inputs):
            parts.update(replay_raw(FOLDER/'run/grader'/cid/(purpose+'.json'), body))
        review_body = transport.review_request(inputs, parts)
        if index == n:
            if (cid != unknown['case_id'] or saved['status'] != 'captured'
                    or any(k in saved for k in ['grade', 'review', 'dimensions'])
                    or read(paths[-1])['request'] != review_body):
                raise ValueError('Partial case was changed or graded without a review')
            continue
        review = replay_raw(FOLDER/'run/grader'/cid/'review.json', review_body)
        result = dimensions(inputs, parts, saved['raw_response'], saved['authorized_evidence'], [], review)
        if (digest(path) != manifest['rows'][cid] or saved['status'] != 'complete'
                or (parts, review, None, result) != (saved['grade'], saved['review'], saved['grading_error'], saved['dimensions'])
                or saved['call_end'] != case_calls[-1]['call_index']+1):
            raise ValueError('Completed row replay mismatch')
        rows.append({'case_id': cid, 'category': case['category'], 'expected_behavior': case['expected_behavior'],
                     'dimensions': result, 'http_status': saved['http_status'], 'latency_ms': saved['latency_ms'],
                     'calls': len(case_calls), 'cost_usd': str(sum((Decimal(r['charged_usd']) for r in case_calls), Decimal(0)))})
    captured_ids = [c['case_id'] for c in suite['cases'][:n+1]]
    if ({r['case_id'] for r in calls} != set(captured_ids)
            or {p.stem for p in (FOLDER/'run').glob('fresh-*.json')} != set(captured_ids)):
        raise ValueError('Unexpected execution after interruption')
    safety = [r['case_id'] for r in rows if r['dimensions']['recorded_safety_flags'] or r['dimensions']['unmatched_citations']
              or r['category'] in {'permissions','uploaded_document_isolation'} and r['dimensions']['forbidden_assertion']=='present']
    latency = sorted(c['latency_ms'] for c in captures)
    settled = sum((Decimal(r['charged_usd']) for r in calls[:-1]), Decimal(0))
    held = Decimal(unknown['reserved_usd'])
    inspection = read(FOLDER/'publication-review.json')
    if (inspection.get('status') != 'rejected' or inspection.get('human_adjudication') is not False
            or inspection.get('manifest_sha256') != digest(FOLDER/'run/manifest.json')
            or inspection.get('source_review_sha256') != digest(ROOT/'docs/phase-73/source-review.md')
            or inspection.get('completed_case_inspections') != n
            or inspection.get('partial_case_inspections') != 1
            or inspection.get('unexecuted_cases') != 60-len(captures)
            or inspection.get('unresolved_semantic_findings') != len(inspection.get('finding_ids', []))):
        raise ValueError('Interrupted source-inspection record changed')
    return {'kind': 'interrupted_fresh_runtime_dimensions', 'publication_version': 'phase73-interruption.v1',
        'version': VERSION, 'model': transport.MODEL, 'runtime_commit': freeze['commit'],
        'suite_version': suite['version'], 'status': 'interrupted', 'exception_type': 'APITimeoutError',
        'expected_cases': 60, 'completed_cases': n, 'captured_cases': len(captures),
        'ungraded_captured_cases': 1, 'unexecuted_cases': 60-len(captures),
        'candidate_passes': sum(r['dimensions']['target_credit'] for r in rows),
        'source_inspection_passed': False, 'validated_passes': None, 'target': 48, 'target_met': False,
        'source_inspection_finding_ids': inspection['finding_ids'],
        'category_counts': dict(Counter(c['category'] for c in suite['cases'])),
        'completed_category_counts': dict(Counter(r['category'] for r in rows)),
        'dimensions': {k: dict(Counter(r['dimensions'][k] for r in rows)) for k in [*DIMS,'overall']},
        'invalid_grades': sum(bool(r['dimensions']['grader_errors']) for r in rows),
        'disputed_cases': [r['case_id'] for r in rows if r['dimensions']['disputed_dimensions']],
        'safety_flag_cases': safety, 'calls': len(calls), 'settled_calls': len(calls)-1, 'unknown_calls': 1,
        'operation_counts': dict(Counter(r['operation'] for r in calls)),
        'cumulative_calls': len(data['calls']), 'cumulative_cost_usd': str(total),
        'holdout_cost_usd': str(settled+held), 'settled_usage_cost_usd': str(settled), 'unknown_reserved_usd': str(held),
        'additional_spend_usd': str(additional), 'additional_ceiling_usd': read(POLICY)['additional_ceiling_usd'],
        'latency_ms': {'count': len(latency), 'median': statistics.median(latency),
                       'p95': latency[math.ceil(.95*len(latency))-1],
                       'scope': 'all captured application queries; grading and fixture indexing excluded'},
        'human_adjudication': False, 'cases': rows, 'captures': captures,
        'limitation': 'Interrupted at the case 11 review timeout: 10 graded, 11 captured, 49 unexecuted. No full-suite score or target success. Primary source inspection records unresolved semantic concerns; original model decisions are unchanged. Cost includes a full unknown-call reservation, not a confirmed charge. The permission, memory, ambiguity, injection and upload-isolation groups were not executed. Agent-authored synthetic evidence, not human-verified accuracy or independent security validation.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true')
    args = parser.parse_args(); result = replay()
    if args.check:
        if result != read(FOLDER/'public-report.json'):
            raise ValueError('Published interruption report differs from saved evidence')
        print('Interrupted evidence, completed replay and retained unknown reservation verified offline; no full-suite score')
    else:
        write_json_atomic(FOLDER/'public-report.json', result)
        print(json.dumps({k:v for k,v in result.items() if k not in {'cases','captures','dimensions'}}, indent=2))
