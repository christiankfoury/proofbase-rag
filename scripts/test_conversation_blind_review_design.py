"""Offline isolation, intermediate disagreement and fail-closed checks."""
from copy import deepcopy
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from scripts import conversation_blind_review_design as design
from scripts import conversation_grader_v11 as existing

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / 'data/evaluation/conversation-continuation/grader-v34-calibration/run'


def fixture(name):
    case = next(c for c in existing.cases('calibration') if c['id'] == name)
    grade = {}
    for stage in ('claims', 'coverage'):
        raw = json.loads((SAVED / 'raw' / name / (stage + '.json')).read_bytes())
        grade.update(json.loads(raw['response']['choices'][0]['message']['content']))
    return deepcopy(case), grade


class BlindReviewTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(socket.socket, 'connect', side_effect=AssertionError('Offline only')))

    def test_all_development_requests_preserve_evidence_rubric_and_caps(self):
        cases = existing.cases('diagnostic') + existing.cases('calibration') + existing.cases('interpretation')
        self.assertEqual(len(cases), 44)
        for case in cases:
            old = existing.transport.initial_requests(case['inputs'])
            plan = design.request_plan(case['inputs'])
            self.assertEqual(len(plan), 4)
            for offset in (0, 2):
                for i, (purpose, body) in enumerate(old):
                    self.assertEqual(plan[offset+i]['body'], body)
                    self.assertEqual(plan[offset+i]['purpose'], purpose)
                    self.assertEqual(body['max_completion_tokens'], 8192 if purpose == 'claims' else 4096)
            # Separate Python objects as well as separate intended requests.
            plan[0]['body']['messages'][1]['content'] = 'candidate contamination'
            self.assertNotIn('candidate contamination', plan[2]['body']['messages'][1]['content'])

    def test_candidate_and_expected_labels_cannot_enter_request_plan(self):
        case, _ = fixture('paraphrase-preserves-conditions')
        for key in ('candidate', 'candidate_judgments', 'review', 'expected', 'rationale'):
            bad = deepcopy(case['inputs']); bad[key] = {'label': 'pass'}
            with self.assertRaises(ValueError): design.request_plan(bad)

    def test_same_correct_or_wrong_labels_never_award_credit(self):
        for name in ('paraphrase-preserves-conditions', 'answer-injection-award-pass'):
            case, grade = fixture(name)
            out = design.compare(case, grade, deepcopy(grade))
            self.assertEqual(out['status'], 'agreement_only')
            self.assertFalse(out['target_credit'])
            self.assertFalse(out['release_eligible'])
            self.assertTrue(out['source_review_required'])

    def test_omitted_extra_claim_detected_even_when_remaining_claim_supported(self):
        case, grade = fixture('unsupported-extra-benefit')
        other = deepcopy(grade); other['claims'].pop()
        out = design.compare(case, grade, other)
        self.assertEqual(out['status'], 'unresolved_disagreement')
        self.assertIn('claims', out['differences'])

    def test_same_aggregate_failure_does_not_hide_fact_status_difference(self):
        case, grade = fixture('contradicted-quantity')
        other = deepcopy(grade); other['facts'][0].update(status='missing', answer_spans=[])
        out = design.compare(case, grade, other)
        self.assertEqual(out['status'], 'unresolved_disagreement')
        self.assertIn('facts', out['differences'])

    def test_nonexact_or_unauthorized_witness_invalidates_either_judge(self):
        case, grade = fixture('paraphrase-preserves-conditions')
        for field, value in [('span', 'fabricated quote'), ('id', 'R999')]:
            other = deepcopy(grade); other['claims'][0]['source_spans'][0][field] = value
            for a, b in ((grade, other), (other, grade)):
                self.assertEqual(design.compare(case, a, b)['status'], 'invalid')

    def test_incomplete_or_missing_judgments_cannot_be_compared_as_agreement(self):
        case, grade = fixture('paraphrase-preserves-conditions')
        other = deepcopy(grade); other['facts'].pop()
        for bad in (None, {}, other):
            self.assertEqual(design.compare(case, grade, bad)['status'], 'invalid')

    def test_safety_and_citation_failures_remain_blocking(self):
        for name in ('paraphrase-preserves-conditions', 'altered-quotation-same-meaning'):
            case, grade = fixture(name)
            if name == 'paraphrase-preserves-conditions': case['safety_flags'] = ['unauthorized_retrieval']
            self.assertEqual(design.compare(case, grade, grade)['status'], 'blocked')
        case, grade = fixture('paraphrase-preserves-conditions')
        case['payload']['citations'][0]['document_id'] = -1
        out = design.compare(case, grade, grade)
        self.assertIn(out['status'], ('invalid', 'blocked'))
        self.assertFalse(out['target_credit'])

    def test_behavior_and_relevance_disagreement_remain_visible(self):
        case, grade = fixture('pure-not-found')
        other = deepcopy(grade); other['actual_behavior'] = 'refuse_no_access'
        other['relevance']['status'] = 'fail'
        out = design.compare(case, grade, other)
        self.assertEqual(set(out['differences']), {'actual_behavior', 'relevance'})

    def test_pilot_complete_output_reservation_fits_proposed_one_dollar(self):
        from decimal import Decimal
        value = json.loads((ROOT / 'data/evaluation/conversation-continuation/blind-review-design/pilot-controls.json').read_bytes())
        self.assertEqual(len(value['cases']), 2)
        bound = sum((design.conservative_bound(c['inputs']) for c in value['cases']), Decimal(0))
        self.assertEqual(bound, Decimal('0.9713200'))
        self.assertLessEqual(bound, Decimal('1.00'))


if __name__ == '__main__':
    unittest.main()
