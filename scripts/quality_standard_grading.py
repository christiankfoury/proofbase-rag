"""One-shot synchronous v18 calls using the shared additional-spend envelope.

Request construction, parsing and scoring stay in the frozen v18 evaluator.
The caller must freeze/seal its protocol and resolve any pending Batch first.
"""
from copy import deepcopy
from decimal import Decimal
import hashlib
from pathlib import Path

from scripts.quality_batch_transport import validate_body, encoded
from scripts.quality_cost_control import charge, digest, read
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.quality_eval_transport_v18 import BudgetStop, exclusive_lock


class StandardLedger:
    def __init__(self, folder, journal, *, maximum_calls=48):
        self.folder, self.journal = Path(folder), journal
        if type(maximum_calls) is not int or not 1 <= maximum_calls <= 180:
            raise ValueError('Invalid bounded call count')
        # Do not consume the one-shot attempt while an earlier outcome is pending.
        if any(row['status'] != 'settled' for row in journal.load()['entries'].values()):
            raise BudgetStop('Pending provider outcome must be resolved first')
        if self.folder.exists():
            raise BudgetStop('Synchronous attempt exists; no resume or retry')
        self.folder.mkdir(parents=True)
        self.path = self.folder / 'calls.json'
        write(self.path, {'maximum_calls': maximum_calls, 'policy_sha256': digest(journal.policy_path),
                         'provider_retries': 0, 'calls': []})

    def call(self, create, body, raw_path):
        with exclusive_lock(self.folder):
            client = getattr(getattr(create, '__self__', None), '_client', None)
            if client is not None and client.max_retries != 0:
                raise BudgetStop('SDK automatic retries must be zero')
            data = read(self.path)
            if data['policy_sha256'] != digest(self.journal.policy_path):
                raise BudgetStop('Synchronous spending policy changed')
            if any(row['status'] != 'completed' for row in data['calls']):
                raise BudgetStop('Unknown provider outcome; do not retry')
            if len(data['calls']) >= data['maximum_calls']:
                raise BudgetStop('Synchronous call allowance exhausted')
            limits = validate_body(body)
            path = Path(raw_path).resolve()
            if not path.is_relative_to(self.folder.resolve()) or path.exists():
                raise BudgetStop('Unsafe or already attempted raw path')
            identity = 'standard-' + hashlib.sha256(str(path).encode()).hexdigest()
            request_hash = hashlib.sha256(encoded(body)).hexdigest()
            try:
                self.journal.reserve(identity, limits['reserved_usd'], request_hash)
            except ValueError as exc:
                raise BudgetStop(str(exc)) from exc
            raw = {'request': deepcopy(body), 'response': None, 'status': 'started'}
            row = {'index': len(data['calls']), 'identity': identity, 'status': 'started',
                   'path': path.relative_to(self.folder.resolve()).as_posix(),
                   'request_sha256': request_hash, 'reserved_usd': str(limits['reserved_usd'])}
            data['calls'].append(row)
            write(path, raw); write(self.path, data)
            try:
                response = create(**body)
                raw.update(status='received', response=response.model_dump(mode='json'))
                write(path, raw)  # Save before parsing or usage validation.
                amount = charge(raw['response'], 'standard')
                usage = raw['response']['usage']
                if (usage['prompt_tokens'] > limits['input_bound']
                        or usage['completion_tokens'] > limits['output_cap']
                        or amount > limits['reserved_usd']):
                    raise BudgetStop('Usage exceeds standard reservation')
                row.update(status='completed', charged_usd=str(amount), raw_sha256=digest(path))
                write(self.path, data)
                self.journal.finish(identity, amount, digest(path))
                return response
            except BaseException as exc:
                raw['exception_type'] = type(exc).__name__
                row['status'] = 'unknown'
                write(path, raw); write(self.path, data)
                self.journal.finish(identity, Decimal(0), digest(path), uncertain=True)
                raise


def audit(folder, requests, journal):
    """Reconstruct requests and costs; never infer semantic readiness here."""
    folder = Path(folder)
    data, spending = read(folder / 'calls.json'), journal.load()
    if (data['policy_sha256'] != digest(journal.policy_path)
            or spending['policy_sha256'] != data['policy_sha256'] or len(data['calls']) != len(requests)
            or data['provider_retries'] != 0 or type(data['maximum_calls']) is not int
            or not len(data['calls']) <= data['maximum_calls'] <= 180):
        raise ValueError('Synchronous call history differs')
    total = Decimal(0)
    seen = set()
    for index, (row, body) in enumerate(zip(data['calls'], requests)):
        path = (folder / row['path']).resolve()
        if not path.is_relative_to(folder.resolve()) or path in seen:
            raise ValueError('Duplicate or unsafe synchronous evidence')
        seen.add(path)
        raw = read(path); limits = validate_body(body)
        amount = charge(raw['response'], 'standard')
        entry = spending['entries'][row['identity']]
        if (row['index'] != index or row['status'] != 'completed' or raw['status'] != 'received'
                or row['identity'] != 'standard-' + hashlib.sha256(str(path).encode()).hexdigest()
                or raw['request'] != body or row['request_sha256'] != hashlib.sha256(encoded(body)).hexdigest()
                or digest(path) != row['raw_sha256'] or amount != Decimal(row['charged_usd'])
                or raw['response']['usage']['prompt_tokens'] > limits['input_bound']
                or raw['response']['usage']['completion_tokens'] > limits['output_cap']
                or row['reserved_usd'] != str(limits['reserved_usd'])
                or entry != {'status': 'settled', 'reserved_usd': row['reserved_usd'],
                    'accounted_usd': row['charged_usd'], 'evidence_sha256': row['request_sha256'],
                    'result_sha256': row['raw_sha256']}):
            raise ValueError('Synchronous raw result or settlement changed')
        total += amount
    return total
