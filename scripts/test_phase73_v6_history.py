"""No-network controls for preserving the old timeout and successor accounting."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import phase73_v6_history as history
from scripts import report_phase73_v6 as report
from scripts.quality_completion_durable import write_json_atomic as write


class History(unittest.TestCase):
    def test_original_prefix_retains_unknown_and_entire_charge(self):
        calls, total, resolved, _, entries = history.retained_prefix()
        original = history.read(history.ORIGINAL/'run/api-ledger.json')
        self.assertEqual(calls, original['calls'])
        self.assertEqual(len(calls), 3474)
        self.assertEqual(total, Decimal('20.73393762'))
        self.assertIn(3038, resolved)
        self.assertEqual(calls[3038]['status'], 'unknown')
        self.assertEqual(calls[3038]['charged_usd'], '0.146775')
        self.assertEqual(entries[calls[3038]['additional_spend_identity']]['provider_outcome'], 'unknown')

    def test_changed_preserved_capture_is_rejected(self):
        from scripts import report_phase73_v5_capture
        with patch.object(report_phase73_v5_capture, 'snapshot', return_value={'changed': True}):
            with self.assertRaisesRegex(ValueError, 'capture inventory'):
                history.retained_prefix()

    def test_readonly_report_accepts_local_budget_stop_but_not_new_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            write(folder/'prior-ledger.json', {'fixture':True})
            prior = SimpleNamespace(data={'calls':[]},spent=Decimal('1'),resolved_rejections=set())
            data = {'prior_sha256':report.digest(folder/'prior-ledger.json'), 'prior_calls':0,
                    'prior_spend_usd':'1','calls':[],
                    'authorization_sha256':report.digest(report.QUALITY/'autonomous-authorization.json'),
                    'bounds':report.bounds(),'unknown_outcome':False,'budget_exhausted':True}
            write(folder/'api-ledger.json', data); write(folder/'run/api-ledger.json', data)
            with patch.object(report,'FOLDER',folder), patch.object(report,'PriorLedger',return_value=prior):
                snapshot = report.SettledSnapshot(folder/'run/api-ledger.json')
                self.assertEqual(snapshot.spent, Decimal('1'))
                self.assertFalse(hasattr(snapshot,'call'))
                data['unknown_outcome'] = True
                write(folder/'api-ledger.json',data); write(folder/'run/api-ledger.json',data)
                with self.assertRaisesRegex(ValueError,'outcome differs'):
                    report.SettledSnapshot(folder/'run/api-ledger.json')


if __name__ == '__main__':
    unittest.main()
