"""Versioned application ledger with explicit per-turn and whole-suite call bounds."""
from decimal import Decimal
from pathlib import Path
from scripts.bounded_redesign_run import write, digest, response_charge, request_hash, prepare, PROFILES


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
        per_turn = bound.get('per_turn', bound['count']//15)
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

