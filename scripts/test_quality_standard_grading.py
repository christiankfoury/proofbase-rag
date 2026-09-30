"""Offline synchronous transport equivalence and cost/failure gates."""
from decimal import Decimal
from unittest.mock import Mock
import unittest
from openai.types.chat import ChatCompletion
from scripts import quality_standard_grading as standard
from scripts import test_quality_cost_control as fixtures
from scripts import quality_eval_transport_v18 as transport
from scripts.quality_eval_calibration_v12 import load_suite
from scripts.quality_cost_control import read
from scripts.quality_completion_durable import write_json_atomic as write


class StandardCalls(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CostControls(methodName='runTest')
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.folder = self.fixture.folder / 'standard'

    def test_all_saved_calibration_requests_and_results_are_unchanged(self):
        ledger = standard.StandardLedger(self.folder, self.fixture.journal, maximum_calls=72)
        requests = []
        for case in load_suite()['cases']:
            saved_folder = fixtures.batch.ROOT / 'data/evaluation/quality-completion-v1/v18-calibration' / case['id']
            rows = iter(read(saved_folder / (purpose + '.json')) for purpose in ['claims','coverage','review'])
            def create(**body):
                raw = next(rows); self.assertEqual(body, raw['request']); requests.append(body)
                return ChatCompletion.model_validate(raw['response'])
            grade, review = transport.grade_case(create, case['inputs'], ledger, self.folder / case['id'])
            saved = read(saved_folder.parent / (case['id'] + '.json'))
            self.assertEqual(grade, saved['grade']); self.assertEqual(review, saved['review'])
        self.assertEqual(len(requests), 72)
        self.assertGreater(standard.audit(self.folder, requests, self.fixture.journal), 0)
        with self.assertRaisesRegex(transport.BudgetStop, 'exists'):
            standard.StandardLedger(self.folder, self.fixture.journal)
        path = self.folder / read(ledger.path)['calls'][0]['path']
        raw = read(path); raw['response']['usage']['completion_tokens'] += 1; write(path, raw)
        with self.assertRaisesRegex(ValueError, 'settlement changed'):
            standard.audit(self.folder, requests, self.fixture.journal)

    def test_pending_batch_prevents_starting_a_replacement(self):
        self.fixture.journal.reserve('batch-pending', Decimal(1), 'plan')
        with self.assertRaisesRegex(transport.BudgetStop, 'Pending'):
            standard.StandardLedger(self.folder, self.fixture.journal)
        self.assertFalse(self.folder.exists())

    def test_timeout_preserves_reservation_and_blocks_next_call(self):
        ledger = standard.StandardLedger(self.folder, self.fixture.journal)
        body = transport.initial_requests(self.fixture.cases[0]['inputs'])[0][1]
        provider = Mock(side_effect=TimeoutError())
        with self.assertRaises(TimeoutError):
            ledger.call(provider, body, self.folder / 'once.json')
        with self.assertRaisesRegex(transport.BudgetStop, 'Unknown'):
            ledger.call(provider, body, self.folder / 'again.json')
        self.assertEqual(provider.call_count, 1)
        row = next(iter(self.fixture.journal.load()['entries'].values()))
        self.assertEqual(row['status'], 'unknown')
        self.assertEqual(row['accounted_usd'], row['reserved_usd'])

    def test_cap_and_sdk_retries_block_before_provider(self):
        from openai import OpenAI
        ledger = standard.StandardLedger(self.folder, self.fixture.journal)
        body = transport.initial_requests(self.fixture.cases[0]['inputs'])[0][1]
        client = OpenAI(api_key='unused-test-credential', max_retries=2)
        with self.assertRaisesRegex(transport.BudgetStop, 'retries'):
            ledger.call(client.chat.completions.create, body, self.folder / 'retry.json')
        self.fixture.journal.reserve('prior', Decimal('9.99'), 'prior')
        self.fixture.journal.finish('prior', Decimal('9.99'), 'settled')
        provider = Mock()
        with self.assertRaisesRegex(transport.BudgetStop, 'ceiling'):
            ledger.call(provider, body, self.folder / 'over-budget.json')
        provider.assert_not_called()
        self.assertEqual(read(ledger.path)['calls'], [])


if __name__ == '__main__':
    unittest.main()
