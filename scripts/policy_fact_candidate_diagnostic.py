"""One predeclared application-path diagnostic; synchronous, no retries or repairs."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.quality_cost_phase73_v2 import SpendJournal, live_policy
from scripts.phase73_v6_budget import response_charge, request_hash
from scripts.reliability_payload_preparation import prepare_request
from scripts.quality_eval_transport_v23 import exclusive_lock

FOLDER = ROOT / 'data/evaluation/policy-fact-candidate'
INITIAL = Decimal('3.73920000')
CEILING = Decimal('.50')


def read(path): return json.loads(Path(path).read_bytes())
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()


def configure():
    os.environ.update(EVIDENCE_ASSESSMENT_PROMPT_VERSION='v6', EVIDENCE_ASSESSMENT_MODE='hybrid',
        POST_GENERATION_VALIDATION_PROMPT_VERSION='v4', REQUEST_ASSESSMENT_MODE='semantic_all_remaining',
        EXTERNAL_AI_MAX_RETRIES='0', PROOFBASE_TELEMETRY_ENABLED='false',
        OBSERVABILITY_LOG_PATH='data/observability/local-runs/policy-fact.jsonl')
    from apps.api.app.core.config import get_settings
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.openai_api_key or any(model != 'gpt-4.1-mini' for model in [settings.openai_chat_model,
            settings.evidence_assessment_model, settings.request_assessment_model, settings.post_generation_validation_model]):
        raise ValueError('Missing credential or unexpected model')
    return settings


def stage(body):
    name = body.get('response_format', {}).get('json_schema', {}).get('name', '')
    if name.startswith('request_assessment'): return 'request'
    if name == 'evidence_assessment_v6': return 'evidence'
    if name.startswith('post_generation_validation'): return 'validation'
    if body.get('messages', [{}])[0].get('content', '').startswith('You are Proofbase'):
        return 'generation'
    raise ValueError('Unexpected diagnostic stage')


def prepare(body):
    body = dict(body, service_tier='default', max_completion_tokens=2048)
    stage(body)
    return prepare_request(body, 'chat')


def same_assessment_payload(actual, prepared, which):
    if prepared is None:
        return False
    if which == 'request':
        return actual == prepared
    # Request-assessment output is genuinely dynamic. Only that context-only
    # field may differ; original question, authorized sources, prompt/schema and
    # all call settings must still match the prepared request.
    def comparable(body):
        body = json.loads(json.dumps(body))
        payload = json.loads(body['messages'][1]['content'])
        payload.pop('request_assessment_for_routing_context_only', None)
        body['messages'][1]['content'] = payload
        return body
    return comparable(actual) == comparable(prepared)


def budget():
    journal = SpendJournal().load(); _, ceiling = live_policy()
    if any(r['status'] != 'settled' for r in journal['entries'].values()):
        raise ValueError('Historical unresolved reservation')
    remainder = ceiling - sum((Decimal(r['accounted_usd']) for r in journal['entries'].values()), Decimal(0))
    if remainder != INITIAL: raise ValueError('Predeclared remaining budget changed')
    return journal


def preflight():
    # This import supplies only dry-run judgments and intentionally selects a dummy key.
    from scripts.test_policy_fact_candidate import mock_response
    from scripts.policy_fact_candidate_support import invoke, authorized_sources
    from openai.resources.chat.completions import Completions
    configure(); journal = budget(); suite = read(FOLDER/'cases.json')
    if len(suite['cases']) != 6 or len({c['id'] for c in suite['cases']}) != 6:
        raise ValueError('Exactly six unique cases required')
    bodies = []
    with ExitStack() as stack:
        for target in ['httpx.HTTPTransport.handle_request', 'httpx.AsyncHTTPTransport.handle_async_request', 'socket.create_connection']:
            stack.enter_context(patch(target, side_effect=AssertionError('Offline preflight network prohibited')))
        for case in suite['cases']:
            def capture(resource, **body):
                canonical, bound = prepare(body)
                bodies.append(dict(case_id=case['id'], stage=stage(body), request=canonical, input_bound=bound[0]))
                return mock_response(body, case, suite)
            with patch.object(Completions, 'create', capture):
                row = invoke(suite, case)
            if row['final_response']['response_type'] != case['expected_action']:
                raise ValueError('Offline routing preparation differs')
            if any(c.restricted for c in authorized_sources(suite, case)):
                raise ValueError('Diagnostic payload unexpectedly restricted')
    maxima = {s: max(b['input_bound'] for b in bodies if b['stage'] == s)
              for s in ['request', 'evidence', 'generation', 'validation']}
    if max(maxima.values()) + 4096 > 16384:
        raise ValueError('Insufficient dynamic payload headroom')
    files = list((ROOT/'apps/api/app').rglob('*.py')) + list((ROOT/'apps/api/app/prompts/versions').glob('*.md'))
    files += [Path(__file__), ROOT/'scripts/policy_fact_candidate_support.py', ROOT/'scripts/test_policy_fact_candidate.py',
        ROOT/'scripts/test_policy_fact_diagnostic.py', ROOT/'scripts/report_policy_fact_candidate.py',
        FOLDER/'cases.json', ROOT/'requirements.txt', ROOT/suite['source_capture'],
        ROOT/'scripts/reliability_payload_preparation.py', ROOT/'scripts/reliability_payload_budget.py',
        ROOT/'scripts/phase73_v6_budget.py', ROOT/'scripts/quality_cost_phase73_v2.py']
    plan = dict(created_at=now(), base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        bindings={p.relative_to(ROOT).as_posix():digest(p) for p in files}, initial_journal=journal,
        allocation_usd=str(CEILING), initial_remainder_usd=str(INITIAL), maximum_calls=24, provider_retries=0,
        maximum_input_tokens=16384, maximum_output_tokens=2048, absolute_upper_bound_usd='0.23592960',
        prices=dict(source='https://developers.openai.com/api/docs/models/gpt-4.1-mini', verified_on='2026-10-02',
                    input_per_million='.40', cached_input_per_million='.10', output_per_million='1.60'),
        prepared_stages=bodies, maximum_prepared_bounds=maxima, dynamic_input_headroom=4096)
    if (FOLDER/'preflight.json').exists(): raise ValueError('Preserve preflight; no overwrite')
    write(FOLDER/'preflight.json', plan)
    print(json.dumps(dict(prepared_payloads=len(bodies), maxima=maxima, absolute_upper_bound_usd=plan['absolute_upper_bound_usd'])))


class Ledger:
    def __init__(self, folder, journal, plan):
        self.folder, self.journal, self.plan = Path(folder), journal, plan
        self.data = dict(calls=[], attempted_cases=[], stopped=False, unknown_outcome=False)
        self.case_id = None
        self.save()

    def save(self): write(self.folder/'api-ledger.json', self.data)

    def stop(self, reason):
        self.data.update(stopped=True, stop_reason=reason); self.save()
        raise ValueError(reason)

    def begin(self, case_id):
        if self.data['stopped'] or case_id in self.data['attempted_cases'] or len(self.data['attempted_cases']) >= 6:
            self.stop('No repeated cases or continuation')
        self.case_id = case_id; self.data['attempted_cases'].append(case_id); self.save()

    def call(self, create, body):
        if self.data['stopped'] or not self.case_id: self.stop('No active case')
        try: canonical, (bound, cap, amount) = prepare(body)
        except Exception: self.stop('Unpriced or over-bound payload')
        which = stage(canonical); rows = self.data['calls']
        if len(rows) >= 24 or any(r['case_id'] == self.case_id and r['stage'] == which for r in rows):
            self.stop('No retry, repair or repeated stage')
        if which in {'request', 'evidence'}:
            expected = next((b['request'] for b in self.plan['prepared_stages']
                             if b['case_id'] == self.case_id and b['stage'] == which), None)
            if not same_assessment_payload(canonical, expected, which): self.stop('Frozen assessment payload differs')
        if sum((Decimal(r['charged_usd']) for r in rows), Decimal(0)) + amount > CEILING:
            self.stop('Diagnostic dollar ceiling exceeded')
        index = len(rows); identity = f'policy-fact-v1-{index:03}'
        path = self.folder/'raw'/f'call-{index:03}.json'
        row = dict(case_id=self.case_id, stage=which, identity=identity, status='reserved',
            input_bound=bound, output_cap=cap, reserved_usd=str(amount), charged_usd=str(amount),
            raw_path=path.relative_to(self.folder).as_posix(), request_sha256=request_hash(canonical))
        self.journal.reserve(identity, amount, row['request_sha256'])
        rows.append(row); self.save()
        raw = dict(request=canonical, response=None, status='reserved'); write(path, raw)
        try:
            response = create(**canonical)
            raw.update(response=response.model_dump(mode='json'), status='received'); write(path, raw)
            usage = raw['response']['usage']; cost = response_charge(raw['response'], canonical['model'])
            if not (0 <= usage['prompt_tokens'] <= bound and 0 <= usage['completion_tokens'] <= cap and 0 <= cost <= amount):
                raise ValueError('Provider exceeded reservation')
            self.journal.finish(identity, cost, digest(path))
            row.update(status='completed', charged_usd=str(cost), raw_sha256=digest(path)); self.save()
            return response
        except BaseException as exc:
            raw.update(status='unknown', exception_type=type(exc).__name__); write(path, raw)
            row.update(status='unknown', raw_sha256=digest(path))
            self.data.update(stopped=True, unknown_outcome=True); self.save()
            self.journal.finish(identity, Decimal(0), digest(path), uncertain=True)
            raise


def run():
    configure(); initial = budget(); plan = read(FOLDER/'preflight.json'); suite = read(FOLDER/'cases.json')
    if initial != plan['initial_journal'] or any(digest(ROOT/p) != h for p,h in plan['bindings'].items()):
        raise ValueError('Frozen runtime/evidence/accounting changed')
    if subprocess.check_output(['git','diff','HEAD','--',*plan['bindings']],cwd=ROOT,text=True).strip():
        raise ValueError('Commit frozen candidate before execution')
    from scripts.policy_fact_candidate_support import invoke
    from openai import OpenAI
    from openai.resources.chat.completions import Completions
    from openai.resources.embeddings import Embeddings
    folder = FOLDER/'run'; folder.mkdir()  # Existing run prohibits retry/resume.
    journal = SpendJournal(); ledger = Ledger(folder, journal, plan)
    manifest = dict(status='running', started_at=now(), rows=[], runtime_commit=subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), preflight_sha256=digest(FOLDER/'preflight.json'))
    write(folder/'manifest.json', manifest)
    chat, init = Completions.create, OpenAI.__init__
    def initialize(client, *args, **kwargs):
        kwargs['max_retries'] = 0; return init(client, *args, **kwargs)
    def call(resource, *args, **body):
        if args or str(resource._client.base_url) != 'https://api.openai.com/v1/':
            ledger.stop('Unexpected endpoint or arguments')
        resource._client.max_retries = 0
        return ledger.call(lambda **kw: chat(resource, **kw), body)
    try:
        with patch.object(OpenAI, '__init__', initialize), patch.object(Completions, 'create', call), \
             patch.object(Embeddings, 'create', side_effect=lambda *a, **kw: ledger.stop('Embeddings prohibited')):
            for case in suite['cases']:
                ledger.begin(case['id']); row = invoke(suite, case)
                path = folder/(case['id']+'.json'); write(path, row)
                manifest['rows'].append(dict(case_id=case['id'], sha256=digest(path))); write(folder/'manifest.json', manifest)
                print(case['id'] + ': ' + row['final_response']['response_type'], flush=True)
                if ledger.data['stopped']: raise ValueError('Transport stopped; no continuation')
                allowed = {c['chunk_id'] for c in row['authorized_evidence']}
                if any(c['chunk_id'] not in allowed for c in row['final_response']['citations']):
                    ledger.stop('Unauthorized citation')
                if case['kind'] == 'inaccessible' and '720' in row['final_response']['answer']:
                    ledger.stop('Inaccessible fixture disclosed')
        manifest['status'] = 'complete'
    except BaseException as exc:
        manifest.update(status='stopped', exception_type=type(exc).__name__)
        raise
    finally:
        current = journal.load(); _, ceiling = live_policy()
        manifest.update(finished_at=now(), charged_usd=str(sum((Decimal(r['charged_usd']) for r in ledger.data['calls']), Decimal(0))),
            remaining_usd=str(ceiling-sum((Decimal(r['accounted_usd']) for r in current['entries'].values()), Decimal(0))))
        write(folder/'additional-spend.json', current); write(folder/'manifest.json', manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--preflight', action='store_true'); parser.add_argument('--approve-live', action='store_true')
    args = parser.parse_args()
    if args.preflight and not args.approve_live: preflight()
    elif args.approve_live and not args.preflight:
        with exclusive_lock(FOLDER): run()
    else: parser.error('Choose offline --preflight or explicitly authorized --approve-live')
