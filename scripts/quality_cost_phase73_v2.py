"""CAD-authorized successor allowance; immutable prior accounting is retained."""
from decimal import Decimal
from scripts import quality_cost_phase73 as previous
from scripts.quality_cost_control import ROOT, read, digest
from scripts.quality_batch_transport import SpendJournal as BaseJournal

FOLDER = ROOT / 'data/evaluation/phase73-successor-v2'
POLICY = FOLDER / 'policy.json'
AUTHORIZATION = FOLDER / 'authorization.json'
PREFIX = FOLDER / 'initial-spend.json'
OLD_SNAPSHOT = ROOT / 'data/evaluation/current-runtime-v5/run/additional-spend.json'


def live_policy(path=POLICY):
    previous.live_policy()
    policy, approval, old = read(path), read(AUTHORIZATION), read(OLD_SNAPSHOT)
    prior = sum((Decimal(r['accounted_usd']) for r in old['entries'].values()), Decimal(0))
    allowance = Decimal(approval['new_allowance_usd'])
    if (policy['authorization_sha256'] != digest(AUTHORIZATION)
            or policy['predecessor_policy_sha256'] != digest(previous.POLICY)
            or policy['predecessor_snapshot_sha256'] != digest(OLD_SNAPSHOT)
            or previous.SpendJournal().load() != old
            or prior != Decimal('9.87823685')
            or approval['decision'] != 'continue_with_cad_balance'
            or Decimal(approval['available_cad']) != Decimal('14.32')
            or allowance != Decimal('9.00')
            or Decimal(approval['budget_cad_per_usd']) != Decimal('1.59')
            or allowance * Decimal('1.59') > Decimal('14.32')
            or approval['retries_authorized'] is not False
            or approval['scoring_changes_authorized'] is not False
            or policy['transport'] != 'standard' or policy['provider_retries'] != 0
            or Decimal(policy['additional_ceiling_usd']) != prior + allowance):
        raise ValueError('CAD authorization, conservative cap or prior accounting changed')
    return policy, prior + allowance


class SpendJournal(BaseJournal):
    def __init__(self, folder=FOLDER, policy_path=POLICY):
        super().__init__(folder, policy_path)

    def load(self):
        data = super().load()
        retained = read(OLD_SNAPSHOT)['entries']
        if not self.path.exists():
            data['entries'] = retained
        elif any(data['entries'].get(k) != v for k, v in retained.items()):
            raise ValueError('Historical accounting changed')
        return data

    def reserve(self, identity, amount, evidence_hash):
        live_policy(self.policy_path)
        return super().reserve(identity, amount, evidence_hash)

    def finish(self, identity, amount, evidence_hash, *, uncertain=False):
        if identity in read(OLD_SNAPSHOT)['entries']:
            raise ValueError('Historical accounting cannot be settled again')
        return super().finish(identity, amount, evidence_hash, uncertain=uncertain)
