"""Offline regression checks; no fresh qualification or release credit."""
from copy import deepcopy
import socket
import unittest
from unittest.mock import patch
from scripts import structured_blind_evaluator_v2 as evaluator
from scripts import structured_blind_evaluator_v1 as previous
from scripts.test_structured_blind_evaluator_v1 import fixture, packet, ambiguous
from scripts.bounded_redesign_run import read
from scripts.conversation_ordering_v2 import cases, legacy


def compare(module, case, first, second):
    return module.compare(case['inputs'], case['payload'], case['evidence'],
                          case['safety_flags'], first, second)


class EmptyReferenceTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(socket.socket, 'connect', side_effect=AssertionError('Offline only')))

    def test_recorded_failure_stays_failed_and_v1_unchanged(self):
        case = next(c for c in cases('diagnostic') if c['id'] == 'verified-identity')
        row = read(legacy.FOLDER/'structured-blind-diagnostic/run/verified-identity.json')
        snapshot = deepcopy(row)
        first, second = row['grade'], row['review']
        old = compare(previous, case, first, second)
        new = compare(evaluator, case, first, second)
        self.assertEqual(old['disputed_dimensions'], ['forbidden_assertion'])
        self.assertEqual(new['status'], 'agreement_only')
        self.assertEqual(new['observed_forbidden_labels'], ['absent', 'present'])
        self.assertEqual(new['dimensions']['overall'], 'fail')
        self.assertEqual(new['dimensions']['factual_support'], 'unresolved')
        self.assertEqual(new['dimensions']['citation_support'], 'fail')
        self.assertFalse(new['target_credit'])
        self.assertFalse(new['release_eligible'])
        self.assertEqual(row, snapshot)

    def test_nonempty_forbidden_disagreement_and_present_are_preserved(self):
        case, grade = fixture(); first = packet(grade); second = deepcopy(first)
        case['inputs']['forbidden_assertions'] = ['A specific disallowed proposition.']
        first['forbidden_assertion'] = 'absent'; second['forbidden_assertion'] = 'present'
        result = compare(evaluator, case, first, second)
        self.assertIn('forbidden_assertion', result['disputed_dimensions'])
        self.assertFalse(result['candidate_pass'])
        self.assertEqual(compare(evaluator, case, second, second)['dimensions']['overall'], 'fail')

    def test_other_disagreements_and_ambiguity_are_preserved(self):
        case, first = ambiguous(); second = deepcopy(first)
        first['forbidden_assertion'] = 'present'; second['forbidden_assertion'] = 'unknown'
        result = compare(evaluator, case, first, second)
        self.assertEqual(result['dimensions']['citation_support'], 'unresolved')
        self.assertEqual(result['dimensions']['completeness'], 'fail')
        self.assertFalse(result['candidate_pass'])
        second['facts'][0]['status'] = 'missing'; second['facts'][0]['answer_spans'] = []
        self.assertIn('completeness', compare(evaluator, case, first, second)['disputed_dimensions'])

    def test_invalid_output_and_permission_flags_cannot_be_repaired(self):
        case, grade = fixture(); value = packet(grade)
        value['forbidden_assertion'] = 'present'
        invalid = deepcopy(value); invalid['claims'][0]['readings'][0]['context_spans'] = [{'id':'A','span':'invented witness'}]
        self.assertEqual(compare(evaluator, case, invalid, invalid)['status'], 'invalid')
        case['safety_flags'] = ['unauthorized_document']
        result = compare(evaluator, case, value, value)
        self.assertEqual(result['dimensions']['overall'], 'fail')
        self.assertFalse(result['candidate_pass'])
        self.assertEqual(compare(evaluator, case, None, None)['status'], 'invalid')

    def test_unknowns_are_resolved_only_for_explicit_empty_set(self):
        case, grade = fixture(); first = packet(grade); second = deepcopy(first)
        first['forbidden_assertion'] = 'unknown'; second['forbidden_assertion'] = 'present'
        self.assertEqual(compare(evaluator, case, first, second)['dimensions']['forbidden_assertion'], 'absent')
        case['inputs']['forbidden_assertions'] = ['A specific disallowed proposition.']
        self.assertEqual(compare(evaluator, case, first, second)['dimensions']['forbidden_assertion'], 'unresolved')

    def test_requests_and_all_other_existing_labels_are_identical(self):
        for stage in ('diagnostic', 'calibration'):
            for case in cases(stage):
                self.assertEqual(evaluator.request_plan(case['inputs']), previous.request_plan(case['inputs']))
        case, grade = fixture(); value = packet(grade)
        old, new = compare(previous, case, value, value), compare(evaluator, case, value, value)
        self.assertEqual(old['dimensions'], new['dimensions'])
        self.assertEqual(old['grader_errors'], new['grader_errors'])


if __name__ == '__main__':
    unittest.main()
