"""Negative controls for the local continuation decision, with no network use."""
from copy import deepcopy
from decimal import Decimal
import unittest

from scripts import audit_phase73_continuation as audit


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = audit.original.read(audit.original.FOLDER / 'run/additional-spend.json')

    def test_shared_journal_cannot_hide_new_or_changed_spending(self):
        changed = deepcopy(self.snapshot)
        changed['entries']['unreported-call'] = {'status': 'settled', 'accounted_usd': '0.01'}
        with self.assertRaisesRegex(ValueError, 'differs'):
            audit.audit_shared_journal(self.snapshot, changed)
        changed = deepcopy(self.snapshot)
        unknown = next(r for r in changed['entries'].values() if r['status'] == 'unknown')
        unknown.update(status='settled', accounted_usd='0')
        with self.assertRaisesRegex(ValueError, 'differs'):
            audit.audit_shared_journal(self.snapshot, changed)

    def test_reservation_is_not_a_provider_receipt(self):
        changed = deepcopy(self.snapshot)
        for row in changed['entries'].values():
            row['status'] = 'settled'
        with self.assertRaisesRegex(ValueError, 'unknown reservation'):
            audit.audit_shared_journal(changed, changed)

    def test_bad_source_or_execution_claim_rejected(self):
        controls = audit.original.read(audit.CONTROLS)
        self.assertEqual(audit.check_controls(controls), 6)
        controls['cases'][0]['source_quote'] += ' Invented source policy.'
        with self.assertRaisesRegex(ValueError, 'quote'):
            audit.check_controls(controls)
        controls = audit.original.read(audit.CONTROLS)
        controls['executed'] = True
        with self.assertRaisesRegex(ValueError, 'execution'):
            audit.check_controls(controls)

    def test_full_audit_does_not_allow_paid_execution(self):
        result = audit.audit()
        self.assertFalse(result['paid_execution_allowed'])
        self.assertFalse(result['original_suite_resume_allowed'])
        self.assertFalse(result['request_store_enabled'])
        self.assertFalse(result['completion_id_available'])
        self.assertEqual(Decimal(result['additional_remaining_usd']), Decimal('3.30807991'))
        self.assertEqual(result['unknown_reservation_usd'], '0.146775')
        self.assertEqual(result['original_cumulative_calls'], 3039)


if __name__ == '__main__':
    unittest.main()
