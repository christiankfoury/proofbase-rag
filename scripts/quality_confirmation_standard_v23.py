"""Fresh, sealed v23 confirmation through bounded standard requests."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import quality_confirmation_v23 as previous
from scripts.quality_cost_control import read, digest
from scripts.quality_cost_phase73_v2 import POLICY, live_policy, SpendJournal
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.quality_confirmation_fact_checks import check_fact_references
from scripts.quality_standard_grading import audit
from scripts.quality_development_v23 import StageLedger
from scripts.quality_eval_transport_v23 import grade_case, initial_requests, review_request
from scripts.report_quality_calibration_v12 import replay_raw
from scripts.quality_eval_contract_v23 import dimensions

FOLDER = previous.FOLDER
FREEZE = FOLDER / 'v23-standard-freeze.json'
SEAL = FOLDER / 'v23-standard-seal.json'
SUITE = FOLDER / 'confirmation-challenges-v1.json'
VALIDATION = FOLDER / 'confirmation-validation-v1.json'
OUT = FOLDER / 'confirmation-v23-standard-01'
REPORT = FOLDER / 'confirmation-v23-standard-report.json'
GATE = FOLDER / 'confirmation-v23-standard-readiness.json'
REVIEW = ROOT / 'docs/phase-73/confirmation-v23-standard-source-review.md'
CODE = tuple(sorted(set(previous.CODE) | {'quality_confirmation_v23.py',
    'quality_confirmation_standard_v23.py', 'test_quality_confirmation_standard_v23.py'}))
STAGE_LIMIT = Decimal('1.20')
PREFIX = previous.development.output('calibration') / 'additional-spend.json'


def retained_entries():
    return read(PREFIX)['entries']



def code_hashes():
    return {name: digest(ROOT / 'scripts' / name) for name in CODE}


def check_references(suite, validation, freeze):
    check_fact_references(suite)
    cases, reviews = suite['cases'], validation.get('case_reviews', [])
    from scripts.quality_eval_contract_v23 import metadata
    if any(c['inputs'].get('source_metadata', []) != metadata(c['evidence']) for c in cases):
        raise ValueError('Authoritative source title mapping differs')
    if not all(r.get('reference_scope_reviewed') is True and r.get('reference_scope_reason', '').strip() for r in reviews):
        raise ValueError('Independent question/reference scope review required')
    if (suite.get('authored_after_freeze') != freeze['commit']
            or validation.get('status') != 'approved' or validation.get('human_adjudication') is not False
            or validation.get('case_count') != 16 or len(cases) != 16 or len(reviews) != 16
            or validation.get('unresolved_findings') != []
            or {r['id'] for r in reviews} != {c['id'] for c in cases}
            or not all(r.get('accept') is True for r in reviews)
            or {r['id']: r.get('independently_derived_expected') for r in reviews} != {c['id']: c['expected'] for c in cases}
            or {r['id']: r.get('independently_derived_fact_statuses') for r in reviews} != {c['id']: c['expected_fact_statuses'] for c in cases}):
        raise ValueError('Independent references or post-freeze authorship failed')


def custody():
    ready = previous.readiness()  # Reuse immutable passing development, before fresh content.
    freeze = read(FREEZE)
    if (freeze.get('readiness_sha256') != ready or freeze.get('code_sha256') != code_hashes()
            or freeze.get('policy_sha256') != digest(POLICY)
            or freeze.get('authorization_sha256') != digest(previous.APPROVAL)):
        raise ValueError('Standard evaluator freeze changed')
    for name, expected in freeze['briefs_sha256'].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise ValueError('Neutral brief changed')
    seal = read(SEAL)
    required = [FREEZE, SUITE, VALIDATION, POLICY, previous.APPROVAL, PREFIX]
    if not all(p.relative_to(ROOT).as_posix() in seal['files_sha256'] for p in required):
        raise ValueError('Standard confirmation seal incomplete')
    for name, expected in seal['files_sha256'].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise ValueError('Sealed artifact changed')
    suite = previous.original.load_suite(SUITE)
    validation = read(VALIDATION)
    if validation.get('suite_sha256') != digest(SUITE) or validation.get('freeze_sha256') != digest(FREEZE):
        raise ValueError('Independent validation hash mismatch')
    check_references(suite, validation, freeze)
    bindings = {p.relative_to(ROOT).as_posix(): digest(p) for p in [*required, SEAL, previous.GATE]}
    return suite, bindings


def preflight():
    suite, bindings = custody()
    policy, ceiling = live_policy()
    spending = SpendJournal().load()
    if any(row['status'] != 'settled' for row in spending['entries'].values()):
        raise ValueError('Pending provider outcome blocks execution')
    amount = sum((previous.case_bound(c['inputs']) for c in suite['cases']), Decimal(0))
    accounted = sum((Decimal(r['accounted_usd']) for r in spending['entries'].values()), Decimal(0))
    if spending != read(PREFIX):
        raise ValueError('Prior development spending differs')
    if accounted + STAGE_LIMIT > ceiling:
        raise ValueError('Confirmation stage allowance exceeds remaining shared ceiling')
    return {'cases': 16, 'maximum_calls': 48, 'token_based_upper_bound_usd': str(amount), 'stage_spending_limit_usd': str(STAGE_LIMIT),
            'accounted_before_usd': str(accounted), 'additional_ceiling_usd': str(ceiling),
            'provider_retries': 0, 'bindings': bindings, 'code_sha256': code_hashes()}


def execute(client):
    plan = preflight()
    suite, _ = custody()
    if client.max_retries != 0 or OUT.exists():
        raise ValueError('Retries or repeated attempt are forbidden')
    journal = SpendJournal()
    ledger = StageLedger(OUT / 'requests', journal, 48, STAGE_LIMIT)
    manifest = {'status': 'running', 'plan': plan, 'rows': {}, 'human_adjudication': False}
    write(OUT / 'manifest.json', manifest)
    try:
        for case in suite['cases']:
            grade = review = error = None
            try:
                grade, review = grade_case(client.chat.completions.create, case['inputs'], ledger,
                                          OUT / 'requests' / case['id'])
            except (ValueError, IndexError) as exc:
                error = type(exc).__name__
            result = dimensions(case['inputs'], grade, case['payload'], case['evidence'], case['safety_flags'], review)
            mismatch = previous.compare(case, grade, result)
            path = OUT / (case['id'] + '.json')
            write(path, {'grade': grade, 'review': review, 'error': error, 'dimensions': result, 'mismatches': mismatch})
            manifest['rows'][case['id']] = digest(path)
            write(OUT / 'manifest.json', manifest)
            print(f"Completed {len(manifest['rows'])}/16; {'matches' if not mismatch else 'disagreement'}", flush=True)
        manifest['status'] = 'complete'
    except BaseException as exc:
        manifest.update(status='interrupted', exception_type=type(exc).__name__)
        raise
    finally:
        write(OUT / 'manifest.json', manifest)
        write(OUT / 'additional-spend.json', journal.load())


def replay():
    suite, bindings = custody()
    manifest = read(OUT / 'manifest.json')
    if manifest['plan']['bindings'] != bindings or manifest['plan']['code_sha256'] != code_hashes():
        raise ValueError('Synchronous manifest custody changed')
    rows, bodies = [], []
    for case in suite['cases']:
        if case['id'] not in manifest['rows']:
            continue
        path = OUT / (case['id'] + '.json')
        if digest(path) != manifest['rows'][case['id']]:
            raise ValueError('Grading row changed')
        saved = read(path)
        grade = review = error = None
        try:
            parts = {}
            for purpose, body in initial_requests(case['inputs']):
                bodies.append(body)
                parts.update(replay_raw(OUT / 'requests' / case['id'] / (purpose + '.json'), body))
            body = review_request(case['inputs'], parts); bodies.append(body)
            review = replay_raw(OUT / 'requests' / case['id'] / 'review.json', body)
            grade = parts
        except (ValueError, IndexError) as exc:
            error = type(exc).__name__
        result = dimensions(case['inputs'], grade, case['payload'], case['evidence'], case['safety_flags'], review)
        mismatch = previous.compare(case, grade, result)
        if saved != {'grade': grade, 'review': review, 'error': error, 'dimensions': result, 'mismatches': mismatch}:
            raise ValueError('Synchronous grading reconstruction differs')
        rows.append({'id': case['id'], 'matched': not mismatch and not result['grader_errors'] and not result['disputed_dimensions'],
                     'mismatches': mismatch, 'grader_errors': result['grader_errors'], 'disputed_dimensions': result['disputed_dimensions']})
    snapshot = read(OUT / 'additional-spend.json')
    class Snapshot:
        policy_path = POLICY
        def load(self):
            return snapshot
    total = audit(OUT / 'requests', bodies, Snapshot())
    retained = retained_entries()
    calls = read(OUT / 'requests/calls.json')['calls']
    if (any(snapshot['entries'].get(k) != v for k,v in retained.items())
            or set(snapshot['entries']) != set(retained) | {r['identity'] for r in calls}):
        raise ValueError('Full spending history differs')
    accounted = sum((Decimal(r['accounted_usd']) for r in snapshot['entries'].values()), Decimal(0))
    if total > STAGE_LIMIT or accounted > Decimal(read(POLICY)['additional_ceiling_usd']):
        raise ValueError('Additional cap exceeded')
    return {'version': previous.VERSION, 'status': manifest['status'], 'count': len(rows),
            'matched': sum(r['matched'] for r in rows), 'calls': len(calls), 'cost_usd': str(total),
            'additional_accounted_usd': str(accounted), 'prior_accounted_usd': str(accounted-total),
            'seal_sha256': digest(SEAL), 'ledger_sha256': digest(OUT / 'additional-spend.json'),
            'semantic_validation_passed': False, 'human_adjudication': False, 'rows': rows}


def readiness():
    report, gate = replay(), read(GATE)
    if (report != read(REPORT) or report['status'] != 'complete' or report['count'] != 16
            or report['matched'] != 16 or report['calls'] != 48 or gate.get('status') != 'approved'
            or gate.get('unresolved_semantic_findings') != 0 or gate.get('human_adjudication') is not False
            or gate.get('report_sha256') != digest(REPORT) or gate.get('source_review_sha256') != digest(REVIEW)):
        raise ValueError('Synchronous confirmation readiness failed')
    return digest(GATE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['preflight', 'execute', 'report'])
    parser.add_argument('--allow-external-ai', action='store_true')
    args = parser.parse_args()
    if args.action == 'execute':
        if not args.allow_external_ai:
            raise SystemExit('Explicit external approval required')
        preflight()
        from apps.api.app.core.config import get_settings
        from openai import OpenAI
        execute(OpenAI(api_key=get_settings().openai_api_key, max_retries=0, timeout=180))
    elif args.action == 'report':
        result = replay(); write(REPORT, result)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(preflight(), indent=2))
