"""User-authorized conservative carry-forward of one still-unknown request.

Historical evidence is immutable. Only its accounting disposition is settled in
this successor; provider outcome remains explicitly unknown. New unknown calls
still stop all dependent execution.
"""
from copy import deepcopy
from decimal import Decimal
from scripts import quality_cost_standard as prior
from scripts.quality_cost_control import ROOT, read, digest
from scripts.quality_batch_transport import SpendJournal as BaseJournal

FOLDER = ROOT / 'data/evaluation/phase73-successor-v1'
POLICY = FOLDER / 'policy.json'
AUTHORIZATION = FOLDER / 'authorization.json'
PREFIX = FOLDER / 'initial-spend.json'
OLD_SNAPSHOT = ROOT / 'data/evaluation/current-runtime-v4/run/additional-spend.json'
OLD_AUDIT = ROOT / 'data/evaluation/phase73-continuation-v1/audit.json'


def live_policy(path=POLICY):
    _, ceiling = prior.live_policy()
    policy, approval, audit = read(path), read(AUTHORIZATION), read(OLD_AUDIT)
    if (policy['authorization_sha256'] != digest(AUTHORIZATION)
            or policy['additional_ceiling_usd'] != str(ceiling)
            or policy['predecessor_policy_sha256'] != digest(prior.POLICY)
            or policy['predecessor_snapshot_sha256'] != digest(OLD_SNAPSHOT)
            or policy['continuation_audit_sha256'] != digest(OLD_AUDIT)
            or approval['decision'] != 'retain_one_unknown_reservation_and_continue'
            or approval['unknown_request_sha256'] != audit['unknown_request_sha256']
            or approval['retained_reservation_usd'] != audit['unknown_reservation_usd']
            or approval['additional_ceiling_usd'] != str(ceiling)
            or approval['retries_authorized'] is not False
            or approval['scoring_changes_authorized'] is not False):
        raise ValueError('Specific carry-forward authorization or ceiling changed')
    if prior.SpendJournal().load() != read(OLD_SNAPSHOT):
        raise ValueError('Historical shared journal changed after transition')
    for name, expected in audit['evidence_sha256'].items():
        target = (ROOT / name).resolve()
        if not target.is_relative_to(ROOT) or digest(target) != expected:
            raise ValueError('Interrupted audit evidence changed')
    return policy, ceiling


def retained_entries():
    live_policy()
    audit = read(OLD_AUDIT)
    entries = deepcopy(read(OLD_SNAPSHOT)['entries'])
    identity = audit['unknown_shared_identity']
    unknown = {key for key, row in entries.items() if row['status'] != 'settled'}
    if unknown != {identity}:
        raise ValueError('Authorization covers exactly one historical unknown')
    row = entries[identity]
    if (row['status'] != 'unknown' or row['accounted_usd'] != row['reserved_usd']
            or row['reserved_usd'] != audit['unknown_reservation_usd']
            or row['evidence_sha256'] != audit['unknown_request_sha256']):
        raise ValueError('Historical unknown reservation changed')
    row.update(status='settled', provider_outcome='unknown',
               accounting_basis='user_authorized_full_reservation_retained',
               authorization_sha256=digest(AUTHORIZATION))
    return entries


class SpendJournal(BaseJournal):
    def __init__(self, folder=FOLDER, policy_path=POLICY):
        super().__init__(folder, policy_path)

    def load(self):
        retained = retained_entries()
        data = super().load()
        if not self.path.exists():
            data['entries'] = retained
        elif any(data['entries'].get(k) != v for k, v in retained.items()):
            raise ValueError('Immutable carry-forward accounting changed')
        return data

    def reserve(self, identity, amount, evidence_hash):
        live_policy(self.policy_path)
        return super().reserve(identity, amount, evidence_hash)

    def finish(self, identity, amount, evidence_hash, *, uncertain=False):
        if identity in retained_entries():
            raise ValueError('Historical reservation cannot be settled again or released')
        return super().finish(identity, amount, evidence_hash, uncertain=uncertain)
