"""Continue the same USD 10 envelope without rewriting rejected-job evidence."""
from copy import deepcopy
from decimal import Decimal
from scripts.quality_cost_control import ROOT, FOLDER as ORIGINAL, read, digest, live_policy as original_policy
from scripts.quality_batch_transport import SpendJournal as OriginalJournal

POLICY = ORIGINAL / 'policy-v2.json'
FOLDER = ORIGINAL / 'continuation-v2'


def bound_file(binding):
    path = (ROOT / binding['path']).resolve()
    if not path.is_relative_to(ROOT) or digest(path) != binding['sha256']:
        raise ValueError('Continuation evidence changed')
    return path


def live_policy(path=POLICY):
    policy, ceiling = original_policy(path)
    predecessor = read(bound_file(policy['predecessor_policy']))
    if Decimal(predecessor['additional_ceiling_usd']) != ceiling:
        raise ValueError('Continuation cannot increase the approved ceiling')
    old = read(bound_file(policy['predecessor_journal']))
    if old['policy_sha256'] != policy['predecessor_policy']['sha256']:
        raise ValueError('Predecessor policy binding changed')
    resolution = read(bound_file(policy['batch_rejection_resolution']))
    if resolution.get('status') != 'resolved_no_batch' or resolution.get('provider_error_code') != 'billing_hard_limit_reached':
        raise ValueError('Batch rejection remains unresolved')
    for name, expected in resolution['evidence_sha256'].items():
        bound_file({'path': name, 'sha256': expected})
    audit = read(ORIGINAL / 'batch-rejection-provider-audit.json')
    interruption = read(ROOT / 'data/evaluation/quality-completion-v1/confirmation-v18-batch-interruption.json')
    if (not audit.get('complete') or audit.get('matches') != [] or audit.get('exception_type')
            or not audit.get('pages') or any(p['data'] for p in audit['pages'])
            or interruption.get('http_status') != 400
            or interruption.get('provider_error_code') != 'billing_hard_limit_reached'):
        raise ValueError('No-batch audit does not establish the rejected outcome')
    rows = list(old['entries'].values())
    if (len(rows) != 1 or rows[0]['status'] != 'unknown'
            or rows[0]['result_sha256'] != interruption['evidence_sha256']['data/evaluation/quality-completion-v1/confirmation-v18-batch-01/initial/state.json']
            or Decimal(rows[0]['accounted_usd']) != Decimal(resolution['retained_reservation_usd'])):
        raise ValueError('Retained reservation differs from interrupted attempt')
    return policy, ceiling


def retained_entries():
    policy, _ = live_policy()
    old = read(bound_file(policy['predecessor_journal']))
    entries = deepcopy(old['entries'])
    for row in entries.values():
        # Accounting is settled conservatively at the full reservation, NOT priced usage.
        row.update(status='settled', accounting_basis='resolved_rejection_full_reservation_retained',
                   resolution_sha256=policy['batch_rejection_resolution']['sha256'])
    return entries


class SpendJournal(OriginalJournal):
    def __init__(self, folder=FOLDER, policy_path=POLICY):
        super().__init__(folder, policy_path)

    def load(self):
        retained = retained_entries()
        data = super().load()
        if not self.path.exists():
            data['entries'] = retained
        elif any(data['entries'].get(k) != v for k, v in retained.items()):
            raise ValueError('Retained reservation removed or changed')
        return data

    def finish(self, identity, amount, evidence_hash, *, uncertain=False):
        if identity in retained_entries():
            raise ValueError('Retained historical reservation is immutable')
        return super().finish(identity, amount, evidence_hash, uncertain=uncertain)
