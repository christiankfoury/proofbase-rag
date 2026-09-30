"""Durable, bounded Batch transport for unchanged v18 grading requests.

Prepare/submit/collect are separate commands: no polling loop, resubmission or
automatic fallback to standard pricing. A newly frozen protocol must authorize
each plan hash before submission; historical confirmation cannot be resumed.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.quality_cost_control import FOLDER, POLICY, MODEL, charge, digest, read, live_policy
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.quality_eval_transport_v18 import reserve, exclusive_lock

TERMINAL = {'completed', 'failed', 'expired', 'cancelled'}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode()


class SpendJournal:
    """One envelope shared by future grader batches and synchronous app calls."""
    def __init__(self, folder=FOLDER, policy_path=POLICY):
        self.folder, self.policy_path = Path(folder), Path(policy_path)
        self.path = self.folder / 'additional-spend.json'

    def load(self):
        data = read(self.path) if self.path.exists() else {'policy_sha256': digest(self.policy_path), 'entries': {}}
        if data['policy_sha256'] != digest(self.policy_path):
            raise ValueError('Spending policy changed after reservation')
        for row in data['entries'].values():
            amount, bound = Decimal(row['accounted_usd']), Decimal(row['reserved_usd'])
            if not amount.is_finite() or not bound.is_finite() or not 0 <= amount <= bound:
                raise ValueError('Invalid spending entry')
        return data

    def reserve(self, identity, amount, evidence_hash):
        self.folder.mkdir(parents=True, exist_ok=True)
        with exclusive_lock(self.folder):
            _, ceiling = live_policy(self.policy_path)
            data = self.load()
            if identity in data['entries']:
                raise ValueError('Operation already reserved; never resubmit')
            if any(r['status'] != 'settled' for r in data['entries'].values()):
                raise ValueError('Pending or unknown provider outcome blocks new spending')
            if not amount.is_finite() or amount <= 0:
                raise ValueError('Invalid reservation')
            accounted = sum((Decimal(r['accounted_usd']) for r in data['entries'].values()), Decimal(0))
            if accounted + amount > ceiling:
                raise ValueError('Additional spending ceiling would be exceeded')
            data['entries'][identity] = {'status': 'reserved', 'reserved_usd': str(amount),
                                        'accounted_usd': str(amount), 'evidence_sha256': evidence_hash}
            write(self.path, data)

    def finish(self, identity, amount, evidence_hash, *, uncertain=False):
        with exclusive_lock(self.folder):
            data = self.load()
            row = data['entries'][identity]
            if row['status'] == 'settled':
                if row['accounted_usd'] == str(amount) and row['result_sha256'] == evidence_hash:
                    return  # Safe local replay, never another provider submission.
                raise ValueError('Settlement changed')
            if not amount.is_finite() or not 0 <= amount <= Decimal(row['reserved_usd']):
                raise ValueError('Settlement exceeds reservation')
            row.update(status='unknown' if uncertain else 'settled',
                       accounted_usd=row['reserved_usd'] if uncertain else str(amount),
                       result_sha256=evidence_hash)
            write(self.path, data)


def validate_body(body):
    if set(body) != {'model', 'reasoning_effort', 'max_completion_tokens', 'messages', 'response_format'}:
        raise ValueError('Only unchanged text v18 grader requests are supported')
    if (body['model'] != MODEL or body['reasoning_effort'] != 'medium'
            or body['max_completion_tokens'] != 4096
            or not body['messages'] or not all(isinstance(m.get('content'), str) for m in body['messages'])
            or body['response_format'].get('type') != 'json_schema'):
        raise ValueError('Grader configuration changed')
    return reserve(body)


def prepare(folder, requests, bindings):
    """Local only. Bind a new frozen/sealed protocol before paid submission."""
    folder = Path(folder)
    if folder.exists():
        raise ValueError('Job folder already exists')
    if not 1 <= len(requests) <= 180 or not bindings:
        raise ValueError('A bounded request set and custody bindings are required')
    rows, identifiers, bound = [], set(), Decimal(0)
    for item in requests:
        cid, body = item['custom_id'], item['body']
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', cid) or cid in identifiers:
            raise ValueError('Invalid or duplicate custom_id')
        identifiers.add(cid)
        limits = validate_body(body)
        bound += limits['reserved_usd'] / 2
        rows.append({'custom_id': cid, 'method': 'POST', 'url': '/v1/chat/completions', 'body': body})
    for name, expected in bindings.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise ValueError('Custody binding differs')
    folder.mkdir(parents=True)
    (folder / 'input.jsonl').write_bytes(b''.join(encoded(row) + b'\n' for row in rows))
    from scripts.quality_confirmation_v18 import CODE
    plan = {'model': MODEL, 'count': len(rows), 'reservation_usd': str(bound),
            'input_sha256': digest(folder / 'input.jsonl'), 'bindings': bindings,
            'endpoint': '/v1/chat/completions', 'completion_window': '24h', 'provider_retries': 0,
            'code_sha256': {name: digest(ROOT / 'scripts' / name) for name in sorted(set(CODE) | {
                            'quality_batch_transport.py', 'quality_cost_control.py', 'quality_batch_grading.py'})}}
    write(folder / 'plan.json', plan)
    write(folder / 'state.json', {'status': 'prepared', 'plan_sha256': digest(folder / 'plan.json')})
    return plan


def verify(folder):
    plan, state = read(folder / 'plan.json'), read(folder / 'state.json')
    if digest(folder / 'plan.json') != state['plan_sha256'] or digest(folder / 'input.jsonl') != plan['input_sha256']:
        raise ValueError('Prepared job changed')
    if state.get('authorization_sha256') and digest(folder / 'authorization.json') != state['authorization_sha256']:
        raise ValueError('Job authorization changed')
    for name, expected in plan['bindings'].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise ValueError('Frozen custody changed')
    for name, expected in plan['code_sha256'].items():
        if digest(ROOT / 'scripts' / name) != expected:
            raise ValueError('Batch implementation changed')
    rows = [json.loads(line) for line in (folder / 'input.jsonl').read_bytes().splitlines()]
    amount = sum((validate_body(row['body'])['reserved_usd'] / 2 for row in rows), Decimal(0))
    if (len(rows) != plan['count'] or len({r['custom_id'] for r in rows}) != len(rows)
            or any(not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', r['custom_id']) or r['method'] != 'POST'
                   or r['url'] != '/v1/chat/completions' for r in rows)
            or str(amount) != plan['reservation_usd']):
        raise ValueError('Prepared bounds differ')
    return plan, state, rows


def submit(folder, client, journal):
    folder = Path(folder)
    with exclusive_lock(folder):
        plan, state, _ = verify(folder)
        if state['status'] != 'prepared':
            raise ValueError('Submission already attempted; never resubmit')
        live_policy(journal.policy_path)
        authorization = read(folder / 'authorization.json')
        if (authorization.get('plan_sha256') != state['plan_sha256']
                or authorization.get('status') != 'approved'
                or authorization.get('protocol_bindings') != plan['bindings']
                or authorization.get('human_adjudication') is not False):
            raise ValueError('New freeze/seal and reviewed plan authorization required')
        if client.max_retries != 0:
            raise ValueError('SDK automatic retries must be zero')
        identity = 'batch-' + state['plan_sha256']
        journal.reserve(identity, Decimal(plan['reservation_usd']), state['plan_sha256'])
        state.update(status='submitting', journal_identity=identity,
                     authorization_sha256=digest(folder / 'authorization.json'))
        write(folder / 'state.json', state)
        try:
            with (folder / 'input.jsonl').open('rb') as handle:
                uploaded = client.files.create(file=handle, purpose='batch')
            write(folder / 'upload.json', uploaded.model_dump(mode='json'))
            batch = client.batches.create(input_file_id=uploaded.id, endpoint=plan['endpoint'], completion_window='24h')
            write(folder / 'submission.json', batch.model_dump(mode='json'))
            state.update(status='submitted', batch_id=batch.id, input_file_id=uploaded.id)
            write(folder / 'state.json', state)
        except BaseException as exc:
            # A timeout can conceal a successfully accepted batch. Never create it again.
            state.update(status='unknown', exception_type=type(exc).__name__)
            write(folder / 'state.json', state)
            journal.finish(identity, Decimal(0), digest(folder / 'state.json'), uncertain=True)
            raise
    return state


def collect(folder, client, journal):
    """One status read; later calls only retrieve the same batch ID."""
    folder = Path(folder)
    with exclusive_lock(folder):
        plan, state, requests = verify(folder)
        if state['status'] == 'complete':
            if state['result_sha256'] != digest(folder / 'result.json'):
                raise ValueError('Completed result changed')
            return read(folder / 'result.json')
        if state['status'] != 'submitted':
            raise ValueError('No safely identified submitted batch')
        if client.max_retries != 0:
            raise ValueError('SDK automatic retries must be zero')
        batch = client.batches.retrieve(state['batch_id'])
        snapshot = batch.model_dump(mode='json')
        write(folder / 'provider-status.json', snapshot)
        if batch.id != state['batch_id'] or batch.input_file_id != state['input_file_id']:
            raise ValueError('Provider batch identity differs')
        if batch.status not in TERMINAL:
            return {'status': batch.status, 'batch_id': batch.id}
        # Raw files are saved before any parsing or scoring. Error rows cannot earn credit.
        lines = []
        for kind in ('output', 'error'):
            file_id = getattr(batch, kind + '_file_id', None)
            if file_id:
                content = client.files.content(file_id).content
                path = folder / (kind + '.jsonl')
                if path.exists() and path.read_bytes() != content:
                    raise ValueError('Provider result file changed')
                path.write_bytes(content)
                lines.extend(content.splitlines())
        expected = {r['custom_id']: r['body'] for r in requests}
        seen, valid, errors, amount = set(), {}, [], Decimal(0)
        try:
            for line in lines:
                row = json.loads(line)
                cid = row.get('custom_id')
                if cid not in expected or cid in seen:
                    raise ValueError('Unknown or duplicated result ID')
                seen.add(cid)
                response = row.get('response') or {}
                if row.get('error') or response.get('status_code') != 200:
                    errors.append(cid)
                    continue
                body = response['body']
                value = charge(body, 'batch')
                limits = validate_body(expected[cid])
                if body['usage']['prompt_tokens'] > limits['input_bound'] or body['usage']['completion_tokens'] > limits['output_cap']:
                    raise ValueError('Returned usage exceeds declared bound')
                amount += value
                valid[cid] = {'request': expected[cid], 'status': 'received', 'response': body,
                              'batch_id': batch.id, 'request_id': response.get('request_id'),
                              'cache_aware_cost_usd': str(value)}
            errors.extend(sorted(set(expected) - seen))
            if batch.status != 'completed':
                errors.append('batch_' + batch.status)
        except (ValueError, KeyError, TypeError) as exc:
            errors.append('invalid_result_' + type(exc).__name__)
        result = {'status': 'unresolved' if errors else 'complete', 'batch_id': batch.id,
                  'successful_responses': len(valid), 'expected_responses': len(expected),
                  'errors': errors, 'cache_aware_estimate_usd': str(amount),
                  'raw_files_sha256': {p.name: digest(p) for p in (folder / 'output.jsonl', folder / 'error.jsonl') if p.exists()},
                  'human_adjudication': False, 'evaluation_passed': False}
        write(folder / 'result.json', result)
        for cid, raw in valid.items():
            write(folder / 'responses' / (cid + '.json'), raw)
        journal.finish(state['journal_identity'], amount, digest(folder / 'result.json'), uncertain=bool(errors))
        state.update(status=result['status'], result_sha256=digest(folder / 'result.json'))
        write(folder / 'state.json', state)
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'submit', 'collect'))
    parser.add_argument('job', type=Path)
    parser.add_argument('--requests', type=Path, help='JSON object containing requests and immutable artifact bindings')
    parser.add_argument('--allow-external-ai', action='store_true')
    args = parser.parse_args()
    if args.action == 'prepare':
        spec = read(args.requests)
        result = prepare(args.job, spec['requests'], spec['bindings'])
    else:
        if not args.allow_external_ai:
            raise SystemExit('Explicit --allow-external-ai required; no network request sent')
        if args.action == 'submit':
            live_policy()  # Fail before credential/client creation.
        from apps.api.app.core.config import get_settings
        from openai import OpenAI
        client = OpenAI(api_key=get_settings().openai_api_key, max_retries=0, timeout=60)
        result = globals()[args.action](args.job, client, SpendJournal())
    print(json.dumps(result, indent=2))
