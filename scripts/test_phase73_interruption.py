"""Offline controls for honest interrupted publication and cost retention."""
from copy import deepcopy
import unittest
from unittest.mock import patch
from scripts import report_phase73_interruption as report


class InterruptionTests(unittest.TestCase):
    def setUp(self):
        self.data = report.read(report.FOLDER/'run/api-ledger.json')
        self.calls = self.data['calls'][self.data['prior_calls']:]
        self.row = deepcopy(self.calls[-1])
        self.raw = report.read(report.FOLDER/self.row['raw_path'])

    def test_unknown_reservation_is_not_a_settled_charge(self):
        report.validate_unknown(self.row, self.raw)
        self.row['charged_usd'] = '0'
        with self.assertRaises(ValueError):
            report.validate_unknown(self.row, self.raw)

    def test_cannot_invent_usage_or_response(self):
        self.row['output_tokens'] = 0
        with self.assertRaises(ValueError):
            report.validate_unknown(self.row, self.raw)
        self.row['output_tokens'] = None
        self.raw['response'] = {'usage': {'prompt_tokens': 0}}
        with self.assertRaises(ValueError):
            report.validate_unknown(self.row, self.raw)

    def test_changed_request_rejected(self):
        self.raw['request']['max_completion_tokens'] -= 1
        with self.assertRaises(ValueError):
            report.validate_unknown(self.row, self.raw)

    def test_journal_cannot_release_unknown_reservation(self):
        original = report.read
        def altered(path):
            value = original(path)
            if path == report.FOLDER/'run/additional-spend.json':
                value['entries'][self.row['additional_spend_identity']]['accounted_usd'] = '0'
            return value
        with patch.object(report, 'read', altered), self.assertRaises(ValueError):
            report.audit_spend(self.calls)

    def test_full_replay_has_no_qualified_score_or_resume(self):
        value = report.replay()
        self.assertEqual((value['completed_cases'], value['captured_cases'], value['unexecuted_cases']), (10, 11, 49))
        self.assertEqual((value['settled_calls'], value['unknown_calls']), (93, 1))
        self.assertIsNone(value['validated_passes'])
        self.assertFalse(value['source_inspection_passed'])
        self.assertFalse(value['target_met'])
        self.assertEqual(value['unknown_reserved_usd'], self.row['reserved_usd'])
        self.assertTrue(self.data['unknown_outcome'])


if __name__ == '__main__':
    unittest.main()
