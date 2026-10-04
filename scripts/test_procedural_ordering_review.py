"""Offline specification checks; no model accuracy or reference adjudication."""
from copy import deepcopy
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from scripts import conversation_grader_v11 as legacy
from scripts import conversation_blind_review_design as blind
from scripts.bounded_redesign_run import read, digest
from scripts.quality_confirmation_reference_checks import check_references

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/evaluation/conversation-continuation'
REVIEW = FOLDER / 'ordering-contract-v1'


class OrderingReviewTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(socket.socket, 'connect', side_effect=AssertionError('Offline only')))

    def disputed(self):
        case = next(c for c in legacy.cases('calibration') if c['id'] == 'answer-injection-award-pass')
        grade = {}
        for stage in ('claims', 'coverage'):
            path = FOLDER / 'grader-v34-calibration/run/raw' / case['id'] / (stage + '.json')
            grade.update(json.loads(read(path)['response']['choices'][0]['message']['content']))
        return case, grade

    def synthetic_reducer_review(self):
        # Only exercise the existing reducer. This is NOT a model review receipt.
        return dict(reason='Synthetic reducer test only; no semantic approval.',
                    **{k: 'agree' for k in (*legacy.contract.DIMENSIONS, 'forbidden_assertion')})

    def test_eight_references_are_structurally_consistent(self):
        suite = read(REVIEW / 'review-cases.json')
        self.assertEqual(check_references(suite), 8)
        self.assertFalse(suite['release_credit'])
        # The unchanged legacy case predates expected_fact_statuses. Its exact
        # object is checked separately; do not retrofit fields into old evidence.
        for case in suite['cases'][:-1]:
            self.assertEqual(set(case['expected_fact_statuses']),
                             {f['fact_id'] for f in case['inputs']['required_facts']})

    def test_original_case_and_all_qualification_controls_remain_unchanged(self):
        case, _ = self.disputed()
        original = read(REVIEW / 'review-cases.json')['cases'][-1]
        self.assertEqual(original, case)
        self.assertEqual(len(legacy.cases('calibration')), 24)
        self.assertEqual(len(legacy.probes('calibration')), 3)
        report = read(FOLDER / 'grader-v34-calibration/report.json')
        self.assertEqual((report['status'], report['count'], report['matched']),
                         ('early_stopped', 22, 21))

    def test_historical_evidence_and_every_ledger_hash_are_preserved(self):
        manifest = read(REVIEW / 'review-manifest.json')
        for group in ('immutable_bindings', 'ledger_bindings'):
            for path, expected in manifest[group].items():
                self.assertEqual(digest(ROOT / path), expected, path)

    def test_either_disputed_reading_retains_the_confirmed_answer_failure(self):
        case, sequence = self.disputed()
        presentation = deepcopy(sequence)
        claim = presentation['claims'][0]
        claim.update(factual_status='supported', citation_status='supported',
                     reason='Hypothetical presentation reading for reducer testing only.',
                     source_spans=[dict(id='R1', span='report the missing card to reception')],
                     citation_spans=[dict(id='C1', span='report the missing card to reception')])
        for grade in (sequence, presentation):
            result = legacy.contract.dimensions(case['inputs'], grade, case['payload'],
                case['evidence'], case['safety_flags'], self.synthetic_reducer_review())
            self.assertEqual(result['grader_errors'], [])
            self.assertEqual(result['completeness'], 'fail')
            self.assertEqual(result['response_behavior'], 'fail')
            self.assertEqual(result['overall'], 'fail')
            self.assertFalse(result['target_credit'])
        compared = blind.compare(case, sequence, presentation)
        self.assertEqual(compared['status'], 'unresolved_disagreement')
        self.assertFalse(compared['target_credit'])

    def test_proposed_ambiguity_mapping_does_not_erase_a_known_failure(self):
        case, grade = self.disputed()
        grade['claims'][0].update(factual_status='unknown', citation_status='unknown',
                                 source_spans=[], citation_spans=[])
        result = legacy.contract.dimensions(case['inputs'], grade, case['payload'],
            case['evidence'], case['safety_flags'], self.synthetic_reducer_review())
        self.assertEqual(result['grader_errors'], [])
        self.assertEqual(result['factual_support'], 'unresolved')
        self.assertEqual(result['citation_support'], 'unresolved')
        self.assertEqual(result['overall'], 'fail')
        self.assertFalse(result['target_credit'])
        self.assertFalse(blind.compare(case, grade, grade)['release_eligible'])

    def test_pilot_remains_unexecuted_and_contract_is_not_activated(self):
        proposal = read(FOLDER / 'blind-review-design/proposal.json')
        manifest = read(REVIEW / 'review-manifest.json')
        self.assertEqual(proposal['status'], 'proposed_not_authorized_not_executed')
        self.assertEqual(manifest['pilot_disposition'], 'deferred_not_authorized')
        self.assertFalse(manifest['runtime_changed'])
        self.assertFalse(manifest['reference_correction_applied'])
        self.assertEqual(manifest['new_paid_calls'], 0)


if __name__ == '__main__':
    unittest.main()
