"""Approved replacement budget and interpretation-first transport regressions."""
import unittest
from copy import deepcopy
from decimal import Decimal
from unittest.mock import patch
from scripts import conversation_cad1311_budget as budget
from scripts import test_conversation_recovery_budget as old_tests
from scripts.bounded_redesign_run import read, write, digest
from scripts import conversation_grader_v9 as grader
from scripts import quality_eval_transport_v31 as old_transport


class BudgetTests(old_tests.RecoveryBudgetTests):
    def setUp(self):
        self.enterContext(patch.object(old_tests, 'b', budget))
        super().setUp()
        old = read(budget.AUTHORIZATION)
        recovery = budget.FOLDER / 'recovery.json'
        write(recovery, old)
        self.enterContext(patch.object(budget, 'RECOVERY_AUTHORIZATION', recovery))
        write(budget.AUTHORIZATION, dict(user_answer='Yes I approve',
            total_ceiling_usd='14.88536776', remaining_budget_including_hold_usd='8.00',
            previous_remainder_added=False, recovery_authorization_sha256=digest(recovery)))

    def test_old_allowance_cannot_be_added(self):
        value = read(budget.AUTHORIZATION)
        value['previous_remainder_added'] = True
        write(budget.AUTHORIZATION, value)
        with self.assertRaises(ValueError):
            budget.prefix()


class TransportTests(unittest.TestCase):
    def test_same_schema_meaning_and_evidence_with_interpretation_first(self):
        for case in grader.cases('diagnostic') + grader.cases('calibration') + grader.cases('interpretation'):
            old = old_transport.initial_requests(case['inputs'])
            new = grader.transport.initial_requests(case['inputs'])
            for (purpose, a), (_, b) in zip(old, new):
                a, b = deepcopy(a), deepcopy(b)
                a['messages'][0] = b['messages'][0]
                if purpose == 'claims':
                    item = b['response_format']['json_schema']['schema']['properties']['claims']['items']
                    self.assertLess(list(item['properties']).index('reason'), list(item['properties']).index('factual_status'))
                    item['required'] = a['response_format']['json_schema']['schema']['properties']['claims']['items']['required']
                self.assertEqual(a, b)
                grader.transport.reserve(b)
        probe = grader.probes('diagnostic')[0]
        a = old_transport.review_request(probe['inputs'], probe['candidate'])
        b = grader.transport.review_request(probe['inputs'], probe['candidate'])
        schema = b['response_format']['json_schema']['schema']
        self.assertEqual(list(schema['properties'])[0], 'reason')
        schema['required'] = a['response_format']['json_schema']['schema']['required']
        a['messages'][0] = b['messages'][0]
        self.assertEqual(a, b)
        self.assertEqual(grader.CEILING, Decimal('14.88536776'))


if __name__ == '__main__':
    unittest.main()
