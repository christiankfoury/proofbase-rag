"""Bounded, durable mixed-model accounting for one Phase 73 measurement.

The historical conservative floor is immutable. The user-selected additional
ceiling covers every new call; no retry after an uncertain outcome.
"""
from contextlib import contextmanager
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import threading
from unittest.mock import patch

from scripts.quality_completion_durable import write_json_atomic
from scripts.quality_completion_ledger import Ledger as QualityLedger, digest, FOLDER as QUALITY
from scripts.quality_eval_transport_v18 import exclusive_lock, MODEL, reserve
from scripts.quality_cost_control import POLICY, read as read_cost, charge as grader_charge
from scripts.quality_batch_transport import SpendJournal

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/evaluation/current-runtime-v4'
PRICES = {'gpt-4.1-mini': ('0.40', '1.60'),
          'gpt-4.1-mini-2025-04-14': ('0.40', '1.60'),
          'text-embedding-3-small': ('0.02', '0'), MODEL: ('2.50', '15.00')}
APP_INPUT_CAP = 131072
APP_OUTPUT_CAP = 2048
APP_CALLS_PER_CASE = 32
GRADER_CALLS_PER_CASE = 3
GRADER_INPUT_CAP = 272000
GRADER_OUTPUT_CAP = 4096
CACHED_INPUT_RATES = {'gpt-4.1-mini': '0.10', 'gpt-4.1-mini-2025-04-14': '0.10'}


def response_charge(response, model):
    if model == MODEL:
        return grader_charge(response)
    expected = {'gpt-4.1-mini': 'gpt-4.1-mini-2025-04-14'}.get(model, model)
    if response.get('model', model) != expected:
        raise BudgetStop('Provider returned an unpriced model')
    usage = response['usage']
    it, ot = usage['prompt_tokens'], usage.get('completion_tokens', 0)
    cached = (usage.get('prompt_tokens_details') or {}).get('cached_tokens', 0)
    if any(type(v) is not int for v in (it, ot, cached)) or not 0 <= cached <= it or ot < 0:
        raise BudgetStop('Invalid cached usage')
    ri, ro = map(Decimal, PRICES[model])
    rc = Decimal(CACHED_INPUT_RATES.get(model, str(ri)))
    return ((it - cached) * ri + cached * rc + ot * ro) / 1_000_000


class BudgetStop(RuntimeError):
    pass


def bounds():
    app = (Decimal(APP_INPUT_CAP) * Decimal('.4') + APP_OUTPUT_CAP * Decimal('1.6')) / 1_000_000
    grader = (Decimal(GRADER_INPUT_CAP) * Decimal('2.5') + GRADER_OUTPUT_CAP * Decimal('15')) / 1_000_000
    return {'cases': 60, 'app_calls_per_case': APP_CALLS_PER_CASE,
            'grader_calls_per_case': GRADER_CALLS_PER_CASE,
            'maximum_calls': 60 * (APP_CALLS_PER_CASE + GRADER_CALLS_PER_CASE),
            'app_input_cap': APP_INPUT_CAP, 'app_output_cap': APP_OUTPUT_CAP,
            'grader_input_cap': GRADER_INPUT_CAP, 'grader_output_cap': GRADER_OUTPUT_CAP,
            'upper_bound_usd': str(60 * (APP_CALLS_PER_CASE * app + GRADER_CALLS_PER_CASE * grader)),
            'prices_per_million': {model:list(rates) for model,rates in PRICES.items()}, 'provider_retries': 0,
            'local_cumulative_ceiling_usd': None,
            'additional_ceiling_usd': read_cost(POLICY)['additional_ceiling_usd'],
            'cost_policy_sha256': digest(POLICY),
            'cached_input_rates_per_million': CACHED_INPUT_RATES}


def request_hash(body):
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


class Ledger:
    def __init__(self, path=FOLDER/'api-ledger.json'):
        self.path = Path(path)
        self.lock = threading.RLock()
        self.case_id = None
        self.additional_spend = SpendJournal()
        self.reload()

    @classmethod
    def initialize(cls):
        previous = QualityLedger(QUALITY/'api-ledger.json')
        if previous.data['stage'] is not None:
            raise BudgetStop('Prior stage is still active')
        FOLDER.mkdir(parents=True, exist_ok=True)
        if (FOLDER/'prior-ledger.json').exists() or (FOLDER/'api-ledger.json').exists():
            raise BudgetStop('Historical prefix already initialized')
        prior = FOLDER/'prior-ledger.json'
        prior.write_bytes((QUALITY/'api-ledger.json').read_bytes())
        write_json_atomic(FOLDER/'api-ledger.json', {
            'prior_sha256': digest(prior), 'prior_spend_usd': str(previous.spent),
            'prior_calls': len(previous.data['calls']), 'authorization_sha256': digest(QUALITY/'autonomous-authorization.json'),
            'bounds': bounds(), 'calls': deepcopy(previous.data['calls']),
            'unknown_outcome': False, 'budget_exhausted': False})
        return cls()

    def reload(self):
        self.data = json.loads(self.path.read_bytes())
        base = self.path.parent.parent if self.path.parent.name == 'run' else self.path.parent
        prior_path = base/'prior-ledger.json'
        prior = QualityLedger(prior_path)
        if (self.data['prior_sha256'] != digest(prior_path)
            or self.data['prior_spend_usd'] != str(prior.spent)
            or self.data['prior_calls'] != len(prior.data['calls'])
            or self.data['calls'][:self.data['prior_calls']] != prior.data['calls']
            or self.data['authorization_sha256'] != digest(QUALITY/'autonomous-authorization.json')
            or self.data['bounds'] != bounds()):
            raise BudgetStop('Historical accounting or authorization changed')
        for i, row in enumerate(self.data['calls']):
            charge = Decimal(str(row['charged_usd']))
            if row['call_index'] != i or not charge.is_finite() or charge < 0:
                raise BudgetStop('Invalid call history')
        if self.data['unknown_outcome'] or any(r['status'] != 'completed' for r in self.data['calls']):
            raise BudgetStop('Unsettled provider outcome; do not retry')
        if self.data['budget_exhausted']:
            raise BudgetStop('Predeclared call/token allowance exhausted')

    @property
    def spent(self):
        return Decimal(self.data['prior_spend_usd']) + sum(
            (Decimal(str(r['charged_usd'])) for r in self.data['calls'][self.data['prior_calls']:]), Decimal(0))

    def begin_case(self, case_id):
        self.reload()
        if any(r.get('case_id') == case_id for r in self.data['calls'][self.data['prior_calls']:]):
            raise BudgetStop('Case has already issued calls; no resume')
        self.case_id = case_id

    def stop_bound(self, reason):
        self.data['budget_exhausted'] = True
        write_json_atomic(self.path, self.data)
        raise BudgetStop(reason)

    def call(self, create, body, raw_path, operation='grader'):
        with self.lock, exclusive_lock(self.path.parent):
            self.reload()
            if not self.case_id:
                raise BudgetStop('No declared active case')
            model = body.get('model')
            if model not in PRICES or body.get('stream') or body.get('tools') or body.get('functions'):
                self.stop_bound('Unpriced or unsupported request')
            if operation == 'embedding':
                texts = body.get('input')
                if model != 'text-embedding-3-small' or not (isinstance(texts,str) or isinstance(texts,list) and all(isinstance(t,str) for t in texts)):
                    self.stop_bound('Only text embedding inputs are priced')
            elif model == 'text-embedding-3-small' or not all(isinstance(m.get('content'),str) for m in body.get('messages',[])):
                self.stop_bound('Only text chat messages are priced')
            if operation == 'grader':
                limits = reserve(body)
            else:
                if model == MODEL or operation not in {'chat', 'embedding'}:
                    self.stop_bound('Invalid application operation')
                cap = body.get('max_completion_tokens', body.get('max_tokens', 0)) if operation == 'chat' else 0
                input_bound = len(json.dumps(body, ensure_ascii=False).encode()) + 2048
                if type(cap) is not int or not 0 <= cap <= APP_OUTPUT_CAP or input_bound > APP_INPUT_CAP:
                    self.stop_bound('Application token bound exceeded before call')
                ri, ro = map(Decimal, PRICES[model])
                limits = {'input_bound': input_bound, 'output_cap': cap,
                          'reserved_usd': (input_bound * ri + cap * ro) / 1_000_000}
            current = self.data['calls'][self.data['prior_calls']:]
            same = [r for r in current if r['case_id'] == self.case_id and (r['operation'] == 'grader') == (operation == 'grader')]
            maximum = GRADER_CALLS_PER_CASE if operation == 'grader' else APP_CALLS_PER_CASE
            if (len(same) >= maximum or len(current) >= bounds()['maximum_calls']
                or self.spent - Decimal(self.data['prior_spend_usd']) + limits['reserved_usd'] > Decimal(bounds()['upper_bound_usd'])):
                self.stop_bound('Predeclared case/run allowance exhausted')
            path = Path(raw_path).resolve()
            if not path.is_relative_to(self.path.parent.resolve()) or path.exists():
                raise BudgetStop('Unsafe or already attempted raw path')
            identity = 'sync-' + hashlib.sha256(str(path).encode()).hexdigest()
            # Shared with Batch jobs: reserve before writing a started row or calling OpenAI.
            self.additional_spend.reserve(identity, limits['reserved_usd'], request_hash(body))
            entry = {'request': deepcopy(body), 'status': 'started', 'response': None}
            row = {'call_index': len(self.data['calls']), 'case_id': self.case_id,
                   'operation': operation, 'model': model, 'status': 'started',
                   'raw_path': path.relative_to(self.path.parent.resolve()).as_posix(),
                   'request_sha256': request_hash(body), 'reserved_usd': str(limits['reserved_usd']),
                   'charged_usd': str(limits['reserved_usd']), 'input_bound': limits['input_bound'],
                   'output_cap': limits['output_cap'], 'input_tokens': None, 'output_tokens': None,
                   'additional_spend_identity': identity}
            write_json_atomic(path, entry)
            self.data['calls'].append(row)
            write_json_atomic(self.path, self.data)
            try:
                response = create(**body)
                entry.update(status='received', response=response.model_dump(mode='json'))
                write_json_atomic(path, entry)
                usage = response.usage
                it, ot = usage.prompt_tokens, getattr(usage, 'completion_tokens', 0)
                response_model = getattr(response, 'model', model)
                expected = {'gpt-4.1-mini': 'gpt-4.1-mini-2025-04-14'}.get(model, model)
                charge = response_charge(entry['response'], model)
                if (type(it) is not int or type(ot) is not int or it < 0 or ot < 0
                    or response_model != expected or it > limits['input_bound'] or ot > limits['output_cap'] or charge > limits['reserved_usd']):
                    raise BudgetStop('Provider model or usage outside declaration')
                row.update(status='completed', charged_usd=str(charge), input_tokens=it,
                           output_tokens=ot, response_model=response_model, raw_sha256=digest(path))
                write_json_atomic(self.path, self.data)
                self.additional_spend.finish(identity, charge, digest(path))
                return response
            except BaseException as exc:
                row['status'] = 'unknown'
                self.data['unknown_outcome'] = True
                # Preserve any completed response; uncertainty never erases evidence.
                entry['exception_type'] = type(exc).__name__
                write_json_atomic(path, entry)
                write_json_atomic(self.path, self.data)
                self.additional_spend.finish(identity, Decimal(0), digest(path), uncertain=True)
                raise

    @contextmanager
    def intercept(self):
        from openai import OpenAI
        from openai.resources.chat.completions import Completions
        from openai.resources.embeddings import Embeddings
        chat, embed, init = Completions.create, Embeddings.create, OpenAI.__init__
        ledger = self
        def initialize(client, *args, **kwargs):
            kwargs['max_retries'] = 0
            return init(client, *args, **kwargs)
        def invoke(operation, original, resource, args, kwargs):
            if args:
                raise BudgetStop('Positional SDK arguments are unsupported')
            resource._client.max_retries = 0
            body = dict(kwargs)
            if operation == 'chat':
                key = 'max_tokens' if 'max_tokens' in body else 'max_completion_tokens'
                body[key] = min(body.get(key, APP_OUTPUT_CAP), APP_OUTPUT_CAP)
            with ledger.lock:
                path = ledger.path.parent/'run'/'raw-app'/f"call-{len(ledger.data['calls']):05d}.json"
                return ledger.call(lambda **kw: original(resource, **kw), body, path, operation)
        with patch.object(OpenAI, '__init__', initialize), \
             patch.object(Completions, 'create', lambda resource, *a, **kw: invoke('chat', chat, resource, a, kw)), \
             patch.object(Embeddings, 'create', lambda resource, *a, **kw: invoke('embedding', embed, resource, a, kw)):
            yield self
