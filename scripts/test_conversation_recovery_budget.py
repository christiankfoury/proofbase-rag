"""Offline checks for the single approved retained-reservation exception."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import conversation_recovery_budget as b
from scripts.bounded_redesign_run import read, write, digest


class RecoveryBudgetTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        folder = root / 'continuation'
        original = root / 'original.json'
        authorization = folder / 'network-recovery-authorization.json'
        for key, value in [('ROOT', root), ('FOLDER', folder), ('ORIGINAL', original), ('AUTHORIZATION', authorization)]:
            self.enterContext(patch.object(b, key, value))
        write(original, dict(unknown_outcome=False, calls=[]))
        write(folder / 'authorization.json', dict(prior_ledger_sha256=digest(original)))
        raw = folder / 'failed/run/raw.json'
        write(raw, dict(response=None))
        self.ledger = folder / 'failed/run/api-ledger.json'
        write(self.ledger, dict(unknown_outcome=True, stopped=True, calls=[dict(status='unknown',
            raw_path='raw.json', raw_sha256=digest(raw), accounted_usd='0.1482025', reserved_usd='0.1482025')]))
        write(authorization, dict(user_answer='Yes I approve', total_ceiling_usd='12.50',
            maximum_recovery_attempts=1, retained_ledger_path=self.ledger.relative_to(root).as_posix(),
            retained_ledger_sha256=digest(self.ledger), retained_reservation_usd='0.14820250'))

    def test_hold_is_counted_and_evidence_unchanged(self):
        before = self.ledger.read_bytes()
        result = b.prefix()
        self.assertEqual(result['spent_usd'], '0.14820250')
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_second_unknown_is_not_exempt(self):
        write(b.FOLDER / 'recovery/run/api-ledger.json', read(self.ledger))
        with self.assertRaisesRegex(ValueError, 'Unsettled prior call'):
            b.prefix()

    def test_editing_old_reservation_is_rejected(self):
        ledger = read(self.ledger)
        ledger['calls'][0]['accounted_usd'] = '0'
        write(self.ledger, ledger)
        with self.assertRaises(ValueError):
            b.prefix()

    def test_missing_approval_is_rejected(self):
        approval = read(b.AUTHORIZATION)
        approval['user_answer'] = ''
        write(b.AUTHORIZATION, approval)
        with self.assertRaises(ValueError):
            b.prefix()


if __name__ == '__main__':
    unittest.main()
