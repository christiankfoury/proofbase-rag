"""Offline whole-path reconciliation. No client, credential access or paid pilot."""
from decimal import Decimal
import json
import sys
from scripts import conversation_ordering_v2 as references
from scripts import quality_eval_transport_v35 as transport
from scripts.conversation_cad1311_budget import CEILING, prefix
from scripts.bounded_redesign_run import read, digest

FOLDER = references.legacy.FOLDER
REPORT = FOLDER / 'ordering-contract-v2' / 'completion-budget.json'
FLOOR = Decimal('4.50')


def assessment():
    accounting = prefix()  # Reconcile all receipts, including the original hold.
    accounted = Decimal(accounting['spent_usd'])
    diagnostic_path = FOLDER / 'grader-v34-diagnostic/report.json'
    calibration_path = FOLDER / 'grader-v34-calibration/report.json'
    confirmation_path = FOLDER / 'grader-v25-confirmation/report.json'
    diagnostic, calibration, confirmation = map(read, (diagnostic_path, calibration_path, confirmation_path))
    # The interrupted calibration includes 22 complete three-request cases, no
    # probes. Extrapolate its average per request to every successor case/probe.
    # This is an empirical planning proxy, not a bound or promise for v35.
    if (diagnostic['count'], diagnostic['calls'], calibration['count'], calibration['calls'],
            confirmation['count'], confirmation['calls']) != (16, 51, 22, 66, 16, 48):
        raise ValueError('Historical estimate inputs changed')
    stages = []
    for name in ('diagnostic', 'calibration'):
        cases, probes = references.cases(name), references.probes(name)
        calls = len(cases) * 3 + len(probes)
        reservation = sum((transport.case_bound(c['inputs']) for c in cases), Decimal(0))
        reservation += sum((transport.reserve(transport.review_request(c['inputs'], c['candidate']))['reserved_usd']
                            for c in probes), Decimal(0))
        estimate = (Decimal(diagnostic['cost_usd']) if name == 'diagnostic' else
                    Decimal(calibration['cost_usd']) / calibration['calls'] * calls)
        stages.append(dict(stage=name, cases=len(cases), probes=len(probes), calls=calls,
                           empirical_estimate_usd=str(estimate), full_allowance_reservation_usd=str(reservation)))
    stages.append(dict(stage='fresh_confirmation', cases=16, probes=0, calls=48,
                       empirical_estimate_usd=confirmation['cost_usd'], full_allowance_reservation_usd=None))
    qualification = sum((Decimal(s['empirical_estimate_usd']) for s in stages), Decimal(0))
    remaining = CEILING - accounted
    path_estimate = qualification + FLOOR
    paths = [diagnostic_path, calibration_path, confirmation_path, references.PATH,
             references.legacy.ROOT / 'scripts/quality_eval_contract_v35.py',
             references.legacy.ROOT / 'scripts/quality_eval_transport_v35.py']
    return dict(version='completion-budget.v2', status='blocked' if path_estimate > remaining else 'requires_fresh_preflight',
                ceiling_usd=str(CEILING), accounted_usd=str(accounted), retained_hold_usd='0.14820250',
                remaining_usd=str(remaining), final_launch_floor_usd=str(FLOOR),
                qualification_headroom_usd=str(remaining - FLOOR), stages=stages,
                qualification_estimate_usd=str(qualification),
                qualification_plus_final_floor_usd=str(path_estimate),
                estimated_gap_usd=str(max(Decimal(0), path_estimate - remaining)),
                final=dict(cases=60, required_successes=48, grader_calls=180,
                           application_calls_maximum=60 * 32, cost_estimate_usd=None,
                           full_allowance_reservation_usd=None, suite_authored=False),
                caveats=[
                    'Prior confirmation used an older grader; its cost is an optimistic proxy, not qualification evidence.',
                    'Final USD4.50 is a mandatory launch floor, not a guaranteed full-run cost or conservative reservation.',
                    'Fresh suites are not authored before readiness/freeze; exact future input costs are unknown.',
                    'No paid focus, retry, repair, pilot or independent-review experiment is included or funded.',
                    'Successor prompt length and reasoning costs may increase spending; no cache discount is assumed for future requests.',
                ],
                decision='No paid execution. Preserve funds and V4; candidate acceptance remains blocked.',
                provider_retries=0, output_caps=transport.CAPS, paid_execution_authorized_by_report=False,
                source_bindings={p.relative_to(references.legacy.ROOT).as_posix(): digest(p) for p in paths},
                ledger_bindings=accounting['ledger_sha256'])


if __name__ == '__main__':
    value = assessment()
    if sys.argv[1:] == ['--check']:
        if read(REPORT) != value:
            raise SystemExit('Saved whole-path budget differs from receipt replay')
        print('Whole-path budget matches; ' + value['status'])
    elif sys.argv[1:]:
        raise SystemExit('Use no arguments or --check; this tool cannot execute paid work')
    else:
        print(json.dumps(value, indent=2))
