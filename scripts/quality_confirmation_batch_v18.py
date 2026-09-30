"""Fresh, sealed v18 confirmation through two bounded Batch waves."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import quality_confirmation_v18 as previous
from scripts import quality_batch_grading as grading
from scripts import quality_batch_transport as batch
from scripts.quality_cost_control import POLICY, FOLDER as COSTS, read, digest, charge, live_policy
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.quality_confirmation_fact_checks import check_fact_references

FOLDER = previous.FOLDER
FREEZE = FOLDER / 'v18-batch-freeze.json'
SEAL = FOLDER / 'v18-batch-seal.json'
SUITE = FOLDER / 'confirmation-challenges-v8.json'
VALIDATION = FOLDER / 'confirmation-validation-v8.json'
OUT = FOLDER / 'confirmation-v18-batch-01'
REPORT = FOLDER / 'confirmation-v18-batch-report.json'
GATE = FOLDER / 'confirmation-v18-batch-readiness.json'
REVIEW = ROOT / 'docs/phase-71/confirmation-v18-batch-source-review.md'
CODE = tuple(sorted(set(previous.CODE) | {'quality_batch_grading.py', 'quality_batch_transport.py',
    'quality_cost_control.py', 'quality_confirmation_batch_v18.py', 'test_quality_confirmation_batch_v18.py'}))


def code_hashes():
    return {name: digest(ROOT / 'scripts' / name) for name in CODE}


def check_references(suite, validation, freeze):
    check_fact_references(suite)
    cases, reviews = suite['cases'], validation.get('case_reviews', [])
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
        raise ValueError('Batch evaluator freeze changed')
    for name, expected in freeze['briefs_sha256'].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise ValueError('Neutral brief changed')
    seal = read(SEAL)
    required = [FREEZE, SUITE, VALIDATION, POLICY, previous.APPROVAL]
    if not all(p.relative_to(ROOT).as_posix() in seal['files_sha256'] for p in required):
        raise ValueError('Batch confirmation seal incomplete')
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
    suite, _ = custody()
    bound = sum((previous.case_bound(c['inputs']) / 2 for c in suite['cases']), Decimal(0))
    return {'version': previous.VERSION, 'model': previous.MODEL, 'cases': 16,
            'maximum_calls': 48, 'waves': [32, 16], 'provider_retries': 0,
            'batch_upper_bound_usd': str(bound), 'policy_sha256': digest(POLICY),
            'seal_sha256': digest(SEAL), 'additional_ceiling_usd': read(POLICY)['additional_ceiling_usd']}


def prepare(wave):
    suite, bindings = custody()
    live_policy()
    if wave == 'initial':
        plan = grading.prepare_initial(OUT, suite['cases'], bindings)
    elif wave == 'review':
        plan = grading.prepare_review(OUT)
    else:
        raise ValueError('Invalid wave')
    expected = 32 if wave == 'initial' else 16
    if plan['count'] != expected:
        raise ValueError('Unexpected request count')
    # Exact transport reconstruction is the mechanical plan review; no reference labels supplied.
    job = OUT / wave
    write(job / 'authorization.json', {'status': 'approved', 'plan_sha256': digest(job / 'plan.json'),
        'protocol_bindings': bindings, 'human_adjudication': False,
        'review': 'All requests constructed from sealed inputs by frozen v18 transport; expected wave count and custody verified.'})
    return {'wave': wave, 'requests': expected, 'reservation_usd': plan['reservation_usd']}


def replay():
    suite, bindings = custody()
    if grading.inputs_only(suite['cases']) != read(OUT / 'cases.json')['cases']:
        raise ValueError('Batch inputs differ from sealed cases')
    rebuilt = grading.replay(OUT)
    journal = read(OUT / 'additional-spend.json')
    if journal['policy_sha256'] != digest(POLICY):
        raise ValueError('Confirmation cost policy changed')
    total, calls = Decimal(0), 0
    identities = set()
    for wave, count in [('initial', 32), ('review', 16)]:
        plan, state, requests = batch.verify(OUT / wave)
        if plan['bindings'] != bindings or plan['count'] != count:
            raise ValueError('Batch plan differs from sealed protocol')
        result = read(OUT / wave / 'result.json')
        if result['status'] != 'complete' or result['errors']:
            raise ValueError('Unresolved Batch result')
        amount = Decimal(0)
        for request in requests:
            raw = read(OUT / wave / 'responses' / (request['custom_id'] + '.json'))
            value = charge(raw['response'], 'batch')
            if raw['request'] != request['body'] or value != Decimal(raw['cache_aware_cost_usd']):
                raise ValueError('Batch cost/request mismatch')
            amount += value
            calls += 1
        identity = state['journal_identity']; identities.add(identity)
        entry = journal['entries'][identity]
        if (entry['status'] != 'settled' or Decimal(entry['accounted_usd']) != amount
                or entry['reserved_usd'] != plan['reservation_usd']
                or entry['result_sha256'] != digest(OUT / wave / 'result.json')
                or Decimal(result['cache_aware_estimate_usd']) != amount
                or entry['evidence_sha256'] != digest(OUT / wave / 'plan.json')):
            raise ValueError('Batch ledger settlement mismatch')
        total += amount
    if set(journal['entries']) != identities or total > Decimal(read(POLICY)['additional_ceiling_usd']):
        raise ValueError('Unexpected call history or budget breach')
    actual = {r['id']: r for r in rebuilt['rows']}
    rows = []
    for case in suite['cases']:
        row = actual[case['id']]
        result = row['dimensions']
        mismatch = previous.compare(case, row['grade'], result)
        rows.append({'id': case['id'], 'matched': not mismatch and not result['grader_errors'] and not result['disputed_dimensions'],
                     'mismatches': mismatch, 'grader_errors': result['grader_errors'], 'disputed_dimensions': result['disputed_dimensions']})
    return {'version': previous.VERSION, 'status': 'complete', 'count': 16,
            'matched': sum(r['matched'] for r in rows), 'calls': calls, 'cost_usd': str(total),
            'ledger_sha256': digest(OUT / 'additional-spend.json'), 'seal_sha256': digest(SEAL),
            'semantic_validation_passed': False, 'human_adjudication': False, 'rows': rows}


def readiness():
    report = replay()
    gate = read(GATE)
    if (report != read(REPORT) or report['matched'] != 16
            or gate.get('status') != 'approved' or gate.get('unresolved_semantic_findings') != 0
            or gate.get('human_adjudication') is not False or gate.get('report_sha256') != digest(REPORT)
            or gate.get('source_review_sha256') != digest(REVIEW)):
        raise ValueError('Batch confirmation readiness failed')
    return digest(GATE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('preflight', 'prepare', 'submit', 'collect', 'report'))
    parser.add_argument('--wave', choices=('initial', 'review'))
    parser.add_argument('--allow-external-ai', action='store_true')
    args = parser.parse_args()
    if args.action == 'preflight':
        result = preflight()
    elif args.action == 'prepare':
        result = prepare(args.wave)
    elif args.action == 'report':
        result = replay(); write(REPORT, result)
    else:
        if not args.allow_external_ai or not args.wave:
            raise SystemExit('Explicit external approval and wave required')
        custody(); live_policy()
        from apps.api.app.core.config import get_settings
        from openai import OpenAI
        client = OpenAI(api_key=get_settings().openai_api_key, max_retries=0, timeout=60)
        result = getattr(batch, args.action)(OUT / args.wave, client, batch.SpendJournal())
        if args.action == 'collect' and result.get('status') == 'complete':
            write(OUT / 'additional-spend.json', read(COSTS / 'additional-spend.json'))
    print(json.dumps(result, indent=2))
