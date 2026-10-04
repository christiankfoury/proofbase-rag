"""V35 replacement balance; original unknown request remains fully held."""
from decimal import Decimal
from scripts.conversation_continuation import ROOT, FOLDER, ORIGINAL
from scripts.bounded_redesign_run import read, digest, response_charge

CEILING = Decimal('16.77047526')
FINAL_FLOOR = Decimal('4.50')
PRIOR_AUTHORIZATION = FOLDER / 'cad1311-authorization.json'
AUTHORIZATION = FOLDER / 'v35-execution-authorization.json'
RECOVERY_AUTHORIZATION = FOLDER / 'network-recovery-authorization.json'


def prefix():
    authorization = read(AUTHORIZATION)
    if (authorization['user_answer'] != 'there is 7.60 usd left into the api'
            or authorization['total_ceiling_usd'] != str(CEILING)
            or authorization['remaining_balance_including_hold_usd'] != '7.60'
            or authorization['retained_hold_usd'] != '0.14820250'
            or authorization['confirmed_prior_spend_usd'] != '9.17047526'
            or authorization['previous_remainder_added'] is not False
            or authorization['final_launch_floor_usd'] != str(FINAL_FLOOR)
            or authorization['provider_retries'] != 0
            or authorization['prior_authorization_sha256'] != digest(PRIOR_AUTHORIZATION)):
        raise ValueError('V35 replacement authorization changed')
    if Decimal(authorization['confirmed_prior_spend_usd']) + Decimal(authorization['remaining_balance_including_hold_usd']) != CEILING:
        raise ValueError('Never add the historical remainder twice')
    for path, expected in authorization['prefix']['ledger_sha256'].items():
        if digest(ROOT / path) != expected:
            raise ValueError('Authorized historical ledger changed')
    budget = read(PRIOR_AUTHORIZATION)
    if (budget['user_answer'] != 'Yes I approve' or budget['total_ceiling_usd'] != '14.88536776'
            or budget['remaining_budget_including_hold_usd'] != '8.00'
            or budget['previous_remainder_added'] is not False
            or budget['recovery_authorization_sha256'] != digest(RECOVERY_AUTHORIZATION)):
        raise ValueError('Budget amendment changed')
    approval = read(RECOVERY_AUTHORIZATION)
    allowed = ROOT / approval['retained_ledger_path']
    if (approval['user_answer'] != 'Yes I approve'
            or approval['total_ceiling_usd'] != '12.50'
            or approval['maximum_recovery_attempts'] != 1
            or digest(allowed) != approval['retained_ledger_sha256']):
        raise ValueError('Recovery authorization or retained evidence changed')
    if digest(ORIGINAL) != read(FOLDER / 'authorization.json')['prior_ledger_sha256']:
        raise ValueError('Authorized initial ledger changed')
    total = Decimal(0)
    files = {}
    for path in [ORIGINAL] + sorted(FOLDER.glob('*/run/api-ledger.json')):
        ledger = read(path)
        if path == allowed:
            if not ledger['unknown_outcome'] or not ledger['stopped'] or len(ledger['calls']) != 1:
                raise ValueError('Retained failure changed')
            row = ledger['calls'][0]
            raw_path = path.parent / row['raw_path']
            raw = read(raw_path)
            amount = Decimal(approval['retained_reservation_usd'])
            if (row['status'] != 'unknown' or raw['response'] is not None
                    or digest(raw_path) != row['raw_sha256']
                    or Decimal(row['accounted_usd']) != amount
                    or Decimal(row['reserved_usd']) != amount):
                raise ValueError('Full unknown reservation must remain held')
            total += amount
        else:
            if ledger['unknown_outcome'] or any(r['status'] != 'completed' for r in ledger['calls']):
                raise ValueError('Unsettled prior call; no continuation')
            for row in ledger['calls']:
                raw_path = path.parent / row['raw_path']
                raw = read(raw_path)
                if digest(raw_path) != row['raw_sha256'] or raw['status'] != 'received':
                    raise ValueError('Historical receipt changed')
                amount = response_charge(raw['response'], raw['request']['model'])
                if amount != Decimal(row['accounted_usd']):
                    raise ValueError('Historical cost differs')
                total += amount
        files[path.relative_to(ROOT).as_posix()] = digest(path)
    if total > CEILING:
        raise ValueError('Budget already exceeded')
    # Existing harness field denotes all accounted spending, including this hold.
    return dict(spent_usd=str(total), ledger_sha256=files)


def stage_budget(stage):
    """Planning estimates gate launches; each request also protects the final floor."""
    estimates = {'diagnostic': Decimal('2.48104925'),
                 'calibration': Decimal('1.72120675'),
                 'confirmation': Decimal('0.52179550'), 'final': Decimal(0)}
    if stage not in estimates:
        raise ValueError('Unknown stage')
    spending = prefix()
    remaining = CEILING - Decimal(spending['spent_usd'])
    required = estimates[stage] + FINAL_FLOOR
    if remaining < required:
        raise ValueError('Remaining whole path is not credibly funded')
    return dict(stage=stage, accounted_usd=spending['spent_usd'], remaining_usd=str(remaining),
                remaining_qualification_estimate_usd=str(estimates[stage]),
                final_launch_floor_usd=str(FINAL_FLOOR), estimated_buffer_usd=str(remaining-required),
                estimate_not_guarantee=True, authorization_sha256=digest(AUTHORIZATION))
