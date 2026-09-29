"""Offline boundaries for the single v14 correction; no provider calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import quality_completion_eval_v14 as runner
from scripts import quality_eval_contract_v13 as prior
from scripts import quality_eval_contract_v14 as contract
from scripts import quality_eval_transport_v14 as transport
from scripts.quality_completion_ledger import Ledger


class V14Boundaries(unittest.TestCase):
    def test_same_reducers_schema_coverage_and_bounded_transport(self):
        self.assertIs(contract.dimensions, prior.dimensions)
        self.assertIs(contract.schema, prior.schema)
        self.assertEqual(contract.COVERAGE_PROMPT, prior.COVERAGE_PROMPT)
        body = transport.initial_requests(runner.all_cases()['temporal-current-permission']['inputs'])[0][1]
        self.assertEqual(body['reasoning_effort'], 'medium')
        self.assertEqual(body['max_completion_tokens'], 4096)
        self.assertNotIn('required_facts', json.loads(body['messages'][1]['content']))
        self.assertIn(contract.TEMPORAL_RULES, contract.REVIEW_PROMPT)

    def test_declared_full_gate_and_all_temporal_controls(self):
        diagnostic = runner.plan('v14', 'diagnostic')
        self.assertEqual(diagnostic['maximum_calls'], 36)
        self.assertEqual(len(diagnostic['cases']), 12)
        full = runner.plan('v14', 'calibration')
        self.assertEqual((full['maximum_calls'], len(full['cases']), len(full['audit_ids'])), (75, 24, 3))
        cases = runner.all_cases()
        self.assertEqual(cases['temporal-ambiguous-topic']['expected']['overall'], 'fail')
        for cid in ['temporal-explicit-history', 'temporal-explicit-change', 'temporal-superseded-rule', 'temporal-condition-preserved']:
            self.assertEqual(cases[cid]['expected']['citation_support'], 'fail')

    def test_no_additional_candidate(self):
        with self.assertRaises(ValueError):
            runner.modules('v15')

    def test_failed_diagnostic_stops_and_cannot_be_retried_or_promoted(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            ledger = Ledger.initialize(folder/'api-ledger.json')
            with patch.object(runner, 'gate'), patch.object(transport, 'grade_case', side_effect=ValueError('invalid')) as grade:
                result = runner.execute('v14', 'diagnostic', None, ledger, folder)
            self.assertEqual((result['status'], result['completed'], grade.call_count), ('early_stopped', 1, 1))
            with self.assertRaises(runner.BudgetStop):
                runner.gate('v14', 'diagnostic', folder)
            with self.assertRaises(runner.BudgetStop):
                runner.gate('v14', 'calibration', folder)


if __name__ == '__main__':
    unittest.main()
