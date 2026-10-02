"""One-shot, synchronous 12-case application diagnostic; no evaluator calls."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.phase73_v6_budget import response_charge, request_hash
from scripts.quality_cost_phase73_v2 import SpendJournal, live_policy
from scripts.quality_eval_transport_v23 import exclusive_lock

FOLDER = ROOT / 'data/evaluation/application-reliability-live-v1'
DBNAME = 'proofbase_reliability_diag_v1'
INITIAL_REMAINDER = Decimal('3.79479490')
ALLOCATION = Decimal('1.00')


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


class Stop(RuntimeError):
    pass


def reservation(body, operation):
    """UTF-8 byte bound plus framing allowance; reject rather than trim inputs."""
    if body.get('stream') or body.get('tools') or body.get('functions'):
        raise Stop('Only synchronous text requests are authorized')
    bound = len(json.dumps(body, ensure_ascii=False).encode()) + 2048
    if operation == 'chat':
        if body.get('model') != 'gpt-4.1-mini':
            raise Stop('Unpriced chat model')
        if not body.get('messages') or not all(isinstance(m.get('content'), str) for m in body['messages']):
            raise Stop('Only text messages are priced')
        cap = body.get('max_completion_tokens', body.get('max_tokens'))
        if type(cap) is not int or not 1 <= cap <= 2048 or bound > 16384:
            raise Stop('Chat token bound exceeded')
        amount = (bound * Decimal('.40') + cap * Decimal('1.60')) / 1_000_000
    elif operation == 'embedding':
        texts = body.get('input')
        single_text = isinstance(texts, str) or (isinstance(texts, list) and len(texts) == 1 and isinstance(texts[0], str))
        if body.get('model') != 'text-embedding-3-small' or not single_text or bound > 8192:
            raise Stop('Embedding model/input/token bound exceeded')
        cap = 0
        amount = bound * Decimal('.02') / 1_000_000
    else:
        raise Stop('No evaluator or other operation is authorized')
    return bound, cap, amount


class Ledger:
    def __init__(self, folder, journal):
        self.folder, self.journal = Path(folder), journal
        self.path = self.folder / 'api-ledger.json'
        self.data = {'calls': [], 'stopped': False, 'unknown_outcome': False}
        self.case_id = None
        if self.path.exists():
            raise Stop('One-shot ledger already exists; no retry/resume')
        write(self.path, self.data)

    @property
    def spent(self):
        return sum((Decimal(r['charged_usd']) for r in self.data['calls']), Decimal(0))

    def stop(self, reason):
        self.data.update(stopped=True, stop_reason=reason)
        write(self.path, self.data)
        raise Stop(reason)

    def begin_case(self, case_id):
        if self.data['stopped'] or any(r['case_id'] == case_id for r in self.data['calls']):
            self.stop('Stopped or already attempted case')
        self.case_id = case_id

    def call(self, create, body, operation):
        if self.data['stopped'] or not self.case_id:
            self.stop('No active unblocked case')
        try:
            bound, cap, amount = reservation(body, operation)
        except Stop as exc:
            self.stop(str(exc))
        rows = self.data['calls']
        same = [r for r in rows if r['case_id'] == self.case_id and r['operation'] == operation]
        total = [r for r in rows if r['operation'] == operation]
        if (len(same) >= (7 if operation == 'chat' else 3)
                or len(total) >= (84 if operation == 'chat' else 40)
                or len(rows) >= 124 or self.spent + amount > ALLOCATION):
            self.stop('Call or dollar bound exceeded before submission')
        index = len(rows)
        path = self.folder / 'raw' / f'call-{index:03}.json'
        identity = f'reliability-live-v1-{index:03}'
        row = dict(call_index=index, case_id=self.case_id, operation=operation,
                   request_sha256=request_hash(body), reserved_usd=str(amount),
                   charged_usd=str(amount), input_bound=bound, output_cap=cap,
                   status='reserved', raw_path=path.relative_to(self.folder).as_posix(),
                   additional_spend_identity=identity, started_at=now())
        entry = {'request': deepcopy(body), 'response': None, 'status': 'reserved'}
        # Shared budget records are append-only; old snapshot files remain untouched.
        try:
            self.journal.reserve(identity, amount, row['request_sha256'])
        except Exception:
            self.stop('Shared spending envelope rejected reservation')
        rows.append(row)
        write(self.path, self.data)
        write(path, entry)
        started = time.perf_counter()
        try:
            response = create(**body)
            entry.update(status='received', response=response.model_dump(mode='json'))
            write(path, entry)
            usage = entry['response']['usage']
            it, ot = usage['prompt_tokens'], usage.get('completion_tokens', 0)
            charge = response_charge(entry['response'], body['model'])
            if type(it) is not int or type(ot) is not int or not 0 <= it <= bound or not 0 <= ot <= cap or not 0 <= charge <= amount:
                raise Stop('Provider usage outside reservation')
            self.journal.finish(identity, charge, digest(path))
            row.update(status='completed', charged_usd=str(charge), input_tokens=it,
                       output_tokens=ot, raw_sha256=digest(path), finished_at=now(),
                       latency_ms=round((time.perf_counter()-started)*1000, 2))
            write(self.path, self.data)
            return response
        except BaseException as exc:
            entry['exception_type'] = type(exc).__name__
            write(path, entry)
            row.update(status='unknown', raw_sha256=digest(path))
            self.data.update(stopped=True, unknown_outcome=True)
            write(self.path, self.data)
            self.journal.finish(identity, Decimal(0), digest(path), uncertain=True)
            raise

    @contextmanager
    def intercept(self):
        from openai import OpenAI
        from openai.resources.chat.completions import Completions
        from openai.resources.embeddings import Embeddings
        chat, embed, init = Completions.create, Embeddings.create, OpenAI.__init__
        def initialize(client, *args, **kwargs):
            kwargs['max_retries'] = 0
            return init(client, *args, **kwargs)
        def invoke(operation, original, resource, args, kwargs):
            if args or str(resource._client.base_url) != 'https://api.openai.com/v1/':
                self.stop('Unexpected SDK arguments or endpoint')
            resource._client.max_retries = 0
            body = dict(kwargs)
            if operation == 'chat' and 'max_tokens' not in body and 'max_completion_tokens' not in body:
                body['max_completion_tokens'] = 2048
            return self.call(lambda **kw: original(resource, **kw), body, operation)
        with patch.object(OpenAI, '__init__', initialize), \
             patch.object(Completions, 'create', lambda r, *a, **kw: invoke('chat', chat, r, a, kw)), \
             patch.object(Embeddings, 'create', lambda r, *a, **kw: invoke('embedding', embed, r, a, kw)):
            yield


def configure():
    from scripts.phase73_v6_environment import configure as configure_base
    from apps.api.app.core.config import get_settings
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    settings = configure_base()
    parts = conninfo_to_dict(settings.database_url)
    parts['dbname'] = DBNAME
    os.environ['DATABASE_URL'] = make_conninfo(**parts)
    for key, filename in {'OBSERVABILITY_LOG_PATH': 'requests.jsonl', 'AUDIT_LOG_PATH': 'audit.jsonl',
                          'SECURITY_EVENT_LOG_PATH': 'security.jsonl', 'SECURITY_NOTIFICATION_LOG_PATH': 'notifications.jsonl'}.items():
        os.environ[key] = str(ROOT / 'data/evaluation/local-runs/reliability-live-v1' / filename)
    get_settings.cache_clear()
    return get_settings()


def preflight(settings, suite):
    from scripts.phase73_v6_environment import fingerprint
    from apps.api.app.reasoning.source_planner import plan_multi_document_sources
    from apps.api.app.permissions.access_control import role_can_access
    import psycopg
    if not settings.openai_api_key or settings.openai_chat_model != 'gpt-4.1-mini' or settings.openai_embedding_model != 'text-embedding-3-small':
        raise Stop('Missing credential or unexpected model')
    _, ceiling = live_policy()
    journal = SpendJournal().load()
    spent = sum((Decimal(r['accounted_usd']) for r in journal['entries'].values()), Decimal(0))
    if ceiling - spent != INITIAL_REMAINDER or any(r['status'] != 'settled' for r in journal['entries'].values()):
        raise Stop('Historical remainder changed or unknown call exists')
    if len(suite['cases']) != 12 or len({c['case_id'] for c in suite['cases']}) != 12:
        raise Stop('Exactly twelve unique cases required')
    with psycopg.connect(settings.database_url) as conn:
        for case in suite['cases']:
            user = conn.execute('select business_role from demo_users where id::text=%s', (case['user_id'],)).fetchone()
            if not user or not role_can_access([user[0]], case['user_role']):
                raise Stop('Case identity/role mismatch')
            if len(plan_multi_document_sources(case['question'])) > 3:
                raise Stop('Planned retrieval exceeds three calls')
            for source in case['sources']:
                path = ROOT / source['path']
                if digest(path) != source['sha256'] or source['quote'] not in path.read_text(encoding='utf-8'):
                    raise Stop('Source expectation changed')
                chunks = conn.execute('''select c.content, d.access_roles from chunks c
                    join documents d on c.document_id=d.id where d.external_document_id=%s
                    and d.project_id::text=%s and d.tenant_id::text=%s and d.archived_at is null''',
                    (source['document_id'], case['project_id'], settings.default_demo_tenant_id)).fetchall()
                if not chunks or not any(source['quote'] in content for content, _ in chunks):
                    raise Stop('Expected source not present in local index')
                if any(role_can_access(roles, case['user_role']) != source['authorized'] for _, roles in chunks):
                    raise Stop('Source role expectation differs from database')
    state = fingerprint(settings)
    state.update(database=DBNAME, temperature_note='Unchanged application prompts; no evaluator')
    runtime_paths = subprocess.check_output(['git', 'ls-files', '--', 'apps/api/app', 'requirements.txt'], cwd=ROOT, text=True).splitlines()
    return {'checked_at': now(), 'runtime_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
            'suite_sha256': digest(FOLDER/'cases.json'), 'runner_sha256': digest(__file__),
            'runtime_files_sha256': {p: digest(ROOT/p) for p in runtime_paths},
            'initial_remainder_usd': str(INITIAL_REMAINDER), 'allocation_usd': str(ALLOCATION),
            'maximum_calls': 124, 'maximum_chat_calls': 84, 'maximum_embedding_calls': 40,
            'uncached_upper_bound_usd': '0.8323072', 'provider_retries': 0,
            'initial_journal': journal, 'environment': state}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-external-ai', action='store_true')
    args = parser.parse_args()
    settings, suite = configure(), read(FOLDER/'cases.json')
    prepared = preflight(settings, suite)
    if not args.allow_external_ai:
        write(FOLDER/'preflight.json', prepared)
        print('Preflight passed; zero API calls')
        return
    previous = read(FOLDER/'preflight.json')
    if any(previous[k] != prepared[k] for k in prepared if k != 'checked_at'):
        raise Stop('Preflight inputs changed')
    run = FOLDER/'run'
    with exclusive_lock(FOLDER):
        if run.exists():
            raise Stop('Diagnostic already started; no retry/resume')
        run.mkdir()
        ledger = Ledger(run, SpendJournal())
        manifest = {'status': 'running', 'started_at': now(), 'rows': {}}
        write(run/'manifest.json', manifest)
        from fastapi.testclient import TestClient
        from apps.api.app.main import app
        from scripts.phase73_v6_capture import measure_case
        try:
            with ledger.intercept(), TestClient(app) as client:
                for case in suite['cases']:
                    ledger.begin_case(case['case_id'])
                    path = run/(case['case_id']+'.json')
                    row = measure_case(client, settings, case, path, ledger)
                    manifest['rows'][case['case_id']] = digest(path)
                    write(run/'manifest.json', manifest)
                    if ledger.data['stopped'] or row['safety_flags']:
                        raise Stop('Budget, provider or safety stop')
                    print(f"Captured {case['case_id']}; {len(ledger.data['calls'])} calls; USD {ledger.spent}", flush=True)
            manifest['status'] = 'complete'
        except BaseException as exc:
            manifest.update(status='interrupted', exception_type=type(exc).__name__)
            raise
        finally:
            manifest.update(finished_at=now(), charged_usd=str(ledger.spent),
                            remaining_usd=str(INITIAL_REMAINDER-ledger.spent))
            write(run/'additional-spend.json', ledger.journal.load())
            write(run/'manifest.json', manifest)


if __name__ == '__main__':
    main()
