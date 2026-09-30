"""Cache-aware estimates and a shared additional-spend envelope; no network."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/evaluation/quality-cost-control-v1'
POLICY = FOLDER / 'policy.json'
MODEL = 'gpt-5.4-2026-03-05'
# Official model/Batch documentation checked 2026-09-30. USD per million.
RATES = {'standard': ('2.50', '0.25', '15'), 'batch': ('1.25', '0.125', '7.50')}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def charge(response, mode='standard'):
    if response.get('model') != MODEL:
        raise ValueError('Unpriced model snapshot')
    usage = response['usage']
    it, ot = usage['prompt_tokens'], usage['completion_tokens']
    cached = (usage.get('prompt_tokens_details') or {}).get('cached_tokens', 0)
    if (any(type(n) is not int for n in (it, ot, cached))
            or not 0 <= cached <= it <= 272000 or ot < 0):
        raise ValueError('Invalid usage or long-context price tier')
    ri, rc, ro = map(Decimal, RATES[mode])
    return ((it - cached) * ri + cached * rc + ot * ro) / 1_000_000


def report_history():
    """A derived report, never a rewrite or reduction of the immutable ledger."""
    folder = ROOT / 'data/evaluation/quality-completion-v1'
    path = folder / 'api-ledger.json'
    ledger = read(path)
    start = ledger['reconciliation']['historical_calls']
    full = adjusted = retained = Decimal(0)
    cached = completed = 0
    stages = {}
    for row in ledger['calls'][start:]:
        if row['status'] != 'completed':
            retained += Decimal(row['charged_usd'])
            continue
        raw_path = (folder / row['raw_path']).resolve()
        if not raw_path.is_relative_to(folder.resolve()) or digest(raw_path) != row['raw_sha256']:
            raise ValueError('Historical raw evidence changed')
        raw = read(raw_path)
        request_hash = hashlib.sha256(json.dumps(raw['request'], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if (raw['status'] != 'received' or request_hash != row['request_sha256']
                or raw['request']['model'] != MODEL):
            raise ValueError('Historical request changed')
        response = raw['response']
        value = charge(response)
        usage = response['usage']
        conservative = (usage['prompt_tokens'] * Decimal('2.5') + usage['completion_tokens'] * Decimal('15')) / 1_000_000
        if conservative != Decimal(row['charged_usd']):
            raise ValueError('Historical full-price estimate changed')
        full += conservative
        adjusted += value
        cached += (usage.get('prompt_tokens_details') or {}).get('cached_tokens', 0)
        completed += 1
        stage = row['raw_path'].split('/')[0]
        group = stages.setdefault(stage, {'calls': 0, 'full_price_usd': Decimal(0), 'cache_aware_usd': Decimal(0)})
        group['calls'] += 1
        group['full_price_usd'] += conservative
        group['cache_aware_usd'] += value
    floor = Decimal(ledger['reconciliation']['conservative_spent_usd'])
    return {'ledger_sha256': digest(path), 'completed_queue_calls': completed,
            'historical_floor_usd': str(floor), 'queue_full_price_usd': str(full),
            'queue_cache_aware_usd': str(adjusted), 'cached_input_tokens': cached,
            'cache_discount_estimate_usd': str(full - adjusted),
            'cumulative_estimate_with_unchanged_history_usd': str(floor + adjusted),
            'unresolved_reservation_usd': str(retained),
            'stages': {k: {n: str(v) if isinstance(v, Decimal) else v for n, v in d.items()} for k, d in stages.items()},
            'invoice_verified': False,
            'limitation': 'Derived token-price estimate, not an invoice. Earlier historical floor remains conservative; unresolved reservations are separate. No historical ledger was changed.'}


def live_policy(path=POLICY):
    policy = read(path)
    amount = policy.get('additional_ceiling_usd')
    if amount is None:
        raise ValueError('Additional spending ceiling has not been selected')
    ceiling = Decimal(amount)
    if not ceiling.is_finite() or ceiling <= 0:
        raise ValueError('Invalid additional spending ceiling')
    if not policy.get('external_service_ready'):
        raise ValueError('Provider project spending limit remains unresolved')
    # A user budget selection does not clear an uncertain historical call.
    resolution = policy.get('prior_outcome_resolution')
    if not resolution:
        raise ValueError('Prior rejected/unknown call requires an audited resolution')
    target = (ROOT / resolution['path']).resolve()
    if not target.is_relative_to(ROOT) or digest(target) != resolution['sha256']:
        raise ValueError('Prior outcome resolution changed')
    record = read(target)
    if (record.get('status') != 'resolved_no_generation'
            or record.get('baseline_ledger_sha256') != policy['baseline_ledger_sha256']
            or record.get('provider_error_code') != 'project_spend_limit_exceeded'):
        raise ValueError('Prior outcome resolution does not establish a rejected request')
    if not record.get('evidence_sha256'):
        raise ValueError('Prior resolution lacks preserved evidence')
    for name, expected in record['evidence_sha256'].items():
        evidence = (ROOT / name).resolve()
        if not evidence.is_relative_to(ROOT) or digest(evidence) != expected:
            raise ValueError('Prior rejection evidence changed')
    prior = (ROOT / policy['baseline_ledger_path']).resolve()
    if not prior.is_relative_to(ROOT) or digest(prior) != policy['baseline_ledger_sha256']:
        raise ValueError('Cost baseline changed')
    return policy, ceiling
