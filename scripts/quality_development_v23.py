"""One-shot v23 stages under the CAD-authorized successor spending ceiling."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import quality_development_v22 as prior
from scripts import quality_completion_eval_v18 as old_development
from scripts import quality_eval_contract_v23 as contract
from scripts import quality_eval_transport_v23 as transport
from scripts.quality_cost_phase73_v2 import POLICY, SpendJournal, live_policy
from scripts.quality_cost_control import read, digest
from scripts.quality_standard_grading import StandardLedger, audit
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.quality_confirmation_reference_checks import check_references
from scripts.report_quality_calibration_v12 import replay_raw

FOLDER = ROOT / 'data/evaluation/phase73-successor-v2'
CONTROLS = FOLDER / 'v23-development-controls.json'
DIAGNOSTIC_GATE = FOLDER / 'v23-diagnostic-readiness.json'
SOURCE_REVIEW = ROOT / 'docs/phase-73/v23-diagnostic-source-review.md'
STAGE_LIMITS = {'diagnostic': Decimal('1.00'), 'calibration': Decimal('1.50')}
CODE = sorted(set(prior.CODE) | {'quality_eval_contract_v23.py', 'quality_eval_transport_v23.py',
    'quality_cost_phase73_v2.py', 'quality_development_v23.py', 'test_quality_v23.py'})


def cases(stage):
    value = read(CONTROLS); check_references(value)
    if len(value['cases']) != 8 or len(value['review_probes']) != 3:
        raise ValueError('Development controls changed')
    return (value['cases'] if stage == 'diagnostic'
            else old_development.baseline.load_suite()['cases'])


def probes(stage):
    return (read(CONTROLS)['review_probes']
            if stage == 'diagnostic' else old_development.baseline.load_audits()['cases'])


def output(stage):
    if stage not in STAGE_LIMITS:
        raise ValueError('Unknown stage')
    return FOLDER / ('v23-' + stage)


def compare(case, grade, dims):
    mismatch = old_development.compare(case, grade, dims)
    if 'expected_fact_statuses' in case:
        actual = {f['fact_id']: f['status'] for f in grade['facts']} if grade else {}
        if actual != case['expected_fact_statuses']:
            mismatch['fact_statuses'] = {'expected': case['expected_fact_statuses'], 'actual': actual}
    return mismatch


def plan(stage, *, require_unused=True):
    _, ceiling = live_policy()
    prior_report = prior.replay('diagnostic')
    inspection = read(FOLDER/'v22-diagnostic-inspection.json')
    if (prior_report != read(FOLDER/'v22-diagnostic-report.json') or prior_report['status'] != 'early_stopped'
            or prior_report['count'] != 3 or prior_report['matched'] != 2 or prior_report['calls'] != 9
            or inspection['status'] != 'rejected_output_contract'
            or inspection['report_sha256'] != digest(FOLDER/'v22-diagnostic-report.json')
            or inspection['source_review_sha256'] != digest(ROOT/'docs/phase-73/v22-diagnostic-source-review.md')):
        raise ValueError('Preserved v22 diagnostic defect changed')
    prefix = prior.output('diagnostic') / 'additional-spend.json'
    if stage == 'calibration':
        report = replay('diagnostic'); gate = read(DIAGNOSTIC_GATE)
        if (report['status'] != 'complete' or report['matched'] != 8 or report['matching_probes'] != 3
                or gate.get('status') != 'approved' or gate.get('unresolved_semantic_findings') != 0
                or gate.get('report_sha256') != digest(FOLDER / 'v23-diagnostic-report.json')
                or report != read(FOLDER / 'v23-diagnostic-report.json')
                or gate.get('source_review_sha256') != digest(SOURCE_REVIEW)):
            raise ValueError('Diagnostic readiness required')
        prefix = output('diagnostic') / 'additional-spend.json'
    spending = read(prefix)
    if require_unused and (output(stage).exists() or SpendJournal().load() != spending):
        raise ValueError('Stage attempted or prior spending differs; no resume')
    amount = sum((Decimal(row['accounted_usd']) for row in spending['entries'].values()), Decimal(0))
    if amount + STAGE_LIMITS[stage] > ceiling:
        raise ValueError('Declared stage allowance exceeds remaining shared ceiling')
    bound = sum((transport.case_bound(c['inputs']) for c in cases(stage)), Decimal(0))
    bound += sum((transport.reserve(transport.review_request(c['inputs'], c['candidate']))['reserved_usd']
                  for c in probes(stage)), Decimal(0))
    paths = [CONTROLS, old_development.CONTROLS, old_development.baseline.SUITE,
             old_development.baseline.AUDITS, old_development.baseline.VALIDATION,
             POLICY, FOLDER / 'authorization.json', prefix, FOLDER/'v22-diagnostic-inspection.json', ROOT/'docs/phase-73/v22-diagnostic-source-review.md']
    if stage == 'calibration':
        paths += [DIAGNOSTIC_GATE, SOURCE_REVIEW, FOLDER / 'v23-diagnostic-report.json']
    return {'stage': stage, 'version': contract.VERSION, 'case_ids': [c['id'] for c in cases(stage)],
            'probe_ids': [c['id'] for c in probes(stage)], 'maximum_calls': len(cases(stage))*3+len(probes(stage)),
            'token_based_upper_bound_usd': str(bound), 'stage_spending_limit_usd': str(STAGE_LIMITS[stage]),
            'prior_accounted_usd': str(amount), 'additional_ceiling_usd': str(ceiling), 'provider_retries': 0, 'request_timeout_seconds': 180,
            'prefix_path': prefix.relative_to(ROOT).as_posix(),
            'bindings': {p.relative_to(ROOT).as_posix(): digest(p) for p in paths},
            'code_sha256': {n: digest(ROOT/'scripts'/n) for n in CODE}}


class StageLedger(StandardLedger):
    def __init__(self, folder, journal, maximum_calls, limit):
        self.limit = limit
        super().__init__(folder, journal, maximum_calls=maximum_calls)

    def call(self, create, body, path):
        spent = sum((Decimal(row.get('charged_usd', row['reserved_usd']))
                     for row in read(self.path)['calls']), Decimal(0))
        if spent + transport.reserve(body)['reserved_usd'] > self.limit:
            raise transport.BudgetStop('Declared stage spending limit reached before provider call')
        return super().call(create, body, path)


def judged(case, grade, review, error):
    dims = contract.dimensions(case['inputs'], grade, case['payload'], case['evidence'], case['safety_flags'], review)
    mismatch = compare(case, grade, dims)
    return {'grade': grade, 'review': review, 'error': error, 'dimensions': dims, 'mismatches': mismatch,
            'matched': not mismatch and not dims['grader_errors'] and not dims['disputed_dimensions']}


def probe_result(case, review, error):
    return {'review': review, 'error': error, 'matched': bool(review and all(
        review[k] == ('dispute' if k in case['expected_disputes'] else 'agree')
        for k in (*contract.DIMENSIONS, 'forbidden_assertion')))}


def execute(stage, client):
    spec = plan(stage)
    if client.max_retries != 0:
        raise ValueError('SDK retries forbidden')
    out = output(stage); journal = SpendJournal()
    ledger = StageLedger(out/'requests', journal, spec['maximum_calls'], STAGE_LIMITS[stage])
    manifest = {'status': 'running', 'plan': spec, 'rows': {}, 'probes': {}, 'human_adjudication': False}
    write(out/'manifest.json', manifest)
    try:
        for case in cases(stage):
            grade = review = error = None
            try:
                grade, review = transport.grade_case(client.chat.completions.create, case['inputs'], ledger,
                                                     out/'requests'/case['id'])
            except (ValueError, IndexError) as exc:
                error = type(exc).__name__
            row = judged(case, grade, review, error); path = out/(case['id']+'.json'); write(path, row)
            manifest['rows'][case['id']] = digest(path); write(out/'manifest.json', manifest)
            print(f"{stage}: {len(manifest['rows'])}/{len(cases(stage))}; {'matches' if row['matched'] else 'disagreement'}", flush=True)
            if stage == 'diagnostic' and not row['matched']:
                manifest['status'] = 'early_stopped'; break
        else:
            for case in probes(stage):
                review = error = None
                body = transport.review_request(case['inputs'], case['candidate'])
                try:
                    review = transport.parsed(ledger.call(client.chat.completions.create, body,
                                               out/'requests'/(case['id']+'.json')), contract.review_schema())
                except (ValueError, IndexError) as exc:
                    error = type(exc).__name__
                path = out/(case['id']+'-probe.json'); write(path, probe_result(case, review, error))
                manifest['probes'][case['id']] = digest(path); write(out/'manifest.json', manifest)
            manifest['status'] = 'complete'
    except BaseException as exc:
        manifest.update(status='interrupted', exception_type=type(exc).__name__)
        raise
    finally:
        write(out/'manifest.json', manifest); write(out/'additional-spend.json', journal.load())


def replay(stage):
    out = output(stage); manifest = read(out/'manifest.json')
    if manifest['plan'] != plan(stage, require_unused=False):
        raise ValueError('Declared development inputs changed')
    bodies, rows, reviews = [], [], []
    for case in cases(stage):
        if case['id'] not in manifest['rows']:
            continue
        grade = review = error = None
        try:
            parts = {}
            for purpose, body in transport.initial_requests(case['inputs']):
                bodies.append(body); parts.update(replay_raw(out/'requests'/case['id']/(purpose+'.json'), body))
            body = transport.review_request(case['inputs'], parts); bodies.append(body)
            review = replay_raw(out/'requests'/case['id']/'review.json', body); grade = parts
        except (ValueError, IndexError) as exc:
            error = type(exc).__name__
        path = out/(case['id']+'.json'); row = judged(case, grade, review, error)
        if digest(path) != manifest['rows'][case['id']] or row != read(path):
            raise ValueError('Development judgment changed')
        rows.append({'id': case['id'], **row})
    for case in probes(stage):
        if case['id'] not in manifest['probes']:
            continue
        body = transport.review_request(case['inputs'], case['candidate']); bodies.append(body)
        review = error = None
        try:
            review = replay_raw(out/'requests'/(case['id']+'.json'), body)
        except (ValueError, IndexError) as exc:
            error = type(exc).__name__
        path = out/(case['id']+'-probe.json'); row = probe_result(case, review, error)
        if digest(path) != manifest['probes'][case['id']] or row != read(path):
            raise ValueError('Development probe changed')
        reviews.append({'id': case['id'], **row})
    snapshot = read(out/'additional-spend.json')
    cost = audit(out/'requests', bodies, SimpleNamespace(policy_path=POLICY, load=lambda: snapshot))
    prefix = read(ROOT/manifest['plan']['prefix_path'])
    calls = read(out/'requests/calls.json')['calls']
    expected = dict(prefix['entries'])
    for row in calls:
        if row['identity'] in expected:
            raise ValueError('Duplicate spending identity')
        expected[row['identity']] = snapshot['entries'][row['identity']]
    if snapshot['entries'] != expected or cost > STAGE_LIMITS[stage]:
        raise ValueError('Full spending prefix or stage bound differs')
    accounted = sum((Decimal(r['accounted_usd']) for r in snapshot['entries'].values()), Decimal(0))
    prior_new_calls = 0 if stage == 'diagnostic' else len(read(output('diagnostic')/'requests/calls.json')['calls'])
    return {'stage': stage, 'status': manifest['status'], 'count': len(rows),
            'matched': sum(r['matched'] for r in rows), 'matching_probes': sum(r['matched'] for r in reviews),
            'calls': len(calls), 'cost_usd': str(cost), 'rows': rows, 'probes': reviews,
            'additional_accounted_usd': str(accounted),
            'new_allowance_spent_usd': str(accounted - Decimal('9.87823685')),
            'new_allowance_remaining_usd': str(Decimal('18.87823685') - accounted),
            'cumulative_calls': 3483 + prior_new_calls + len(calls),
            'cumulative_conservative_usd': str(Decimal('20.73393762') + accounted - Decimal('9.87823685')),
            'semantic_validation_passed': False, 'human_adjudication': False}



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['preflight', 'execute', 'report'])
    parser.add_argument('--stage', choices=list(STAGE_LIMITS), default='diagnostic')
    parser.add_argument('--allow-external-ai', action='store_true')
    args = parser.parse_args()
    if args.action == 'execute':
        if not args.allow_external_ai:
            raise SystemExit('Explicit external approval required')
        plan(args.stage)
        from apps.api.app.core.config import get_settings
        from openai import OpenAI
        execute(args.stage, OpenAI(api_key=get_settings().openai_api_key, max_retries=0, timeout=180))
    elif args.action == 'report':
        result = replay(args.stage); write(FOLDER/('v23-'+args.stage+'-report.json'), result)
        print(json.dumps({k:v for k,v in result.items() if k not in {'rows','probes'}}, indent=2))
    else:
        print(json.dumps(plan(args.stage), indent=2))
