"""Cumulative budget includes the prior CAD-authorized comparison."""
import tempfile
from pathlib import Path
import sys
from decimal import Decimal
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.conversation_continuation import Ledger, prefix, read, PREVIOUS


class BudgetTests(unittest.TestCase):
    def test_prior_receipts_reconcile_without_historical_topup(self):
        value=prefix()
        self.assertGreaterEqual(Decimal(value['spent_usd']),Decimal('.1529816'))
        self.assertIn('data/evaluation/bounded-redesign/cad20-comparison/api-ledger.json',value['ledger_sha256'])

    def test_prefix_spend_blocks_call_before_submission(self):
        old=read(PREVIOUS/'preflight-complete.json')
        plan=dict(prefix=dict(spent_usd='12.49999',ledger_sha256={}),profile='candidate-mini',
            turns=[dict(case_id='dev-03',turn=0)],bounds=old['bounds'])
        body=next(r['request'] for r in old['prepared_payloads'] if r['profile']=='candidate-mini' and r['stage']=='conversational_producer')
        with tempfile.TemporaryDirectory() as folder:
            ledger=Ledger(folder,plan);ledger.begin('candidate-mini','dev-03',0);provider=Mock()
            with self.assertRaises(ValueError):ledger.call(provider,body)
            provider.assert_not_called();self.assertEqual(ledger.accounted,Decimal('12.49999'))

    def test_undeclared_turn_does_not_expand_focused_budget(self):
        plan=dict(prefix=dict(spent_usd='.1529816',ledger_sha256={}),profile='candidate-mini',
            turns=[dict(case_id='dev-03',turn=0)],bounds={})
        with tempfile.TemporaryDirectory() as folder:
            ledger=Ledger(folder,plan)
            with self.assertRaises(ValueError):ledger.begin('candidate-mini','dev-03',1)


if __name__=='__main__':unittest.main()
