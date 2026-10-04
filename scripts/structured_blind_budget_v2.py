"""Offline replacement USD6.49 balance; no provider or paid execution command."""
from decimal import Decimal
import json
import sys

from scripts import structured_blind_budget_v1 as prior
from scripts.bounded_redesign_run import read, digest

AUTHORIZATION = prior.FOLDER / 'structured-blind-v1/authorization-649.json'
REPORT = prior.FOLDER / 'structured-blind-v1/budget-649.json'


def assessment():
    authorization = read(AUTHORIZATION)
    old = prior.assessment()
    if old != read(prior.REPORT):
        raise ValueError('Prior preparation or spending changed; reconcile before any new decision')
    if (authorization['user_answer'] != '6.49 usd'
            or authorization['remaining_balance_including_hold_usd'] != '6.49'
            or authorization['previous_remainder_added'] is not False
            or authorization['final_launch_floor_usd'] != '4.50'
            or authorization['provider_retries'] != 0
            or authorization['prior_assessment_sha256'] != digest(prior.REPORT)
            or authorization['prior_stop_sha256'] != digest(prior.FOLDER / 'v35-execution-stop.json')):
        raise ValueError('Replacement authorization changed')
    accounted = Decimal(old['accounted_usd'])
    hold = Decimal(old['retained_hold_usd'])
    confirmed = accounted - hold
    ceiling = confirmed + Decimal(authorization['remaining_balance_including_hold_usd'])
    remaining = ceiling - accounted
    expected = dict(confirmed_prior_spend_usd=confirmed, retained_hold_usd=hold,
                    accounted_prior_usd=accounted, total_ceiling_usd=ceiling,
                    new_call_headroom_usd=remaining)
    if any(Decimal(authorization[k]) != v for k, v in expected.items()):
        raise ValueError('Replacement arithmetic differs; never add the old remainder')
    result = dict(old)
    required = Decimal(old['qualification_plus_final_floor_usd'])
    result.update(version='structured-blind-budget.v2', ceiling_usd=str(ceiling),
        remaining_usd=str(remaining), qualification_headroom_usd=str(remaining - prior.FINAL_FLOOR),
        estimated_gap_usd=str(max(Decimal(0), required - remaining)),
        status='budget_blocked' if required > remaining else 'not_launch_ready',
        authorization_sha256=digest(AUTHORIZATION), prior_assessment_sha256=digest(prior.REPORT),
        paid_execution_authorized=False)
    return result


if __name__ == '__main__':
    value = assessment()
    if sys.argv[1:] == ['--check']:
        if value != read(REPORT):
            raise SystemExit('Saved replacement assessment differs')
        print('Replacement USD6.49 assessment matches: ' + value['status'])
    elif sys.argv[1:]:
        raise SystemExit('Only --check or no arguments; paid execution is unavailable')
    else:
        print(json.dumps(value, indent=2))
