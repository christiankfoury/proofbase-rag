from copy import deepcopy
import json
import socket
import unittest
from unittest.mock import patch
from scripts import offline_judgment_comparator_v1 as c


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(socket.socket,'connect',side_effect=AssertionError('Offline only')))
        self.rows=c.read(c.OUT/'er1/v1/matrix.json')['controls']

    def test_frozen_matrix(self):
        for row in self.rows:
            with self.subTest(row=row['id']):
                result=c.compare(row['case'],row['first'],row['second'])
                self.assertEqual(result['outcome'],c.outcome(row['expected']))
                self.assertFalse(result['release_eligible'])
                self.assertFalse(result['target_credit'])

    def test_symmetry_and_input_preservation(self):
        for row in self.rows:
            before=deepcopy(row)
            a=c.compare(row['case'],row['first'],row['second'])
            b=c.compare(row['case'],row['second'],row['first'])
            self.assertEqual(a['status'],b['status'],row['id'])
            self.assertEqual(row,before)

    def test_missing_malformed_and_ambiguous_bindings(self):
        row=deepcopy(self.rows[0])
        for bad in (None,{},[],{'claims':[]}):
            self.assertEqual(c.compare(row['case'],row['first'],bad)['status'],'invalid')
        row['case']['inputs']['factual_sources']*=2
        self.assertEqual(c.compare(row['case'],row['first'],row['second'])['status'],'invalid')

    def test_complete_replay_and_hash_custody(self):
        report=c.report()
        self.assertEqual(len(report['replay']),44)
        self.assertEqual(report['missing_slots'],29)
        self.assertEqual(report['false_matches'],0)
        self.assertEqual(report['missed_matches'],0)
        probes=[r for r in report['replay'] if r['path'].endswith('-probe.json')]
        self.assertEqual(len(probes),3)
        self.assertTrue(all(r['packet_fields']==['grade','second'] for r in probes))
        self.assertTrue(all(r['comparison']['status']!='invalid' for r in probes))

    def test_safety_is_retained_not_credited(self):
        row=deepcopy(self.rows[0]); row['case']['safety_flags']=['unauthorized_document']
        result=c.compare(row['case'],row['first'],row['second'])
        self.assertEqual(result['recorded_safety_flags'],['unauthorized_document'])
        self.assertFalse(result['target_credit'])

    def test_no_company_or_case_specific_normalization(self):
        for original in self.rows:
            row=json.loads(json.dumps(original).replace('Lark','Kestrel').replace('38','47'))
            row['case']['id']='unseen-case'
            self.assertEqual(c.compare(row['case'],row['first'],row['second'])['outcome'],c.outcome(row['expected']))


if __name__=='__main__': unittest.main()
