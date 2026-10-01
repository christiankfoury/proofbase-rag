"""Complete successor accounting with the specifically authorized timeout retained."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from scripts import quality_confirmation_standard_v23 as confirmation
from scripts import quality_cost_phase73_v2 as spending
from scripts.quality_cost_control import ROOT, read, digest, charge
from scripts.quality_completion_ledger import Ledger as LegacyLedger
from scripts.quality_standard_grading import audit as audit_standard

VERSION = 'phase73-successor-accounting-prefix.v2'
ORIGINAL = ROOT / 'data/evaluation/current-runtime-v5'


def retained_prefix():
    from scripts.phase73_v5_history import PriorLedger as V5Prior
    from scripts.report_phase73_v5 import SettledSnapshot, audit_calls, audit_additional_spend
    from scripts.report_phase73_v5_capture import snapshot
    spending.live_policy()
    inventory = snapshot(ORIGINAL)
    if inventory != read(ORIGINAL/'capture-publication.json'):
        raise ValueError('Original capture inventory changed')
    ledger = SettledSnapshot(ORIGINAL/'run/api-ledger.json')
    prior = V5Prior(ORIGINAL/'prior-ledger.json')
    audit_additional_spend(audit_calls(ledger))
    if len(ledger.data['calls']) != 3474 or ledger.spent != Decimal('20.73393762'):
        raise ValueError('Original cumulative history changed')
    paths = {ORIGINAL/'capture-publication.json', spending.AUTHORIZATION, spending.POLICY,
             spending.PREFIX, spending.OLD_SNAPSHOT}
    paths.update(ORIGINAL/name for name in inventory['run_artifacts_sha256'])
    paths.update(ORIGINAL/name for name in inventory['supporting_artifacts_sha256'])
    retained = read(spending.OLD_SNAPSHOT)['entries']
    initial = read(spending.PREFIX)
    if initial['entries'] != retained or initial['policy_sha256'] != digest(spending.POLICY):
        raise ValueError('Successor initial accounting differs')
    return deepcopy(ledger.data['calls']), ledger.spent, sorted(prior.resolved_rejections), paths, retained


def standard_stages():
    dev = confirmation.previous.development
    return [(dev.prior.output('diagnostic'), 9), (dev.output('diagnostic'), 27),
            (dev.output('calibration'), 75), (confirmation.OUT, 48)]


def build_prefix(*, qualify=True):
    if qualify:
        from scripts.report_phase73_v5 import replay
        replay()
        confirmation.readiness()
    calls, floor, resolved, paths, retained = retained_prefix()
    report, gate = read(confirmation.REPORT), read(confirmation.GATE)
    if (gate.get('status') != 'approved' or gate.get('unresolved_semantic_findings') != 0
            or gate.get('human_adjudication') is not False
            or gate.get('report_sha256') != digest(confirmation.REPORT)
            or gate.get('source_review_sha256') != digest(confirmation.REVIEW)
            or report.get('status') != 'complete' or report.get('matched') != 16
            or report.get('count') != 16 or report.get('calls') != 48):
        raise ValueError('Qualified fresh confirmation required')
    paths.update({confirmation.REPORT, confirmation.GATE, confirmation.REVIEW,
                  confirmation.FREEZE, confirmation.SEAL})
    expected = deepcopy(retained)
    total = Decimal(0)
    for stage, count in standard_stages():
        folder = stage/'requests'
        history = read(folder/'calls.json')
        snapshot = read(stage/'additional-spend.json')
        if (len(history['calls']) != count or history['policy_sha256'] != digest(spending.POLICY)
                or snapshot['policy_sha256'] != digest(spending.POLICY)):
            raise ValueError('Incomplete successor standard history')
        bodies = []
        for row in history['calls']:
            path = (folder/row['path']).resolve()
            if not path.is_relative_to(folder.resolve()):
                raise ValueError('Unsafe standard evidence path')
            bodies.append(read(path)['request'])
        audit_standard(folder, bodies, SimpleNamespace(policy_path=spending.POLICY,
                                                       load=lambda: snapshot))
        paths.update(p for p in stage.rglob('*') if p.is_file())
        for row in history['calls']:
            path = (folder/row['path']).resolve()
            if (not path.is_relative_to(folder.resolve()) or row['status'] != 'completed'
                    or row['identity'] in expected):
                raise ValueError('Unknown, duplicate or unsafe successor request')
            raw = read(path)
            cost = charge(raw['response'])
            if digest(path) != row['raw_sha256'] or cost != Decimal(row['charged_usd']):
                raise ValueError('Successor raw cost changed')
            entry = snapshot['entries'][row['identity']]
            if (entry['status'] != 'settled' or Decimal(entry['accounted_usd']) != cost
                    or entry['result_sha256'] != row['raw_sha256']
                    or entry['reserved_usd'] != row['reserved_usd']):
                raise ValueError('Successor shared accounting differs')
            expected[row['identity']] = entry
            total += cost
            calls.append({'call_index':len(calls), 'status':'completed',
                          'operation':'grader_standard', 'model':raw['response']['model'],
                          'charged_usd':str(cost), 'raw_path':path.relative_to(ROOT).as_posix(),
                          'raw_sha256':digest(path), 'standard_identity':row['identity']})
        if snapshot['entries'] != expected:
            raise ValueError('Complete successor spending prefix differs')
    accounted = sum((Decimal(r['accounted_usd']) for r in expected.values()), Decimal(0))
    if accounted != Decimal(report['additional_accounted_usd']):
        raise ValueError('Confirmation shared total differs')
    return {'version':VERSION, 'calls':calls, 'resolved_rejection_indices':resolved,
            'prior_spend_usd':str(floor+total), 'additional_accounted_usd':str(accounted),
            'historical_timeout_provider_outcome':'unknown',
            'historical_timeout_accounting_basis':'user_authorized_full_reservation_retained',
            'invoice_verified':False,
            'sources_sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(paths)}}


class PriorLedger:
    def __init__(self, path):
        self.data = read(Path(path))
        if self.data.get('version') != VERSION:
            legacy = LegacyLedger(path)
            self.spent = legacy.spent
            self.resolved_rejections = set()
            return
        if self.data != build_prefix(qualify=False):
            raise ValueError('Successor historical prefix changed')
        self.spent = Decimal(self.data['prior_spend_usd'])
        self.resolved_rejections = set(self.data['resolved_rejection_indices'])
