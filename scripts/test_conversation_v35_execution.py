"""Offline checks of the funded one-shot runner; fake requests spend no money."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import Mock, patch
from openai.types.chat import ChatCompletion
from scripts import conversation_grader_v12 as runner
from scripts import conversation_v35_budget as budget
from scripts import conversation_measurement_v13 as final
from scripts import conversation_confirmation_v12 as confirmation


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(socket.socket, 'connect', side_effect=AssertionError('Offline only')))

    def ledger(self, spent='9.31867776', stage='diagnostic'):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.enterContext(patch.object(runner, 'ROOT', root))
        self.enterContext(patch.object(runner, 'FOLDER', root))
        plan = dict(stage=stage, prefix=dict(spent_usd=spent, ledger_sha256={}), maximum_calls=51)
        ledger = runner.RollingLedger(root / 'test/run', plan)
        self.enterContext(patch.object(runner, 'prefix', side_effect=lambda: dict(
            spent_usd=str(ledger.accounted), ledger_sha256={'test/run/api-ledger.json': runner.digest(ledger.folder / 'api-ledger.json')})))
        return ledger

    def body(self):
        return runner.transport.initial_requests(runner.cases('diagnostic')[0]['inputs'])[0][1]

    def test_replacement_balance_never_adds_old_remainder(self):
        result = budget.stage_budget('diagnostic')
        self.assertEqual(budget.CEILING, Decimal('16.77047526'))
        self.assertEqual(result['remaining_usd'], '7.45179750')
        self.assertEqual(result['estimated_buffer_usd'], '0.47074825')
        self.assertEqual(result['final_launch_floor_usd'], '4.50')
        approval = runner.read(budget.AUTHORIZATION)
        self.assertFalse(approval['previous_remainder_added'])
        self.assertEqual(approval['retained_hold_usd'], '0.14820250')

    def test_whole_path_blocks_stage_before_spending(self):
        with patch.object(budget, 'prefix', return_value=dict(spent_usd='11.00')):
            with self.assertRaisesRegex(ValueError, 'whole path'):
                budget.stage_budget('diagnostic')

    def test_final_floor_blocks_qualification_request(self):
        ledger = self.ledger(spent=str(budget.CEILING-budget.FINAL_FLOOR-Decimal('.01')))
        provider = Mock()
        with self.assertRaises(runner.transport.BudgetStop):
            ledger.call(provider, self.body(), ledger.folder / 'raw.json')
        provider.assert_not_called()
        self.assertEqual(ledger.data['calls'], [])

    def test_receipt_is_reserved_first_and_settled_without_retry(self):
        ledger = self.ledger()
        def create(**body):
            self.assertEqual(runner.read(ledger.folder/'api-ledger.json')['calls'][0]['status'], 'reserved')
            return ChatCompletion.model_validate(dict(id='synthetic',object='chat.completion',created=0,model=body['model'],
                choices=[dict(index=0,finish_reason='stop',message=dict(role='assistant',content='{}'))],
                usage=dict(prompt_tokens=100,completion_tokens=100,total_tokens=200)))
        provider = Mock(side_effect=create)
        ledger.call(provider, self.body(), ledger.folder/'raw.json')
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(ledger.accounted, Decimal('9.32042776'))
        self.assertFalse(ledger.data['unknown_outcome'])
        with self.assertRaises(runner.transport.BudgetStop):
            ledger.call(provider, self.body(), ledger.folder/'raw.json')
        self.assertEqual(provider.call_count, 1)

    def test_unknown_request_keeps_full_reservation_and_stops(self):
        ledger = self.ledger()
        provider = Mock(side_effect=TimeoutError('Synthetic unknown outcome'))
        body = self.body()
        with self.assertRaises(TimeoutError):
            ledger.call(provider, body, ledger.folder/'raw.json')
        self.assertTrue(ledger.data['stopped'])
        self.assertTrue(ledger.data['unknown_outcome'])
        self.assertEqual(Decimal(ledger.data['calls'][0]['accounted_usd']), runner.transport.reserve(body)['reserved_usd'])
        with self.assertRaises(runner.transport.BudgetStop):
            ledger.call(provider, body, ledger.folder/'retry.json')
        self.assertEqual(provider.call_count, 1)

    def test_no_subset_version_reuse_or_unqualified_confirmation(self):
        stage = 'calibration'
        plan = dict(stage=stage, case_ids=[c['id'] for c in runner.cases(stage)],
            probe_ids=[c['id'] for c in runner.probes(stage)], maximum_calls=99,
            provider_retries=0, output_caps=runner.transport.CAPS, total_ceiling_usd=str(budget.CEILING))
        runner.validate_plan('grader-v35-calibration', plan, runner.cases, runner.probes)
        bad = deepcopy(plan); bad['case_ids'].pop()
        with self.assertRaises(ValueError):
            runner.validate_plan('grader-v35-calibration', bad, runner.cases, runner.probes)
        with self.assertRaises(ValueError):
            runner.versioned('answer-dimensions.v34-candidate')
        with patch.object(confirmation, 'read', return_value=dict(version='answer-dimensions.v34-candidate')):
            with self.assertRaisesRegex(ValueError, 'V35'):
                confirmation.readiness()

    def test_final_transport_retains_full_allowances_and_fresh_destination(self):
        ledger = final.MeasurementLedger.__new__(final.MeasurementLedger)
        ledger.mode='application'; ledger.case_id='fresh-001'
        ledger.case_calls={'fresh-001':{'application':0}}
        body=dict(model='gpt-5.4-2026-03-05',reasoning_effort='low',max_completion_tokens=1600,messages=[])
        self.assertEqual(ledger.prepare_request(body)[1]['output_cap'],1600)
        self.assertEqual(final.APP_CALLS,32)
        self.assertEqual(final.FOLDER.name,'final-v3')
        with self.assertRaises(runner.transport.BudgetStop):
            ledger.prepare_request(dict(body,max_completion_tokens=2049))


if __name__ == '__main__':
    unittest.main()
