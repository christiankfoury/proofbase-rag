"""No-network custody, references and full 16-case Batch confirmation replay."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import quality_confirmation_batch2_v18 as runner
from scripts.quality_completion_durable import write_json_atomic as write
from scripts import test_quality_cost_control as cost_tests


class ConfirmationBatch(unittest.TestCase):
    def test_development_failure_blocks_before_fresh_suite(self):
        with patch.object(runner.previous, 'readiness', side_effect=ValueError('development failed')), \
             patch.object(runner.previous.original, 'load_suite') as load:
            with self.assertRaisesRegex(ValueError, 'development failed'):
                runner.custody()
            load.assert_not_called()

    def test_changed_freeze_blocks_before_fresh_suite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'freeze.json'; write(path, {'readiness_sha256': 'changed'})
            with patch.object(runner, 'FREEZE', path), patch.object(runner.previous, 'readiness', return_value='ready'), \
                 patch.object(runner.previous.original, 'load_suite') as load:
                with self.assertRaisesRegex(ValueError, 'freeze changed'):
                    runner.custody()
                load.assert_not_called()

    def test_reference_disagreement_is_not_silently_accepted(self):
        suite = runner.previous.load_suite()
        validation = runner.read(runner.previous.VALIDATION)
        freeze = runner.read(runner.previous.FREEZE)
        runner.check_references(suite, validation, freeze)
        validation['case_reviews'][0]['independently_derived_expected']['overall'] = 'unresolved'
        with self.assertRaisesRegex(ValueError, 'Independent references'):
            runner.check_references(suite, validation, freeze)

    def test_sixteen_case_replay_and_single_attempt(self):
        fixture = cost_tests.CostControls(methodName='runTest')
        fixture.setUp()
        try:
            from scripts.quality_eval_calibration_v12 import load_suite
            cases = deepcopy(load_suite()['cases'][:16])
            for case in cases:
                saved = runner.read(runner.ROOT / 'data/evaluation/quality-completion-v1/v18-calibration' / (case['id'] + '.json'))
                case['expected_fact_statuses'] = {f['fact_id']: f['status'] for f in saved['grade']['facts']}
            out = fixture.folder / 'confirmation'
            with patch.object(runner, 'OUT', out), patch.object(runner, 'POLICY', fixture.policy_path), \
                 patch.object(runner, 'custody', return_value=({'cases': cases}, fixture.bindings)), \
                 patch.object(runner, 'live_policy'), patch.object(runner, 'retained_entries', return_value={}), patch.object(runner, 'SEAL', runner.previous.SEAL):
                runner.prepare('initial')
                with self.assertRaisesRegex(ValueError, 'exists'):
                    runner.prepare('initial')
                for wave in ('initial', 'review'):
                    if wave == 'review':
                        runner.prepare('review')
                    job = out / wave
                    runner.batch.submit(job, fixture.client, fixture.journal)
                    fixture.terminal(job)
                    self.assertEqual(runner.batch.collect(job, fixture.client, fixture.journal)['status'], 'complete')
                    write(out / 'additional-spend.json', fixture.journal.load())
                report = runner.replay()
                self.assertEqual((report['matched'], report['count'], report['calls']), (16, 16, 48))
                self.assertFalse(report['semantic_validation_passed'])
                journal = fixture.journal.load()
                next(iter(journal['entries'].values()))['accounted_usd'] = '0'
                write(out / 'additional-spend.json', journal)
                with self.assertRaisesRegex(ValueError, 'settlement mismatch'):
                    runner.replay()
        finally:
            fixture.doCleanups()


if __name__ == '__main__':
    unittest.main()
