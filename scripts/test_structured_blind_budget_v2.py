"""Replacement allowance rejects double counting, changed evidence and holds."""
from copy import deepcopy
from decimal import Decimal
import socket
import unittest
from unittest.mock import patch
from scripts import structured_blind_budget_v2 as budget


class ReplacementBudgetTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(socket.socket, 'connect', side_effect=AssertionError('Offline only')))
        self.original_read = budget.read
        self.previous = budget.read(budget.prior.REPORT)
        self.enterContext(patch.object(budget.prior, 'assessment', return_value=self.previous))

    def test_replacement_preserves_hold_and_whole_path_stop(self):
        result = budget.assessment()
        self.assertEqual(Decimal(result['ceiling_usd']), Decimal('17.24794526'))
        self.assertEqual(result['remaining_usd'], '6.34179750')
        self.assertEqual(result['retained_hold_usd'], '0.14820250')
        self.assertEqual(result['qualification_headroom_usd'], '1.84179750')
        self.assertEqual(result['status'], 'budget_blocked')
        self.assertFalse(result['paid_execution_authorized'])

    def test_cannot_add_old_remainder_raise_allowance_or_release_hold(self):
        for key, value in [('previous_remainder_added', True), ('remaining_balance_including_hold_usd', '12.35'),
                           ('total_ceiling_usd', '99'), ('retained_hold_usd', '0'), ('provider_retries', 1)]:
            authorization = deepcopy(self.original_read(budget.AUTHORIZATION))
            authorization[key] = value
            with patch.object(budget, 'read', side_effect=lambda p: authorization if p == budget.AUTHORIZATION else self.original_read(p)):
                with self.assertRaises(ValueError): budget.assessment()

    def test_new_spending_invalidates_the_saved_decision(self):
        changed = deepcopy(self.previous)
        changed['accounted_usd'] = '11.0'
        with patch.object(budget.prior, 'assessment', return_value=changed):
            with self.assertRaises(ValueError): budget.assessment()


if __name__ == '__main__':
    unittest.main()
