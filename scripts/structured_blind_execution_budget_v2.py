"""One authorized successor within the existing ceiling; no additional funds."""
from decimal import Decimal
from scripts import structured_blind_execution_budget as previous
from scripts.bounded_redesign_run import read, digest

ROOT, FOLDER = previous.ROOT, previous.FOLDER
CEILING, FINAL_FLOOR = previous.CEILING, previous.FINAL_FLOOR
AUTHORIZATION = FOLDER/'structured-blind-v2/authorization.json'
COUNTS = {'diagnostic': (140, 102), 'calibration': (102, 80),
          'confirmation': (32, 32), 'final': (0, 0)}


def estimates():
    ledger = read(FOLDER/'structured-blind-diagnostic/run/api-ledger.json')
    rates = {}
    for purpose in ('claims', 'coverage'):
        usages = [read(FOLDER/'structured-blind-diagnostic/run'/c['raw_path'])['response']['usage']
                  for c in ledger['calls'] if purpose in c['raw_path']]
        rates[purpose] = sum((Decimal(u['prompt_tokens'])*Decimal('.0000025') +
                              Decimal(u['completion_tokens'])*Decimal('.000015')
                              for u in usages), Decimal(0))/len(usages)
    return {stage: str(a*rates['claims']+b*rates['coverage'])
            for stage, (a, b) in COUNTS.items()}


def prefix():
    approval = read(AUTHORIZATION)
    if (approval['user_answer'] != 'lets do this' or approval['total_ceiling_usd'] != str(CEILING)
        or approval['previous_remainder_added'] is not False or approval['provider_retries'] != 0
        or approval['retained_hold_usd'] != '0.14820250'
        or approval['final_launch_floor_usd'] != str(FINAL_FLOOR)
        or approval['prior_authorization_sha256'] != digest(previous.AUTHORIZATION)
        or approval['baseline_assessment_sha256'] != digest(FOLDER/'structured-blind-v1/offline-assessment.json')
        or approval['observed_ledger_sha256'] != digest(FOLDER/'structured-blind-diagnostic/run/api-ledger.json')
        or approval['remaining_qualification_estimates_usd'] != estimates()):
        raise ValueError('Successor authorization or planning evidence changed')
    for path, expected in approval['prefix']['ledger_sha256'].items():
        if digest(ROOT/path) != expected: raise ValueError('Authorized starting evidence changed')
    return previous.prefix()


def stage_budget(stage):
    spending = prefix()
    estimate = Decimal(estimates()[stage])
    remaining = CEILING-Decimal(spending['spent_usd'])
    required = estimate+FINAL_FLOOR
    if remaining < required: raise ValueError('Remaining whole path is not credibly funded')
    return dict(stage=stage, accounted_usd=spending['spent_usd'], remaining_usd=str(remaining),
                remaining_qualification_estimate_usd=str(estimate), final_launch_floor_usd=str(FINAL_FLOOR),
                estimated_buffer_usd=str(remaining-required), estimate_not_guarantee=True,
                authorization_sha256=digest(AUTHORIZATION))
