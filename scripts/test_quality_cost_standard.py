"""Terminal cancellation and retained-cost continuation checks; no network."""
from contextlib import ExitStack
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import quality_cost_standard as cost
from scripts.quality_completion_durable import write_json_atomic as write


class StandardContinuation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'data/evaluation/quality-completion-v1/confirmation-v18-batch2-01/initial'
        self.folder.mkdir(parents=True)
        self.original = cost.prior.retained_entries()
        self.raw = cost.read(cost.ROOT / 'data/evaluation/quality-completion-v1/v18-calibration/unsupported-extra-benefit/claims.json')
        self.requests = [{'custom_id': 'one', 'body': self.raw['request']},
                         {'custom_id': 'two', 'body': self.raw['request']}]
        self.state = {'batch_id': 'batch-test', 'input_file_id': 'input-test', 'journal_identity': 'batch-test'}
        self.status = {'status': 'cancelled', 'id': 'batch-test', 'input_file_id': 'input-test',
                       'request_counts': {'failed': 0, 'completed': 1, 'total': 2}}
        output = {'custom_id': 'one', 'error': None, 'response': {'status_code': 200, 'body': self.raw['response']}}
        (self.folder / 'output.jsonl').write_text(json.dumps(output) + '\n', encoding='utf-8')
        self.result = {'batch_id': 'batch-test', 'successful_responses': 1, 'expected_responses': 2,
                       'errors': ['two', 'batch_cancelled'],
                       'cache_aware_estimate_usd': str(cost.charge(self.raw['response'], 'batch')),
                       'raw_files_sha256': {'output.jsonl': cost.digest(self.folder / 'output.jsonl')}}
        self.policy_path = self.root / 'policy.json'
        self.policy = deepcopy(cost.read(cost.prior.POLICY))
        self.refresh()
        stack = ExitStack(); self.addCleanup(stack.close)
        stack.enter_context(patch.object(cost, 'ROOT', self.root))
        stack.enter_context(patch.object(cost, 'POLICY', self.policy_path))
        stack.enter_context(patch.object(cost.prior, 'live_policy', return_value=(self.policy, Decimal(10))))
        stack.enter_context(patch.object(cost.prior, 'retained_entries', return_value=self.original))
        stack.enter_context(patch.object(cost.prior, 'bound_file', side_effect=self.bound_file))
        stack.enter_context(patch.object(cost, 'verify', side_effect=lambda _: ({'count': 2}, self.state, self.requests)))

    def bound_file(self, binding):
        path = self.root / binding['path']
        if cost.digest(path) != binding['sha256']:
            raise ValueError('Continuation evidence changed')
        return path

    def refresh(self):
        for name, value in [('provider-status.json', self.status), ('result.json', self.result), ('state.json', self.state)]:
            write(self.folder / name, value)
        old = {'policy_sha256': cost.digest(cost.prior.POLICY), 'entries': deepcopy(self.original)}
        old['entries']['batch-test'] = {'status': 'unknown', 'reserved_usd': '1.40505625',
            'accounted_usd': '1.40505625', 'result_sha256': cost.digest(self.folder / 'result.json')}
        write(self.root / 'old-journal.json', old)
        self.policy['transition_journal'] = {'path': 'old-journal.json', 'sha256': cost.digest(self.root / 'old-journal.json')}
        self.policy['cancellation_evidence_sha256'] = {p.relative_to(self.root).as_posix(): cost.digest(p) for p in self.folder.iterdir()}
        write(self.policy_path, self.policy)

    def test_terminal_partial_cost_preserves_full_reservation_and_cap(self):
        _, limit = cost.live_policy(self.policy_path)
        self.assertEqual(limit, Decimal(10))
        retained = cost.retained_entries()
        self.assertEqual(sum(Decimal(r['accounted_usd']) for r in retained.values()), Decimal('2.80849875'))
        self.assertEqual(retained['batch-test']['accounting_basis'], 'cancelled_batch_full_reservation_retained')
        journal = cost.SpendJournal(self.root / 'new', self.policy_path)
        with patch('scripts.quality_batch_transport.live_policy', return_value=(self.policy, Decimal(10))):
            with self.assertRaisesRegex(ValueError, 'ceiling'):
                journal.reserve('new', Decimal('7.2'), 'plan')
            journal.reserve('new', Decimal(1), 'plan')
        with self.assertRaisesRegex(ValueError, 'immutable'):
            journal.finish('batch-test', Decimal(0), 'changed')
        data = journal.load(); del data['entries']['batch-test']; write(journal.path, data)
        with self.assertRaisesRegex(ValueError, 'Historical reservations'):
            journal.load()

    def test_pending_or_incomplete_results_block(self):
        for change in ['pending', 'missing', 'usage']:
            with self.subTest(change=change):
                self.status['status'] = 'cancelling' if change == 'pending' else 'cancelled'
                self.status['request_counts']['completed'] = 2 if change == 'missing' else 1
                if change == 'usage':
                    self.result['cache_aware_estimate_usd'] = '0'
                self.refresh()
                with self.assertRaises(ValueError):
                    cost.live_policy(self.policy_path)

    def test_raw_binding_and_content_tampering_block(self):
        del self.policy['cancellation_evidence_sha256'][(self.folder / 'output.jsonl').relative_to(self.root).as_posix()]
        with self.assertRaisesRegex(ValueError, 'binding missing'):
            cost.live_policy(self.policy_path)
        self.refresh()
        (self.folder / 'output.jsonl').write_text('{}\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            cost.live_policy(self.policy_path)


if __name__ == '__main__':
    unittest.main()
