"""The second protocol shares the original cap and keeps rejected-job accounting."""
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from scripts import quality_cost_continuation as cost
from scripts.quality_completion_durable import write_json_atomic as write


class Continuation(unittest.TestCase):
    def test_audited_rejection_retains_full_reservation(self):
        policy, limit = cost.live_policy()
        self.assertEqual(limit, Decimal(10))
        entries = cost.retained_entries()
        self.assertEqual(sum(Decimal(r['accounted_usd']) for r in entries.values()), Decimal('1.40344250'))
        self.assertEqual(len(entries), 1)
        self.assertEqual(next(iter(entries.values()))['accounting_basis'], 'resolved_rejection_full_reservation_retained')

    def test_retained_amount_blocks_overspend_before_request(self):
        with tempfile.TemporaryDirectory() as temp:
            journal = cost.SpendJournal(Path(temp))
            with self.assertRaisesRegex(ValueError, 'ceiling'):
                journal.reserve('new', Decimal(9), 'plan')
            self.assertFalse(journal.path.exists())
            journal.reserve('new', Decimal(1), 'plan')
            self.assertEqual(len(journal.load()['entries']), 2)
            journal.finish('new', Decimal('.2'), 'result')
            self.assertEqual(sum(Decimal(r['accounted_usd']) for r in journal.load()['entries'].values()), Decimal('1.60344250'))

    def test_retained_row_cannot_be_deleted_or_settled_to_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            journal = cost.SpendJournal(Path(temp)); data = journal.load()
            identity = next(iter(data['entries']))
            with self.assertRaisesRegex(ValueError, 'immutable'):
                journal.finish(identity, Decimal(0), 'changed')
            data['entries'] = {}; write(journal.path, data)
            with self.assertRaisesRegex(ValueError, 'removed or changed'):
                journal.load()


if __name__ == '__main__':
    unittest.main()
