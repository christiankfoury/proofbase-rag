"""Offline custody replay and negative controls; no provider calls."""
from copy import deepcopy
import unittest
from unittest.mock import patch
from scripts.test_application_reliability import OfflineCase
from scripts import report_reliability_live_v2 as report


class Evidence(OfflineCase):
    def test_custody_and_accounting(self):
        result=report.replay()
        self.assertEqual(result['charged_usd'],'0.02128484')
        self.assertEqual(len(result['rows']),6)

    def test_changed_charge_is_rejected(self):
        original=report.read
        def read(path):
            value=original(path)
            if path.name=='api-ledger.json':
                value=deepcopy(value);value['calls'][0]['charged_usd']='0'
            return value
        with patch.object(report,'read',side_effect=read),self.assertRaises(AssertionError):report.replay()

    def test_changed_source_is_rejected(self):
        original=report.read
        def read(path):
            value=original(path)
            if path.name=='check-03.json':
                value=deepcopy(value);value['authorized_evidence']=[]
            return value
        with patch.object(report,'read',side_effect=read),self.assertRaises(AssertionError):report.replay()


if __name__=='__main__':unittest.main(verbosity=2)
