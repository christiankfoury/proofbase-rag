"""Offline receipt reuse and whole-path assessment; no execution or authorization."""
from decimal import Decimal
import json
import sys

from scripts import conversation_ordering_v2 as references
from scripts import structured_blind_evaluator_v1 as evaluator
from scripts import quality_eval_transport_v35 as transport
from scripts.bounded_redesign_run import read, digest, response_charge, request_hash
from scripts.conversation_v35_budget import prefix, CEILING, FINAL_FLOOR
from scripts.report_quality_calibration_v12 import replay_raw
from scripts.conversation_custody import verify_bindings

ROOT, FOLDER = references.legacy.ROOT, references.legacy.FOLDER
REPORT = FOLDER / 'structured-blind-v1' / 'offline-assessment.json'


def _cost_proxy(raw):
    """Observed token lengths at frozen rates, with NO future cache savings."""
    usage = raw['response']['usage']
    return (Decimal(usage['prompt_tokens']) * transport.INPUT_RATE +
            Decimal(usage['completion_tokens']) * transport.OUTPUT_RATE) / 1000000


def reusable_coverage(case, stage):
    """At most judge A. Neither second blind draw nor overall approval is reused."""
    folder = FOLDER / ('grader-v35-' + stage)
    manifest = read(folder / 'run/manifest.json')
    if case['id'] not in manifest['rows']:
        return None
    path = folder / 'run/raw' / case['id'] / 'coverage.json'
    plan = evaluator.request_plan(case['inputs'])
    body = next(r['body'] for r in plan if r['judge'] == 'a' and r['purpose'] == 'coverage')
    raw = read(path)
    if raw['request'] != body:
        return None
    preflight = read(folder / 'preflight.json')
    if digest(folder / 'preflight.json') != manifest['preflight_sha256']:
        raise ValueError('Old preflight changed')
    verify_bindings(ROOT, manifest['runtime_commit'], preflight['bindings'])
    ledger = read(folder / 'run/api-ledger.json')
    if digest(folder / 'run/api-ledger.json') != manifest['ledger_sha256']:
        raise ValueError('Old ledger changed')
    receipt = next(c for c in ledger['calls'] if c['raw_path'] == path.relative_to(folder / 'run').as_posix())
    if (receipt['raw_sha256'] != digest(path) or receipt['status'] != 'completed'
            or receipt['request_sha256'] != request_hash(body)
            or Decimal(receipt['accounted_usd']) != response_charge(raw['response'], body['model'])):
        raise ValueError('Unverified coverage receipt')
    coverage = replay_raw(path, body)
    row_path = folder / 'run' / (case['id'] + '.json')
    if digest(row_path) != manifest['rows'][case['id']]:
        raise ValueError('Old judgment changed')
    saved = read(row_path)
    if saved['error'] or any(saved['grade'][k] != value for k, value in coverage.items()):
        raise ValueError('Coverage replay differs')
    return dict(stage=stage, case_id=case['id'], judge='a', purpose='coverage',
                raw_path=path.relative_to(ROOT).as_posix(), raw_sha256=digest(path),
                request_sha256=request_hash(body), cost_proxy_usd=str(_cost_proxy(raw)),
                reuse_kind='component_only', acceptance_reused=False)


def _averages(stage):
    folder = FOLDER / ('grader-v35-' + stage) / 'run'
    groups = {'claims': [], 'coverage': []}
    for receipt in read(folder / 'api-ledger.json')['calls']:
        purpose = receipt['raw_path'].split('/')[-1].removesuffix('.json')
        if purpose in groups:
            groups[purpose].append(_cost_proxy(read(folder / receipt['raw_path'])))
    return {key: sum(values, Decimal(0)) / len(values) for key, values in groups.items()}


def assessment():
    accounting = prefix()
    stages, reuse = [], []
    for stage in ('diagnostic', 'calibration'):
        cases, probes = references.cases(stage), references.probes(stage)
        # Probe candidates are compared offline only after four blind judgments;
        # none of the old candidate-conditioned review responses can be reused.
        receipts = [r for c in cases if (r := reusable_coverage(c, stage))]
        reuse.extend(receipts)
        means = _averages(stage)
        count = len(cases) + len(probes)
        full = Decimal(count * 2) * sum(means.values())
        new = full - sum((Decimal(r['cost_proxy_usd']) for r in receipts), Decimal(0))
        reservation = sum((evaluator.full_reservation(c['inputs']) for c in cases + probes), Decimal(0))
        reusable_ids = {r['case_id'] for r in receipts}
        reused_reservation = sum((transport.reserve(next(r['body']
            for r in evaluator.request_plan(c['inputs'])
            if r['judge'] == 'a' and r['purpose'] == 'coverage'))['reserved_usd']
            for c in cases if c['id'] in reusable_ids), Decimal(0))
        stages.append(dict(stage=stage, cases=len(cases), probes=len(probes),
            total_requests=count * 4, reusable_component_requests=len(receipts),
            new_requests=count * 4 - len(receipts),
            no_reuse_proxy_usd=str(full), with_reuse_proxy_usd=str(new),
            full_allowance_reservation_usd=str(reservation),
            new_request_reservation_usd=str(reservation - reused_reservation)))
    # Confirmation must be fresh and isolated. A high-effort V35 per-purpose
    # proxy is more relevant than the old V25 total; still not a future-cost bound.
    means = _averages('calibration')
    fresh = Decimal(16 * 2) * sum(means.values())
    stages.append(dict(stage='fresh_confirmation', cases=16, probes=0, total_requests=64,
                       reusable_component_requests=0, new_requests=64,
                       no_reuse_proxy_usd=str(fresh), with_reuse_proxy_usd=str(fresh),
                       full_allowance_reservation_usd=None, new_request_reservation_usd=None))
    remaining = CEILING - Decimal(accounting['spent_usd'])
    estimate = sum((Decimal(s['with_reuse_proxy_usd']) for s in stages), Decimal(0))
    no_reuse = sum((Decimal(s['no_reuse_proxy_usd']) for s in stages), Decimal(0))
    path = estimate + FINAL_FLOOR
    bindings = [references.PATH, FOLDER / 'v35-execution-stop.json',
                ROOT / 'scripts/structured_blind_evaluator_v1.py',
                ROOT / 'scripts/structured_blind_budget_v1.py']
    return dict(version=evaluator.VERSION, status='budget_blocked' if path > remaining else 'not_launch_ready',
        ceiling_usd=str(CEILING), accounted_usd=accounting['spent_usd'],
        retained_hold_usd='0.14820250', remaining_usd=str(remaining),
        final_launch_floor_usd=str(FINAL_FLOOR), qualification_headroom_usd=str(remaining - FINAL_FLOOR),
        stages=stages, reusable_components=reuse, stage_acceptances_reused=0,
        qualification_proxy_usd=str(estimate), no_reuse_qualification_proxy_usd=str(no_reuse),
        qualification_plus_final_floor_usd=str(path), estimated_gap_usd=str(max(Decimal(0), path-remaining)),
        final=dict(cases=60, required_successes=48, grader_requests=240,
            application_calls_maximum=60 * 32, fresh_suite_authored=False, cost_estimate_usd=None),
        caveats=[
            'Cost proxies reuse observed V35 token lengths without future cache discounts; new interpretation output may cost more.',
            'Four blind requests replace three anchored requests; final launch floor is not a completion guarantee.',
            'Exact future confirmation/final request lengths and full reservations are unknown before freeze and isolated authoring.',
            'Component reuse does not carry over stage acceptance, source review or claims/reviewer qualification.',
            'No live successor runner, paid pilot, retry, cap reduction or top-up is included.',
        ], provider_retries=0, claims_output_cap=8192, coverage_output_cap=4096,
        source_bindings={p.relative_to(ROOT).as_posix(): digest(p) for p in bindings},
        ledger_bindings=accounting['ledger_sha256'], paid_execution_authorized=False,
        decision='No paid execution; preserve remaining funds, all release gates and V4.')


if __name__ == '__main__':
    value = assessment()
    if sys.argv[1:] == ['--check']:
        if read(REPORT) != value:
            raise SystemExit('Saved offline assessment differs')
        print('Offline component reuse and budget replay match: ' + value['status'])
    elif sys.argv[1:]:
        raise SystemExit('Only --check or no arguments; no paid execution supported')
    else:
        print(json.dumps(value, indent=2))
