"""Audited successor prefix; never rewrite an interrupted historical ledger."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

from scripts import quality_confirmation_batch_v18 as confirmation
from scripts.quality_cost_control import ROOT, POLICY, read, digest, charge, live_policy
from scripts.quality_completion_ledger import Ledger as LegacyLedger

VERSION = 'phase73-accounting-prefix.v2'


def build_prefix(*, qualify=True):
    if qualify:
        confirmation.readiness()
    policy, _ = live_policy()
    baseline = ROOT / policy['baseline_ledger_path']
    resolution = ROOT / policy['prior_outcome_resolution']['path']
    old = read(baseline)
    calls = deepcopy(old['calls'])
    unresolved = [i for i, row in enumerate(calls) if row['status'] != 'completed']
    # Exactly the preserved first-call quota rejection, not a general exception waiver.
    rejected_path = 'confirmation-v18-01/fresh-v18-01/claims.json'
    if (unresolved != [len(calls) - 1] or calls[-1]['raw_path'] != rejected_path
            or calls[-1]['status'] != 'unknown'
            or Decimal(calls[-1]['charged_usd']) != Decimal(policy['prior_unresolved_reservation_usd'])):
        raise ValueError('Historical rejection does not match audited resolution')
    floor = Decimal(old['reconciliation']['conservative_spent_usd']) + sum(
        (Decimal(r['charged_usd']) for r in calls[old['reconciliation']['historical_calls']:]), Decimal(0))
    if floor != Decimal(policy['historical_conservative_usd']) + Decimal(policy['prior_unresolved_reservation_usd']):
        raise ValueError('Historical conservative floor changed')
    paths = {baseline, resolution, POLICY, confirmation.REPORT, confirmation.GATE,
             confirmation.REVIEW, confirmation.OUT / 'additional-spend.json'}
    report, gate = read(confirmation.REPORT), read(confirmation.GATE)
    if (gate.get('status') != 'approved' or gate.get('unresolved_semantic_findings') != 0
            or gate.get('human_adjudication') is not False
            or gate.get('report_sha256') != digest(confirmation.REPORT)
            or gate.get('source_review_sha256') != digest(confirmation.REVIEW)
            or report.get('matched') != 16 or report.get('calls') != 48):
        raise ValueError('Qualified Batch confirmation required')
    total = Decimal(0)
    for wave, count in [('initial', 32), ('review', 16)]:
        folder = confirmation.OUT / wave
        plan, state, requests = confirmation.batch.verify(folder)
        if len(requests) != count or state['status'] != 'complete':
            raise ValueError('Incomplete Batch accounting prefix')
        paths.update(p for p in folder.rglob('*') if p.is_file())
        for request in requests:
            path = folder / 'responses' / (request['custom_id'] + '.json')
            raw = read(path)
            cost = charge(raw['response'], 'batch')
            if raw['request'] != request['body'] or cost != Decimal(raw['cache_aware_cost_usd']):
                raise ValueError('Batch accounting row changed')
            total += cost
            calls.append({'call_index': len(calls), 'status': 'completed', 'operation': 'grader_batch',
                          'model': raw['response']['model'], 'charged_usd': str(cost),
                          'raw_path': path.relative_to(ROOT).as_posix(), 'raw_sha256': digest(path),
                          'batch_custom_id': request['custom_id']})
    if total != Decimal(report['cost_usd']):
        raise ValueError('Batch accounting total changed')
    return {'version': VERSION, 'calls': calls, 'resolved_rejection_indices': unresolved,
            'prior_spend_usd': str(floor + total), 'retained_reservation_usd': policy['prior_unresolved_reservation_usd'],
            'batch_cost_usd': str(total), 'invoice_verified': False,
            'sources_sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}}


class PriorLedger:
    def __init__(self, path):
        self.data = read(Path(path))
        if self.data.get('version') != VERSION:
            # Settled historical fixtures remain useful for accounting regressions.
            legacy = LegacyLedger(path)
            self.spent = legacy.spent
            self.resolved_rejections = set()
            return
        expected = build_prefix(qualify=False)
        if self.data != expected:
            raise ValueError('Historical accounting prefix changed')
        self.spent = Decimal(self.data['prior_spend_usd'])
        self.resolved_rejections = set(self.data['resolved_rejection_indices'])
