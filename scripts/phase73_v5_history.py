"""Complete successor accounting with the specifically authorized timeout retained."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from scripts import quality_confirmation_standard_v21 as confirmation
from scripts import quality_cost_phase73 as spending
from scripts.quality_cost_control import ROOT, read, digest, charge
from scripts.quality_completion_ledger import Ledger as LegacyLedger
from scripts.phase73_eval_history import PriorLedger as OriginalPrior
from scripts.quality_standard_grading import audit as audit_standard

VERSION = 'phase73-successor-accounting-prefix.v1'
ORIGINAL = ROOT / 'data/evaluation/current-runtime-v4'


def retained_prefix():
    spending.live_policy()
    audit = read(spending.OLD_AUDIT)
    data = read(ORIGINAL / 'run/api-ledger.json')
    prior = OriginalPrior(ORIGINAL / 'prior-ledger.json')
    seal = read(ORIGINAL / 'interruption-seal.json')
    paths = {ORIGINAL/'run/api-ledger.json', ORIGINAL/'prior-ledger.json',
             ORIGINAL/'interruption-seal.json', spending.OLD_AUDIT,
             spending.AUTHORIZATION, spending.POLICY, spending.PREFIX}
    if (data['calls'][:data['prior_calls']] != prior.data['calls']
            or data['prior_spend_usd'] != str(prior.spent)
            or data['prior_sha256'] != digest(ORIGINAL/'prior-ledger.json')
            or digest(ORIGINAL/'run/api-ledger.json') != seal['root_ledger_sha256']):
        raise ValueError('Original call prefix changed')
    for name, expected in seal['run_files_sha256'].items():
        path = (ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise ValueError('Original interrupted evidence changed')
        paths.add(path)
    calls = deepcopy(data['calls'])
    unresolved = [i for i, row in enumerate(calls)
                  if row['status'] != 'completed' and i not in prior.resolved_rejections]
    index = audit['unknown_call_index']
    row = calls[index]
    total = prior.spent + sum((Decimal(r['charged_usd'])
                              for r in calls[data['prior_calls']:]), Decimal(0))
    if (unresolved != [index] or index != len(calls)-1
            or len(calls) != audit['original_cumulative_calls']
            or str(total) != audit['original_cumulative_conservative_usd']
            or row['status'] != 'unknown'
            or row['request_sha256'] != audit['unknown_request_sha256']
            or row['additional_spend_identity'] != audit['unknown_shared_identity']
            or row['charged_usd'] != row['reserved_usd']
            or row['reserved_usd'] != audit['unknown_reservation_usd']):
        raise ValueError('Only the specifically authorized historical timeout may remain unknown')
    # Verify the accounting-only transition; the copied API row stays unknown.
    retained = spending.retained_entries()
    initial = read(spending.PREFIX)
    if initial['entries'] != retained or initial['policy_sha256'] != digest(spending.POLICY):
        raise ValueError('Successor initial accounting differs')
    return calls, total, sorted(prior.resolved_rejections | {index}), paths, retained


def standard_stages():
    dev = confirmation.previous.development
    return [(dev.prior.output('diagnostic'), 15), (dev.output('diagnostic'), 18),
            (dev.output('calibration'), 75), (confirmation.OUT, 48)]


def build_prefix(*, qualify=True):
    if qualify:
        from scripts.report_phase73_interruption import replay
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
