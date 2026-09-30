"""Pre-freeze confirmation custody and fact-status checks; no provider calls."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import quality_confirmation_v15 as runner
from scripts.quality_confirmation_fact_checks import check_fact_references
from scripts.quality_completion_eval_v15 import controls


class ConfirmationCustody(unittest.TestCase):
    def test_missing_or_inconsistent_fact_references_are_rejected(self):
        data = controls()
        cases = deepcopy(data['cases'])
        for case in cases:
            case['expected_fact_statuses'] = data['fact_status_expectations'][case['id']]
        self.assertEqual(check_fact_references({'cases':cases}), 4)
        cases[0]['expected_fact_statuses'] = {}
        with self.assertRaisesRegex(ValueError, 'Invalid fact-status reference'):
            check_fact_references({'cases':cases})
        cases[0]['expected_fact_statuses'] = {'F1':'covered'}
        with self.assertRaisesRegex(ValueError, 'Fact-status/completeness mismatch'):
            check_fact_references({'cases':cases})

    def test_development_failure_blocks_before_confirmation_load(self):
        with patch('scripts.report_quality_v15_recovery.replay', return_value={'matching_judgments':0}), \
             patch.object(runner, 'load_suite') as load:
            with self.assertRaisesRegex(ValueError, 'Development calibration'):
                runner.execute(lambda **kw:self.fail('Provider called'), None)
            load.assert_not_called()

    def test_changed_freeze_blocks_before_confirmation_load(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            freeze,gate=folder/'freeze.json',folder/'gate.json'
            gate.write_text('{}');freeze.write_text(json.dumps({'readiness_sha256':'changed'}))
            with patch.object(runner,'FREEZE',freeze), patch.object(runner,'GATE',gate), \
                 patch.object(runner,'load_suite') as load:
                with self.assertRaisesRegex(ValueError,'Evaluator freeze changed'):
                    runner.preflight(None)
                load.assert_not_called()

    def test_single_attempt_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);(folder/'confirmation-v15-01').mkdir()
            with patch.object(runner,'FOLDER',folder), patch.object(runner,'readiness',return_value='ready'), \
                 patch.object(runner,'preflight',return_value={}):
                with self.assertRaises(FileExistsError):
                    runner.execute(lambda **kw:self.fail('Provider called'),None)


if __name__ == '__main__':
    unittest.main()
