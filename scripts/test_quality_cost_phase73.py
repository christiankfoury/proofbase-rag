"""The single authorized unknown may carry forward, never a new unknown."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from scripts import quality_cost_phase73 as costs
from scripts.quality_completion_durable import write_json_atomic as write


class CarryForward(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.journal = costs.SpendJournal(self.folder / 'spend')

    def test_retains_full_prefix_and_marks_provider_unknown(self):
        original = costs.read(costs.OLD_SNAPSHOT)
        successor = self.journal.load()
        self.assertEqual(len(original['entries']), len(successor['entries']))
        self.assertEqual(sum(Decimal(r['accounted_usd']) for r in successor['entries'].values()), Decimal('6.69192009'))
        identity = costs.read(costs.OLD_AUDIT)['unknown_shared_identity']
        self.assertEqual(original['entries'][identity]['status'], 'unknown')
        self.assertEqual(successor['entries'][identity]['provider_outcome'], 'unknown')
        self.assertEqual(successor['entries'][identity]['accounted_usd'], '0.146775')
        with self.assertRaisesRegex(ValueError, 'cannot be settled'):
            self.journal.finish(identity, Decimal('0'), 'fake-receipt')

    def test_new_unknown_stops_spending(self):
        self.journal.reserve('new', Decimal('.02'), 'request-hash')
        self.journal.finish('new', Decimal(0), 'timeout-hash', uncertain=True)
        with self.assertRaisesRegex(ValueError, 'unknown provider'):
            self.journal.reserve('another', Decimal('.02'), 'another-hash')
        self.assertEqual(self.journal.load()['entries']['new']['accounted_usd'], '0.02')

    def test_cannot_release_old_reservation_or_increase_ceiling(self):
        data = self.journal.load()
        identity = costs.read(costs.OLD_AUDIT)['unknown_shared_identity']
        data['entries'][identity]['accounted_usd'] = '0'
        write(self.journal.path, data)
        with self.assertRaisesRegex(ValueError, 'carry-forward'):
            self.journal.load()
        policy = deepcopy(costs.read(costs.POLICY))
        policy['additional_ceiling_usd'] = '11.00'
        path = self.folder / 'changed-policy.json'; write(path, policy)
        with self.assertRaisesRegex(ValueError, 'ceiling'):
            costs.live_policy(path)

    def test_remaining_cap_enforced_before_reservation(self):
        before = self.journal.load()
        with self.assertRaisesRegex(ValueError, 'ceiling'):
            self.journal.reserve('too-much', Decimal('3.30807992'), 'hash')
        self.assertEqual(self.journal.load(), before)


if __name__ == '__main__':
    unittest.main()
