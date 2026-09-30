"""Audited successor prefix; never rewrite an interrupted historical ledger."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path

from scripts import quality_confirmation_standard_v18 as confirmation
from scripts.quality_cost_control import ROOT, read, digest, charge
from scripts.quality_cost_standard import POLICY, live_policy, retained_entries
from scripts.quality_completion_ledger import Ledger as LegacyLedger

VERSION = 'phase73-accounting-prefix.v3'


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
        raise ValueError('Qualified standard confirmation required')
    # Cancellation receipts are historical calls, already covered by the full
    # retained reservation. Keep failed receipts without assigning a usage price.
    cancelled = ROOT / 'data/evaluation/quality-completion-v1/confirmation-v18-batch2-01/initial'
    paths.update(ROOT / name for name in policy['cancellation_evidence_sha256'])
    partial_cost = Decimal(0)
    for name in ['output.jsonl', 'error.jsonl']:
        path = cancelled / name
        for line in path.read_bytes().splitlines():
            row = json.loads(line); response = row['response']; success = response['status_code'] == 200
            cost = charge(response['body'], 'batch') if success else Decimal(0)
            partial_cost += cost
            if not success:
                unresolved.append(len(calls))
            calls.append({'call_index': len(calls), 'status': 'completed' if success else 'failed',
                          'operation': 'grader_batch_cancelled', 'charged_usd': str(cost),
                          'accounting_basis': 'included_in_full_retained_reservation',
                          'usage_price_known': success, 'batch_custom_id': row['custom_id'],
                          'raw_path': path.relative_to(ROOT).as_posix(), 'raw_sha256': digest(path)})
    total = Decimal(0)
    folder = confirmation.OUT / 'requests'
    history = read(folder / 'calls.json')
    if len(history['calls']) != 48 or history['policy_sha256'] != digest(POLICY):
        raise ValueError('Incomplete standard accounting prefix')
    paths.update(p for p in confirmation.OUT.rglob('*') if p.is_file())
    for row in history['calls']:
        path = (folder / row['path']).resolve()
        if not path.is_relative_to(folder.resolve()) or row['status'] != 'completed':
            raise ValueError('Invalid standard accounting row')
        raw = read(path); cost = charge(raw['response'])
        if digest(path) != row['raw_sha256'] or cost != Decimal(row['charged_usd']):
            raise ValueError('Standard accounting row changed')
        total += cost
        calls.append({'call_index': len(calls), 'status': 'completed', 'operation': 'grader_standard',
                      'model': raw['response']['model'], 'charged_usd': str(cost),
                      'raw_path': path.relative_to(ROOT).as_posix(), 'raw_sha256': digest(path),
                      'standard_identity': row['identity']})
    retained = sum((Decimal(r['accounted_usd']) for r in retained_entries().values()), Decimal(0))
    if (total != Decimal(report['cost_usd'])
            or retained != Decimal(report['retained_reservation_usd'])
            or total + retained != Decimal(report['additional_accounted_usd'])):
        raise ValueError('Standard accounting total changed')
    return {'version': VERSION, 'calls': calls, 'resolved_rejection_indices': unresolved,
            'prior_spend_usd': str(floor + retained + total),
            'prior_batch_retained_reservation_usd': str(retained), 'retained_reservation_usd': policy['prior_unresolved_reservation_usd'],
            'cancelled_batch_successful_cost_usd': str(partial_cost),
            'standard_cost_usd': str(total), 'invoice_verified': False,
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
