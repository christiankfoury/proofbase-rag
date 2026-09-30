"""Same spending ceiling after terminal cancellation; no discarded reservations."""
from copy import deepcopy
from decimal import Decimal
import json
from scripts import quality_cost_continuation as prior
from scripts.quality_batch_transport import SpendJournal as BaseJournal, verify, validate_body
from scripts.quality_cost_control import ROOT, FOLDER as COSTS, read, digest, charge

POLICY = COSTS / 'policy-standard.json'
FOLDER = COSTS / 'standard'


def live_policy(path=POLICY):
    policy, ceiling = prior.live_policy(path)
    source = prior.bound_file(policy['transition_journal'])
    old = read(source)
    if old['policy_sha256'] != digest(prior.POLICY):
        raise ValueError('Previous spending policy changed')
    bindings = policy['cancellation_evidence_sha256']
    for name, expected in bindings.items():
        prior.bound_file({'path': name, 'sha256': expected})
    folder = ROOT / 'data/evaluation/quality-completion-v1/confirmation-v18-batch2-01/initial'
    required = [folder / name for name in ['provider-status.json', 'result.json', 'state.json']]
    if any(p.relative_to(ROOT).as_posix() not in bindings for p in required):
        raise ValueError('Cancellation evidence incomplete')
    status, result, state = map(read, required)
    plan, verified_state, requests = verify(folder)
    if (status['status'] != 'cancelled' or status['request_counts']['failed'] != 0
            or result['successful_responses'] != status['request_counts']['completed']
            or any(str(e).startswith('invalid_result') for e in result['errors'])
            or result['batch_id'] != status['id'] or state['batch_id'] != status['id']
            or status['input_file_id'] != state['input_file_id'] or state != verified_state
            or status['request_counts']['total'] != plan['count']
            or result['expected_responses'] != plan['count']):
        raise ValueError('Cancellation or partial usage remains unresolved')
    expected = {r['custom_id']: r['body'] for r in requests}
    seen, successful, failed, amount = set(), set(), set(), Decimal(0)
    for name, expected_hash in result['raw_files_sha256'].items():
        path = folder / name
        if name not in {'output.jsonl', 'error.jsonl'} or bindings.get(path.relative_to(ROOT).as_posix()) != expected_hash:
            raise ValueError('Partial raw output binding missing')
        for line in path.read_bytes().splitlines():
            row = json.loads(line); cid = row['custom_id']; response = row.get('response') or {}
            if cid not in expected or cid in seen:
                raise ValueError('Partial output contains invalid request identity')
            seen.add(cid)
            if response.get('status_code') != 200:
                # Observed terminal receipts contain HTTP 500 server errors without
                # usage. Keep their full original reservation; do not infer zero cost.
                body = response.get('body') or {}
                if (row.get('error') or response.get('status_code') != 500
                        or (body.get('error') or {}).get('type') != 'server_error'
                        or body.get('usage') is not None):
                    raise ValueError('Unrecognized partial failure receipt')
                failed.add(cid)
                continue
            if row.get('error'):
                raise ValueError('Successful response also reports error')
            successful.add(cid)
            body = response['body']; limits = validate_body(expected[cid]); value = charge(body, 'batch')
            if (body['usage']['prompt_tokens'] > limits['input_bound']
                    or body['usage']['completion_tokens'] > limits['output_cap']):
                raise ValueError('Partial usage exceeds reserved bound')
            amount += value
    if (len(successful) != result['successful_responses'] or amount != Decimal(result['cache_aware_estimate_usd'])
            or set(result['errors']) != (set(expected) - successful) | {'batch_cancelled'}):
        raise ValueError('Partial output accounting differs')
    retained = prior.retained_entries()
    if set(old['entries']) != set(retained) | {state['journal_identity']}:
        raise ValueError('Unexpected predecessor spending')
    if any(old['entries'][key] != value for key, value in retained.items()):
        raise ValueError('Earlier reservation changed')
    entry = old['entries'][state['journal_identity']]
    if (entry['status'] != 'unknown' or entry['accounted_usd'] != entry['reserved_usd']
            or entry['result_sha256'] != digest(folder / 'result.json')):
        raise ValueError('Cancelled Batch reservation changed')
    return policy, ceiling


def retained_entries():
    policy, _ = live_policy()
    entries = deepcopy(read(prior.bound_file(policy['transition_journal']))['entries'])
    for row in entries.values():
        if row['status'] == 'unknown':
            row.update(status='settled', accounting_basis='cancelled_batch_full_reservation_retained',
                       transition_policy_sha256=digest(POLICY))
    return entries


class SpendJournal(BaseJournal):
    def __init__(self, folder=FOLDER, policy_path=POLICY):
        super().__init__(folder, policy_path)

    def load(self):
        retained = retained_entries()
        data = super().load()
        if not self.path.exists():
            data['entries'] = retained
        elif any(data['entries'].get(k) != v for k, v in retained.items()):
            raise ValueError('Historical reservations changed')
        return data

    def finish(self, identity, amount, evidence_hash, *, uncertain=False):
        if identity in retained_entries():
            raise ValueError('Historical reservations are immutable')
        return super().finish(identity, amount, evidence_hash, uncertain=uncertain)
