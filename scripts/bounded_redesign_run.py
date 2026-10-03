"""Once-only comparison under the CAD 20 authorization; no quality scoring here."""
from contextlib import ExitStack
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bounded_redesign_preflight import FOLDER, PROFILES, configure, prepare, c
from scripts.phase73_v6_budget import response_charge, request_hash
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.quality_cost_phase73_v2 import SpendJournal

def read(path): return json.loads(Path(path).read_bytes())
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()


class Ledger:
    def __init__(self, folder, policy, plan):
        self.folder, self.policy, self.plan = Path(folder), policy, plan
        self.data = dict(calls=[], turns=[], stopped=False, unknown_outcome=False)
        self.current = None
        self.save()

    def save(self): write(self.folder/'api-ledger.json', self.data)

    def stop(self, reason):
        self.data.update(stopped=True, stop_reason=reason); self.save()
        raise ValueError(reason)

    @property
    def accounted(self):
        return sum((Decimal(r['accounted_usd']) for r in self.data['calls']), Decimal(0))

    def begin(self, profile, case_id, turn):
        key = dict(profile=profile, case_id=case_id, turn=turn)
        if self.data['stopped'] or key in self.data['turns'] or profile not in PROFILES:
            self.stop('No repeated turn or continuation after stop')
        self.current = key; self.data['turns'].append(key); self.save()

    def call(self, create, body):
        if self.data['stopped'] or not self.current: self.stop('No active turn')
        try:
            canonical, limits = prepare(body)
            stage = canonical.get('response_format', {}).get('json_schema', {}).get('name', '')
            bound = next(r for r in self.plan['bounds'][self.current['profile']] if r['stage'] == stage)
            if (canonical['model'] != bound['model'] or limits['output_cap'] != bound['output_cap']
                    or limits['input_bound'] > bound['input_bound']):
                raise ValueError('Saved payload allowance exceeded')
        except Exception:
            self.stop('Unpriced, unexpected or over-bound request')
        matching = [r for r in self.data['calls'] if r['profile'] == self.current['profile'] and r['stage'] == stage]
        per_turn = bound['count']//15
        if len(matching) >= bound['count'] or sum(all(r[k] == v for k,v in self.current.items()) for r in matching) >= per_turn:
            self.stop('Saved call-count allowance exceeded')
        amount = Decimal(limits['reserved_usd'])
        ceiling = min(Decimal(self.policy['total_ceiling_usd']), Decimal(self.policy['stage_caps_usd']['application']))
        if self.accounted + amount > ceiling: self.stop('Dollar ceiling exceeded before submission')
        index = len(self.data['calls']); path = self.folder/'raw'/f'call-{index:03}.json'
        row = dict(self.current, stage=stage, status='reserved', **limits,
            accounted_usd=str(amount), raw_path=path.relative_to(self.folder).as_posix(), request_sha256=request_hash(canonical))
        raw = dict(request=canonical, response=None, status='reserved')
        # Persist both representations before the network; failed writes never submit.
        write(path, raw); self.data['calls'].append(row); self.save()
        try:
            response = create(**canonical)
            raw.update(response=response.model_dump(mode='json'), status='received'); write(path, raw)
            usage = raw['response']['usage']; cost = response_charge(raw['response'], canonical['model'])
            if not (0 <= usage['prompt_tokens'] <= limits['input_bound'] and
                    0 <= usage['completion_tokens'] <= limits['output_cap'] and 0 <= cost <= amount):
                raise ValueError('Provider receipt exceeds reservation')
            row.update(status='completed', accounted_usd=str(cost), raw_sha256=digest(path))
            self.save(); return response
        except BaseException as exc:
            # A received-but-unaccountable response is retained as well as unknown timeouts.
            raw.update(exception_type=type(exc).__name__); write(path, raw)
            row.update(status='unknown', accounted_usd=str(amount), raw_sha256=digest(path))
            self.data.update(stopped=True, unknown_outcome=True, stop_reason='Unknown provider/accounting outcome')
            self.save(); raise


def freeze():
    path = FOLDER/'cad20-freeze.json'
    if path.exists(): raise ValueError('Freeze already exists')
    files = list((ROOT/'apps/api/app').rglob('*.py')) + list((ROOT/'apps/api/app/prompts/versions').glob('*.md'))
    files += [ROOT/'requirements.txt', FOLDER/'development.json', FOLDER/'preflight-complete.json', FOLDER/'cad20-policy.json']
    # Bind the complete runner/helper dependency set without importing any test fixtures.
    files += list((ROOT/'scripts').glob('*.py'))
    write(path, dict(created_at=now(), bindings={p.relative_to(ROOT).as_posix():digest(p) for p in files},
        historical_journal_sha256=request_hash(SpendJournal().load())))


def run():
    policy = read(FOLDER/'cad20-policy.json'); plan = read(FOLDER/'preflight-complete.json')
    frozen = read(FOLDER/'cad20-freeze.json'); suite = read(FOLDER/'development.json')
    if any(digest(ROOT/p) != h for p,h in frozen['bindings'].items()): raise ValueError('Frozen inputs changed')
    if request_hash(SpendJournal().load()) != frozen['historical_journal_sha256']: raise ValueError('Historical journal changed')
    if subprocess.check_output(['git','diff','HEAD','--',*frozen['bindings']],cwd=ROOT,text=True).strip():
        raise ValueError('Commit frozen inputs before execution')
    if sum(map(Decimal,policy['stage_caps_usd'].values())) != Decimal(policy['total_ceiling_usd']):
        raise ValueError('Stage allocations do not reconcile')
    if Decimal(plan['total_reservation_usd']) > Decimal(policy['stage_caps_usd']['application']):
        raise ValueError('Whole comparison does not fit')
    if len(suite['cases']) != 12 or sum(len(x['turns']) for x in suite['cases']) != 15:
        raise ValueError('Coverage changed')
    from scripts.bounded_redesign_support import invoke
    from openai import OpenAI
    from openai.resources.chat.completions import Completions
    from openai.resources.embeddings import Embeddings
    from apps.api.app.core.config import get_settings
    configure('v4')
    if not get_settings().openai_api_key: raise ValueError('Existing API credential unavailable')
    folder = FOLDER/'cad20-comparison'; folder.mkdir()  # Atomic once-only execution guard.
    ledger = Ledger(folder, policy, plan)
    manifest = dict(status='running', started_at=now(), rows=[], runtime_commit=subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), freeze_sha256=digest(FOLDER/'cad20-freeze.json'),
        policy_sha256=digest(FOLDER/'cad20-policy.json'), preflight_sha256=digest(FOLDER/'preflight-complete.json'))
    write(folder/'manifest.json', manifest)
    chat, init = Completions.create, OpenAI.__init__
    def initialize(client, *args, **kwargs):
        kwargs.update(max_retries=0, timeout=30.0)
        return init(client, *args, **kwargs)
    def call(resource, *args, **body):
        if args or str(resource._client.base_url) != 'https://api.openai.com/v1/':
            ledger.stop('Unexpected endpoint or positional arguments')
        resource._client.max_retries = 0
        return ledger.call(lambda **kw: chat(resource, **kw), body)
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(OpenAI, '__init__', initialize))
            stack.enter_context(patch.object(Completions, 'create', call))
            stack.enter_context(patch.object(Embeddings, 'create', side_effect=lambda *a, **kw: ledger.stop('Unexpected embedding call')))
            for profile in PROFILES:
                configure(profile)
                for case in suite['cases']:
                    def before(turn): ledger.begin(profile, case['id'], turn)
                    def after(turn, evidence):
                        write(folder/f"{profile}-{case['id']}-turn-{turn['turn']}.json", dict(turn, authorized_evidence=evidence))
                        if ledger.data['stopped']: raise ValueError('Stopped transport')
                        allowed = {s['chunk_id'] for s in evidence}; result = turn['final_response']
                        if any(x.get('chunk_id') not in allowed for x in result.get('citations', [])):
                            ledger.stop('Unauthorized citation')
                        if case['id'] == 'dev-10' and '720' in result.get('answer',''):
                            ledger.stop('Inaccessible fixture disclosed')
                    row = invoke(suite, case, before_turn=before, after_turn=after)
                    path = folder/f"{profile}-{case['id']}.json"; write(path, row)
                    manifest['rows'].append(dict(profile=profile, case_id=case['id'], path=path.name, sha256=digest(path)))
                    write(folder/'manifest.json', manifest)
                    print(json.dumps(dict(profile=profile, case_id=case['id'], http=[t['status_code'] for t in row['turns']],
                        accounted_usd=str(ledger.accounted))), flush=True)
        manifest['status'] = 'complete'
    except BaseException as exc:
        manifest.update(status='stopped', exception_type=type(exc).__name__)
        raise
    finally:
        manifest.update(finished_at=now(), accounted_usd=str(ledger.accounted),
            unknown_outcome=ledger.data['unknown_outcome'], ledger_sha256=digest(folder/'api-ledger.json'))
        write(folder/'manifest.json', manifest)


if __name__ == '__main__':
    if sys.argv[1:] == ['freeze']: freeze()
    elif sys.argv[1:] == ['run']: run()
    else: raise SystemExit('Choose freeze or run')
