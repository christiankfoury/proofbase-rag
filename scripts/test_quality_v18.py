"""Regression checks for semantic status blindness and stage custody; no API calls."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import quality_completion_eval_v18 as runner
from scripts import quality_eval_contract_v17 as prior
from scripts import quality_eval_contract_v18 as contract
from scripts.quality_completion_ledger_v18 import Ledger


class TaskContextCorrection(unittest.TestCase):
    def test_historical_error_is_caught_without_relabeling_saved_evidence(self):
        path = runner.FOLDER/'v14-calibration/true-answer-wrong-topic.json'
        before = path.read_bytes()
        row = json.loads(before)
        case = runner.all_cases()['true-answer-wrong-topic']
        self.assertEqual(runner.baseline.compare(case, row['grade'], row['dimensions']), {})
        self.assertIn('fact_statuses', runner.compare(case, row['grade'], row['dimensions']))
        fixed = deepcopy(row['grade'])
        fixed['facts'][0].update(status='missing', answer_spans=[])
        self.assertEqual(runner.compare(case, fixed, row['dimensions']), {})
        self.assertEqual(path.read_bytes(), before)

    def test_existing_reducers_claim_rubric_and_dimensions_remain(self):
        self.assertIs(contract.dimensions, prior.dimensions)
        self.assertIs(contract.schema, prior.schema)
        self.assertTrue(contract.CLAIM_PROMPT.endswith(contract.CONTEXT_RULES))
        self.assertEqual(contract.COVERAGE_PROMPT, prior.COVERAGE_PROMPT)
        self.assertEqual(contract.DIMENSIONS, prior.DIMENSIONS)
        cases = runner.all_cases()
        for cid, expected in runner.controls()['fact_status_expectations'].items():
            self.assertEqual(set(expected), {f['fact_id'] for f in cases[cid]['inputs']['required_facts']})

    def test_preflight_captures_original_full_gate_and_extra_probe(self):
        diagnostic = runner.plan('v18', 'diagnostic')
        self.assertEqual((len(diagnostic['cases']), len(diagnostic['audit_ids']), diagnostic['maximum_calls']), (29, 4, 91))
        full = runner.plan('v18', 'calibration')
        self.assertEqual((len(full['cases']), len(full['audit_ids']), full['maximum_calls']), (24, 3, 75))

    def test_only_named_diagnostic_permits_91_calls(self):
        from decimal import Decimal
        with tempfile.TemporaryDirectory() as temp:
            ledger=Ledger.initialize(Path(temp)/'api-ledger.json')
            with self.assertRaises(runner.BudgetStop):
                ledger.begin_stage('v18-calibration',91,Decimal(10))
            with self.assertRaises(runner.BudgetStop):
                ledger.begin_stage('v18-diagnostic',92,Decimal(10))
            ledger.begin_stage('v18-diagnostic',91,Decimal(10))
            self.assertEqual(ledger.data['stage']['maximum_calls'],91)
            ledger.finish_stage()

    def test_failed_extra_probe_blocks_promotion(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder/'v18-diagnostic').mkdir()
            manifest = {'status':'complete','matched':29,'review_rows':{'probe':{'exact_match':False}}}
            (folder/'v18-diagnostic/manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(runner.BudgetStop, 'Diagnostic did not pass'):
                runner.gate('v18', 'calibration', folder)

    def test_diagnostic_stops_first_error_and_cannot_be_repeated(self):
        _, transport = runner.modules('v18')
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            ledger = Ledger.initialize(folder/'api-ledger.json')
            with patch.object(runner, 'gate'), patch.object(transport, 'grade_case', side_effect=ValueError('invalid')) as grade:
                result = runner.execute('v18', 'diagnostic', None, ledger, folder)
            self.assertEqual((result['status'], result['completed'], grade.call_count), ('early_stopped', 1, 1))
            with self.assertRaises(runner.BudgetStop):
                runner.gate('v18', 'diagnostic', folder)


if __name__ == '__main__':
    unittest.main()
