"""Offline checks of the funded one-shot runner; fake requests spend no money."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import Mock, patch
from openai.types.chat import ChatCompletion
import json
from scripts.test_structured_blind_evaluator_v1 import fixture, packet
from scripts import structured_blind_execution_v1 as runner
from scripts import structured_blind_execution_budget as budget
from scripts import structured_blind_measurement_v1 as final
from scripts import structured_blind_confirmation_v1 as confirmation


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(socket.socket, 'connect', side_effect=AssertionError('Offline only')))

    def ledger(self, spent='10.90614776', stage='diagnostic'):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.enterContext(patch.object(runner, 'ROOT', root))
        self.enterContext(patch.object(runner, 'FOLDER', root))
        plan = dict(stage=stage, prefix=dict(spent_usd=spent, ledger_sha256={}), maximum_calls=60)
        ledger = runner.RollingLedger(root / 'test/run', plan)
        self.enterContext(patch.object(runner, 'prefix', side_effect=lambda: dict(
            spent_usd=str(ledger.accounted), ledger_sha256={'test/run/api-ledger.json': runner.digest(ledger.folder / 'api-ledger.json')})))
        return ledger

    def body(self):
        return runner.transport.initial_requests(runner.cases('diagnostic')[0]['inputs'])[0][1]

    def test_replacement_balance_never_adds_old_remainder(self):
        result = budget.stage_budget('diagnostic')
        self.assertEqual(budget.CEILING, Decimal('20.75794526'))
        self.assertEqual(result['remaining_usd'], '9.85179750')
        self.assertGreater(Decimal(result['estimated_buffer_usd']), Decimal('2.89'))
        self.assertEqual(result['final_launch_floor_usd'], '4.50')
        approval = runner.read(budget.AUTHORIZATION)
        self.assertFalse(approval['previous_remainder_added'])
        self.assertEqual(approval['retained_hold_usd'], '0.14820250')

    def test_whole_path_blocks_stage_before_spending(self):
        with patch.object(budget, 'prefix', return_value=dict(spent_usd='14.00')):
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
        self.assertEqual(ledger.accounted, Decimal('10.90789776'))
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
            probe_ids=[c['id'] for c in runner.probes(stage)], maximum_calls=118,reuse=runner.reuse_for(stage,runner.cases(stage)),version=runner.contract.VERSION,
            provider_retries=0, output_caps=runner.transport.CAPS, total_ceiling_usd=str(budget.CEILING))
        runner.validate_plan('structured-blind-calibration', plan, runner.cases, runner.probes)
        bad = deepcopy(plan); bad['case_ids'].pop()
        with self.assertRaises(ValueError):
            runner.validate_plan('structured-blind-calibration', bad, runner.cases, runner.probes)
        with self.assertRaises(ValueError):
            runner.versioned('answer-dimensions.v34-candidate')
        with patch.object(confirmation, 'read', return_value=dict(version='answer-dimensions.v34-candidate')):
            with self.assertRaisesRegex(ValueError, 'Structured blind'):
                confirmation.readiness()

    def test_final_transport_retains_full_allowances_and_fresh_destination(self):
        ledger = final.MeasurementLedger.__new__(final.MeasurementLedger)
        ledger.mode='application'; ledger.case_id='fresh-001'
        ledger.case_calls={'fresh-001':{'application':0}}
        body=dict(model='gpt-5.4-2026-03-05',reasoning_effort='low',max_completion_tokens=1600,messages=[])
        self.assertEqual(ledger.prepare_request(body)[1]['output_cap'],1600)
        self.assertEqual(final.APP_CALLS,32)
        self.assertEqual(final.FOLDER.name,'final-blind-v1')
        with self.assertRaises(runner.transport.BudgetStop):
            ledger.prepare_request(dict(body,max_completion_tokens=2049))

    def test_live_adapter_reuses_one_coverage_receipt_and_only_charges_three_calls(self):
        case,grade=fixture('task-participant','diagnostic'); structured=packet(grade)
        reused=runner.reuse_for('diagnostic',[case])[case['id']]
        ledger=self.ledger();ledger.root=runner.references.legacy.ROOT
        calls=[]
        def create(**body):
            keys=body['response_format']['json_schema']['schema']['properties']
            value={k:structured[k] for k in keys}
            calls.append(body)
            return ChatCompletion.model_validate(dict(id='synthetic-'+str(len(calls)),object='chat.completion',created=0,
                model=body['model'],choices=[dict(index=0,finish_reason='stop',message=dict(role='assistant',content=json.dumps(value)))],
                usage=dict(prompt_tokens=100,completion_tokens=100,total_tokens=200)))
        first,second=runner.transport.grade_case(create,case['inputs'],ledger,ledger.folder/'raw/case',reused)
        self.assertEqual(len(calls),3)
        self.assertEqual(len(ledger.data['calls']),3)
        self.assertEqual(first,second)
        self.assertTrue(runner.judged(case,first,second)['matched'])
        self.assertEqual(runner.transport.replay(case['inputs'],ledger.folder/'raw/case'),(first,second))

    def test_final_grader_cannot_exceed_four_distinct_calls(self):
        ledger=final.MeasurementLedger.__new__(final.MeasurementLedger)
        ledger.mode='grading';ledger.case_id='fresh-001';ledger.case_calls={'fresh-001':{'grading':4}}
        with self.assertRaises(runner.transport.BudgetStop): ledger.prepare_request(self.body())


if __name__ == '__main__':
    unittest.main()
