"""No-provider regression tests for the prospective contract and reference remedy."""
from copy import deepcopy
from decimal import Decimal
import json
import socket
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import conversation_ordering_v2 as references
from scripts import conversation_completion_budget_v2 as budget
from scripts import quality_eval_contract_v35 as contract
from scripts import quality_eval_transport_v35 as transport
from scripts.bounded_redesign_run import read, digest


class OrderingV2Tests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(socket.socket, 'connect', side_effect=AssertionError('Offline only')))

    def fixture(self):
        case = next(c for c in references.cases('calibration') if c['id'] == references.DISPUTED)
        grade = {}
        for stage in ('claims', 'coverage'):
            raw = read(references.legacy.FOLDER / 'grader-v34-calibration/run/raw' / case['id'] / (stage + '.json'))
            grade.update(json.loads(raw['response']['choices'][0]['message']['content']))
        grade['claims'][0].update(factual_status='unknown', citation_status='unknown',
                                 source_spans=[], citation_spans=[], reason='Synthetic ambiguous interpretation; no model judgment.')
        review = dict(reason='Synthetic reducer agreement, not independent review.',
                      **{k: 'agree' for k in (*contract.DIMENSIONS, 'forbidden_assertion')})
        return deepcopy(case), grade, review

    def test_preserves_all_controls_and_original_evidence(self):
        suite = references.suite()
        self.assertEqual(len(suite['cases']), 32)
        self.assertEqual(len(references.cases('diagnostic')), 16)
        self.assertEqual(len(references.probes('diagnostic')), 3)
        self.assertEqual(len(suite['review_probes']), 3)
        for path, expected in suite['source_bindings'].items():
            self.assertEqual(digest(references.legacy.ROOT / path), expected)

    def test_undeclared_reference_and_input_changes_are_rejected(self):
        for mutation in ('drop', 'answer', 'expectation', 'probe'):
            value = deepcopy(references.suite())
            if mutation == 'drop':
                value['cases'].pop(0)
            elif mutation == 'answer':
                value['cases'][0]['inputs']['answer'] = 'Changed'
            elif mutation == 'expectation':
                value['cases'][0]['expected']['overall'] = 'unresolved'
            else:
                value['review_probes'].pop()
            with patch.object(references, 'read', return_value=value), self.assertRaises(ValueError):
                references.suite()

    def test_correct_uncertainty_matching_never_credits_the_answer(self):
        case, grade, review = self.fixture()
        result = references.judged(case, grade, review)
        self.assertTrue(result['matched'], result['mismatches'])
        self.assertEqual(result['dimensions']['overall'], 'fail')
        self.assertFalse(result['dimensions']['target_credit'])
        self.assertEqual(result['dimensions']['completeness'], 'fail')

    def test_certainty_or_missing_fee_relabel_cannot_pass_comparison(self):
        for field, value in [('citation_status', 'missing'), ('factual_status', 'supported')]:
            case, grade, review = self.fixture()
            grade['claims'][0][field] = value
            self.assertFalse(references.judged(case, grade, review)['matched'])
        case, grade, review = self.fixture()
        grade['facts'][1]['status'] = 'covered'
        self.assertFalse(references.judged(case, grade, review)['matched'])
        case, grade, review = self.fixture()
        grade['claims'][0]['source_spans'] = [dict(id='R1', span='report the missing card to reception')]
        self.assertFalse(references.judged(case, grade, review)['matched'])

    def test_complete_ambiguous_answer_still_has_no_credit(self):
        _, grade, review = self.fixture()
        case = next(c for c in references.cases('calibration') if c['id'] == 'ambiguous-complete-order')
        grade['claims'][0]['text'] = 'First, report the missing Ibis token to reception.'
        grade['claims'].append(dict(text='Pay a 3-credit fee.', factual_status='supported', citation_status='supported',
            source_spans=[dict(id='R1', span='pay a 3-credit fee')],
            citation_spans=[dict(id='C1', span='pay a 3-credit fee')], reason='Synthetic supported fee.'))
        for fact, span in zip(grade['facts'], [grade['claims'][0]['text'], 'Pay a 3-credit fee.']):
            fact.update(status='covered', answer_spans=[span])
        grade.update(actual_behavior='answer', behavior_span=case['inputs']['answer'])
        result = references.judged(case, grade, review)
        self.assertTrue(result['matched'], result['mismatches'])
        self.assertEqual(result['dimensions']['overall'], 'unresolved')
        self.assertFalse(result['dimensions']['target_credit'])

    def test_review_disagreement_error_quotes_and_safety_still_block(self):
        case, grade, review = self.fixture()
        review['factual_support'] = 'dispute'
        self.assertFalse(references.judged(case, grade, review)['matched'])
        review['factual_support'] = 'agree'
        self.assertFalse(references.judged(case, grade, review, error='MalformedResponse')['matched'])
        case['payload']['citations'][0]['citation_text'] = 'Invented quote'
        result = references.judged(case, grade, review)
        self.assertEqual(result['dimensions']['quotation_fidelity'], 'fail')
        self.assertFalse(result['matched'])
        case, grade, review = self.fixture()
        case['safety_flags'] = ['permission_leak']
        self.assertFalse(references.judged(case, grade, review)['dimensions']['target_credit'])

    def test_requests_use_new_contract_without_changing_caps_or_schema(self):
        case, grade, _ = self.fixture()
        originals = dict(transport.previous.initial_requests(case['inputs']))
        for purpose, body in transport.initial_requests(case['inputs']):
            self.assertEqual(body['response_format'], originals[purpose]['response_format'])
            self.assertEqual(body['max_completion_tokens'], {'claims': 8192, 'coverage': 4096}[purpose])
            self.assertEqual(body['messages'][1], originals[purpose]['messages'][1])
            transport.reserve(body)
        claims = transport.initial_requests(case['inputs'])[0][1]
        self.assertEqual(claims['messages'][0]['content'], contract.CLAIM_PROMPT)
        review = transport.review_request(case['inputs'], grade)
        self.assertEqual(review['messages'][0]['content'], contract.REVIEW_PROMPT)
        self.assertEqual(review['max_completion_tokens'], 4096)
        self.assertEqual(review['reasoning_effort'], 'medium')
        self.assertGreater(transport.case_bound(case['inputs']), transport.reserve(review)['reserved_usd'])
        bad = deepcopy(claims)
        bad['max_completion_tokens'] = 1024
        with self.assertRaises(transport.BudgetStop):
            transport.reserve(bad)

    def test_three_stage_transport_preserves_provider_failure_without_retry(self):
        from pathlib import Path
        case, grade, review = self.fixture()
        calls = []

        class FakeLedger:
            def call(self, create, body, path):
                calls.append(path.name)
                schema = body['response_format']['json_schema']['schema']
                result = review if path.name == 'review.json' else {k: grade[k] for k in schema['properties']}
                return SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop',
                    message=SimpleNamespace(content=json.dumps(result), refusal=None))])

        actual = transport.grade_case(None, case['inputs'], FakeLedger(), Path('synthetic'))
        self.assertEqual(actual, (grade, review))
        self.assertEqual(calls, ['claims.json', 'coverage.json', 'review.json'])
        with patch.object(FakeLedger, 'call', side_effect=RuntimeError('Unknown outcome')) as submit:
            with self.assertRaises(RuntimeError):
                transport.grade_case(None, case['inputs'], FakeLedger(), Path('synthetic'))
            self.assertEqual(submit.call_count, 1)

    def test_whole_path_is_unfunded_and_does_not_release_original_hold(self):
        result = budget.assessment()
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['accounted_usd'], '9.31867776')
        self.assertEqual(result['remaining_usd'], '5.56669000')
        self.assertEqual(result['retained_hold_usd'], '0.14820250')
        self.assertEqual([s['calls'] for s in result['stages']], [51, 99, 48])
        self.assertGreater(Decimal(result['qualification_estimate_usd']), Decimal(result['qualification_headroom_usd']))
        self.assertFalse(result['paid_execution_authorized_by_report'])
        self.assertEqual(result['final']['required_successes'], 48)
        self.assertEqual(result['final']['cases'], 60)


if __name__ == '__main__':
    unittest.main()
