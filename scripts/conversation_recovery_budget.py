"""One explicitly authorized transport exception; its full reservation stays held."""
from decimal import Decimal
from scripts.conversation_continuation import ROOT, FOLDER, CEILING, ORIGINAL
from scripts.bounded_redesign_run import read, digest, response_charge

AUTHORIZATION = FOLDER / 'network-recovery-authorization.json'


def prefix():
    approval = read(AUTHORIZATION)
    allowed = ROOT / approval['retained_ledger_path']
    if (approval['user_answer'] != 'Yes I approve'
            or approval['total_ceiling_usd'] != str(CEILING)
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
