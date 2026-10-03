"""Offline receipt safety and unchanged grader contract regressions."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from openai.types.chat import ChatCompletion
from scripts import conversation_grader as r


class GraderTests(unittest.TestCase):
    def test_all_saved_calibration_and_probes_keep_their_meaning(self):
        saved=r.ROOT/'data/evaluation/quality-completion-v1/v18-calibration'
        self.assertEqual(len(r.cases('calibration')),24)
        self.assertEqual(len(r.probes('calibration')),3)
        for case in r.cases('calibration'):
            grade={}
            for purpose,body in r.transport.initial_requests(case['inputs']):
                self.assertEqual(body['max_completion_tokens'],8192 if purpose=='claims' else 4096)
                raw=r.read(saved/case['id']/(purpose+'.json'))
                grade.update(r.transport.parsed(ChatCompletion.model_validate(raw['response']),body['response_format']['json_schema']['schema']))
            review=r.transport.parsed(ChatCompletion.model_validate(r.read(saved/case['id']/'review.json')['response']),r.contract.review_schema())
            self.assertTrue(r.existing.judged(case,grade,review,None)['matched'],case['id'])
        for case in r.probes('calibration'):
            review=r.transport.parsed(ChatCompletion.model_validate(r.read(saved/(case['id']+'-raw.json'))['response']),r.contract.review_schema())
            self.assertTrue(r.existing.probe_result(case,review,None)['matched'])
        self.assertIs(r.contract.validate,r.contract.previous.validate)
        self.assertIs(r.contract.dimensions,r.contract.previous.dimensions)

    def setup_ledger(self,spent='0.3875408'):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        folder=Path(tmp.name);self.enterContext(patch.object(r,'ROOT',folder));self.enterContext(patch.object(r,'FOLDER',folder))
        ledger=r.RollingLedger(folder/'stage/run',dict(prefix=dict(spent_usd=spent,ledger_sha256={}),maximum_calls=3))
        self.enterContext(patch.object(r,'prefix',side_effect=lambda:dict(spent_usd=str(ledger.accounted),ledger_sha256={'stage/run/api-ledger.json':r.digest(ledger.folder/'api-ledger.json')})))
        body=r.transport.initial_requests(r.cases('diagnostic')[0]['inputs'])[0][1]
        return ledger,body

    def test_reserve_before_network_settle_cache_and_forbid_repeat(self):
        ledger,body=self.setup_ledger()
        def create(**kwargs):
            row=r.read(ledger.folder/'api-ledger.json')['calls'][0]
            self.assertEqual(row['status'],'reserved')
            self.assertEqual(row['accounted_usd'],str(r.transport.reserve(body)['reserved_usd']))
            return ChatCompletion.model_validate(dict(id='offline',object='chat.completion',created=0,model=r.transport.MODEL,choices=[],usage=dict(prompt_tokens=1000,completion_tokens=100,total_tokens=1100,prompt_tokens_details=dict(cached_tokens=500))))
        ledger.call(create,body,ledger.folder/'raw/one.json')
        self.assertEqual(ledger.accounted,Decimal('0.3875408')+Decimal('.002875'))
        with self.assertRaises(r.transport.BudgetStop):ledger.call(Mock(),body,ledger.folder/'raw/one.json')

    def test_ceiling_blocks_submission_and_unknown_keeps_full_reservation(self):
        ledger,body=self.setup_ledger('12.4999');provider=Mock()
        with self.assertRaises(r.transport.BudgetStop):ledger.call(provider,body,ledger.folder/'raw/one.json')
        provider.assert_not_called()
        ledger,body=self.setup_ledger('1')
        with self.assertRaises(TimeoutError):ledger.call(Mock(side_effect=TimeoutError),body,ledger.folder/'raw/one.json')
        self.assertTrue(ledger.data['unknown_outcome'])
        self.assertEqual(ledger.accounted,Decimal(1)+r.transport.reserve(body)['reserved_usd'])
        with self.assertRaises(r.transport.BudgetStop):ledger.call(provider,body,ledger.folder/'raw/two.json')
        provider.assert_not_called()

    def test_unapproved_cap_and_model_fail_closed(self):
        body=r.transport.initial_requests(r.cases('diagnostic')[0]['inputs'])[0][1]
        for key,value in [('max_completion_tokens',4096),('model','gpt-5.4'),('reasoning_effort','low')]:
            altered=deepcopy(body);altered[key]=value
            with self.assertRaises(r.transport.BudgetStop):r.transport.reserve(altered)


if __name__=='__main__':unittest.main()
