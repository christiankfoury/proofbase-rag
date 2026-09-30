"""No-network controls for preserving the old timeout and successor accounting."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import phase73_v5_history as history
from scripts import report_phase73_v5 as report
from scripts.quality_completion_durable import write_json_atomic as write


class History(unittest.TestCase):
    def test_successor_calls_append_once_and_preserve_all_shared_entries(self):
        stages = history.standard_stages()[:3]
        scratch = history.ROOT/'data/evaluation/local-runs'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch, prefix='v5-accounting-test-') as temp:
            folder = Path(temp)
            review = folder/'review.md'; review.write_text('Synthetic qualification fixture')
            result = folder/'report.json'
            write(result, {'status':'complete','count':16,'matched':16,'calls':48,
                           'additional_accounted_usd':'7.67683059'})
            gate = folder/'gate.json'
            write(gate, {'status':'approved','human_adjudication':False,
                         'unresolved_semantic_findings':0,'report_sha256':history.digest(result),
                         'source_review_sha256':history.digest(review)})
            # Only qualification metadata is synthetic. Replay all 108 real new
            # development receipts without treating them as live confirmation.
            with patch.object(history,'standard_stages',return_value=stages), \
                 patch.multiple(history.confirmation, REPORT=result, GATE=gate, REVIEW=review,
                                SEAL=gate):
                prefix = history.build_prefix(qualify=False)
                self.assertEqual(len(prefix['calls']),3147)
                self.assertEqual(prefix['additional_accounted_usd'],'7.67683059')
                self.assertEqual(prefix['prior_spend_usd'],'18.53253136')
                self.assertEqual(prefix['calls'][3038]['status'],'unknown')

    def test_original_prefix_retains_unknown_and_entire_charge(self):
        calls, total, resolved, _, entries = history.retained_prefix()
        original = history.read(history.ORIGINAL/'run/api-ledger.json')
        audit = history.read(history.spending.OLD_AUDIT)
        self.assertEqual(calls, original['calls'])
        self.assertEqual(len(calls), 3039)
        self.assertEqual(total, Decimal('17.54762086'))
        self.assertIn(3038, resolved)
        self.assertEqual(calls[3038]['status'], 'unknown')
        self.assertEqual(calls[3038]['charged_usd'], '0.146775')
        self.assertEqual(entries[audit['unknown_shared_identity']]['provider_outcome'], 'unknown')

    def test_an_extra_unknown_is_not_covered_by_authorization(self):
        original_read = history.read
        def changed(path):
            result = original_read(path)
            if Path(path) == history.ORIGINAL/'run/api-ledger.json':
                result = deepcopy(result)
                result['calls'][-2]['status'] = 'unknown'
            return result
        with patch.object(history, 'read', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'specifically authorized'):
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
