"""No-network accounting and custody controls before Phase 73 freeze."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch,Mock
from scripts import phase73_eval_budget as budget
from scripts.quality_completion_ledger import FOLDER as QUALITY,digest,Ledger as QualityLedger
from scripts.quality_completion_durable import write_json_atomic


def response(model='gpt-4.1-mini-2025-04-14',embedding=False):
    usage={'prompt_tokens':10,'total_tokens':10 if embedding else 12}
    if not embedding:
        usage['completion_tokens']=2
    data={'model':model,'usage':usage,'data':[] if embedding else None}
    return SimpleNamespace(model=model,usage=SimpleNamespace(**usage),model_dump=lambda **kw:data)


class Accounting(unittest.TestCase):
    def setUp(self):
        self.additional_spend = Mock()
        self.spend_patch = patch.object(budget, 'SpendJournal', return_value=self.additional_spend)
        self.spend_patch.start()
        self.addCleanup(self.spend_patch.stop)
        self.temp=tempfile.TemporaryDirectory()
        self.folder=Path(self.temp.name)
        frozen_prior=QUALITY/'v15-calibration/api-ledger.json'
        self.prior=QualityLedger(frozen_prior)
        (self.folder/'prior-ledger.json').write_bytes(frozen_prior.read_bytes())
        self.path=self.folder/'api-ledger.json'
        write_json_atomic(self.path,{'prior_sha256':digest(self.folder/'prior-ledger.json'),
            'prior_spend_usd':str(self.prior.spent),'prior_calls':len(self.prior.data['calls']),
            'authorization_sha256':digest(QUALITY/'autonomous-authorization.json'),'bounds':budget.bounds(),
            'calls':self.prior.data['calls'],'unknown_outcome':False,'budget_exhausted':False})
        self.ledger=budget.Ledger(self.path)
        self.ledger.begin_case('fresh-001')
        self.body={'model':'gpt-4.1-mini','messages':[{'role':'user','content':'Synthetic probe'}],'max_completion_tokens':100}

    def tearDown(self):
        self.temp.cleanup()

    def test_chat_and_embedding_settle_separately_and_snapshot_reloads(self):
        self.ledger.call(lambda **kw:response(),self.body,self.folder/'chat.json','chat')
        self.ledger.call(lambda **kw:response('text-embedding-3-small',True),
                         {'model':'text-embedding-3-small','input':['Synthetic probe']},self.folder/'embed.json','embedding')
        self.assertEqual(self.ledger.spent-self.prior.spent,budget.Decimal('0.00000740'))
        write_json_atomic(self.folder/'run/api-ledger.json',self.ledger.data)
        self.assertEqual(budget.Ledger(self.folder/'run/api-ledger.json').spent,self.ledger.spent)
        self.assertEqual(self.additional_spend.reserve.call_count,2)
        self.assertEqual(self.additional_spend.finish.call_count,2)

    def test_additional_budget_blocks_application_before_provider_call(self):
        self.additional_spend.reserve.side_effect=ValueError('Additional spending ceiling would be exceeded')
        provider=Mock()
        with self.assertRaisesRegex(ValueError,'ceiling'):
            self.ledger.call(provider,self.body,self.folder/'blocked.json','chat')
        provider.assert_not_called()
        self.assertFalse((self.folder/'blocked.json').exists())

    def test_cached_application_tokens_reduce_estimate_and_replay(self):
        data={'model':'gpt-4.1-mini-2025-04-14','usage':{'prompt_tokens':100,'completion_tokens':2,
              'prompt_tokens_details':{'cached_tokens':80}}}
        result=SimpleNamespace(model=data['model'],usage=SimpleNamespace(**data['usage']),model_dump=lambda **kw:data)
        self.ledger.call(lambda **kw:result,self.body,self.folder/'cached.json','chat')
        self.assertEqual(self.ledger.spent-self.prior.spent,budget.Decimal('.0000192'))
        from scripts import report_phase73_eval as report
        with patch.object(report,'FOLDER',self.folder):
            self.assertEqual(len(report.audit_calls(self.ledger)),1)

    def test_unknown_provider_outcome_is_reserved_and_blocks_next_call(self):
        provider=Mock(side_effect=TimeoutError())
        with self.assertRaises(TimeoutError):
            self.ledger.call(provider,self.body,self.folder/'unknown.json','chat')
        self.assertGreater(self.ledger.spent,self.prior.spent)
        with self.assertRaisesRegex(budget.BudgetStop,'Unsettled'):
            self.ledger.call(provider,self.body,self.folder/'retry.json','chat')
        self.assertEqual(provider.call_count,1)

    def test_pre_call_input_bound_issues_no_request(self):
        self.body['messages'][0]['content']='x'*budget.APP_INPUT_CAP
        provider=Mock()
        with self.assertRaisesRegex(budget.BudgetStop,'token bound'):
            self.ledger.call(provider,self.body,self.folder/'blocked.json','chat')
        provider.assert_not_called()
        self.assertEqual(self.ledger.spent,self.prior.spent)
        self.assertTrue(self.ledger.data['budget_exhausted'])

    def test_duplicate_attempt_and_tampered_prefix_rejected(self):
        provider=Mock(return_value=response())
        self.ledger.call(provider,self.body,self.folder/'once.json','chat')
        with self.assertRaisesRegex(budget.BudgetStop,'already attempted'):
            self.ledger.call(provider,self.body,self.folder/'once.json','chat')
        self.assertEqual(provider.call_count,1)
        data=json.loads(self.path.read_bytes());data['calls'][0]['charged_usd']=100
        write_json_atomic(self.path,data)
        with self.assertRaisesRegex(budget.BudgetStop,'Historical accounting'):
            budget.Ledger(self.path)

    def test_per_case_call_bound_covers_auxiliary_operations(self):
        provider=Mock(return_value=response())
        with patch.object(budget,'APP_CALLS_PER_CASE',1):
            data=json.loads(self.path.read_bytes());data['bounds']=budget.bounds();write_json_atomic(self.path,data)
            self.ledger.call(provider,self.body,self.folder/'first.json','chat')
            with self.assertRaisesRegex(budget.BudgetStop,'case/run allowance'):
                self.ledger.call(provider,{'model':'text-embedding-3-small','input':['x']},self.folder/'extra.json','embedding')
        self.assertEqual(provider.call_count,1)

    def test_sdk_interception_disables_retries_caps_output_and_counts_embedding(self):
        from openai import OpenAI
        from openai.resources.chat.completions import Completions
        from openai.resources.embeddings import Embeddings
        chat=Mock(return_value=response());embed=Mock(return_value=response('text-embedding-3-small',True))
        with patch.object(Completions,'create',chat),patch.object(Embeddings,'create',embed):
            with self.ledger.intercept():
                client=OpenAI(api_key='unused-test-credential',max_retries=2)
                self.assertEqual(client.max_retries,0)
                client.chat.completions.create(model='gpt-4.1-mini',messages=[{'role':'user','content':'x'}],max_tokens=10000)
                client.embeddings.create(model='text-embedding-3-small',input=['x'])
        self.assertEqual(chat.call_count,1);self.assertEqual(embed.call_count,1)
        self.assertEqual(chat.call_args.kwargs['max_tokens'],2048)
        self.assertEqual(len(self.ledger.data['calls'])-self.ledger.data['prior_calls'],2)

    def test_offline_audit_rejects_changed_raw_response(self):
        from scripts import report_phase73_eval as report
        self.ledger.call(lambda **kw:response(),self.body,self.folder/'chat.json','chat')
        with patch.object(report,'FOLDER',self.folder):
            self.assertEqual(len(report.audit_calls(self.ledger)),1)
            raw=json.loads((self.folder/'chat.json').read_bytes())
            raw['response']['usage']['prompt_tokens']=11
            write_json_atomic(self.folder/'chat.json',raw)
            with self.assertRaisesRegex(ValueError,'binding failed'):
                report.audit_calls(self.ledger)


class Custody(unittest.TestCase):
    def test_changed_runtime_or_failed_evaluator_blocks_before_suite_load(self):
        from scripts import phase73_eval_protocol as protocol
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            write_json_atomic(folder/'freeze.json',{'files':{},'bounds':budget.bounds()})
            with patch.object(protocol,'FOLDER',folder),patch.object(protocol,'file_inventory',return_value={'changed':'hash'}):
                with self.assertRaisesRegex(ValueError,'Frozen source'):
                    protocol.verify_custody()
            with patch.object(protocol,'FOLDER',folder),patch.object(protocol,'file_inventory',return_value={}), \
                 patch.object(protocol,'evaluator_ready',side_effect=ValueError('Evaluator not ready')):
                data=json.loads((folder/'freeze.json').read_bytes());data['evaluator_readiness_sha256']='pending'
                write_json_atomic(folder/'freeze.json',data)
                with self.assertRaisesRegex(ValueError,'Evaluator not ready'):
                    protocol.verify_custody()


class AdditionalReplay(unittest.TestCase):
    def test_shared_journal_binds_every_new_call_and_prior_batch(self):
        from scripts import report_phase73_eval as report
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp); confirmation=folder/'confirmation'
            policy_hash=digest(report.POLICY)
            prior={'status':'settled','reserved_usd':'1','accounted_usd':'.1',
                   'evidence_sha256':'plan','result_sha256':'result'}
            write_json_atomic(confirmation/'additional-spend.json',{'policy_sha256':policy_hash,'entries':{'batch':prior}})
            row={'additional_spend_identity':'sync-1','reserved_usd':'.5','charged_usd':'.2',
                 'request_sha256':'request','raw_sha256':'raw'}
            snapshot={'policy_sha256':policy_hash,'entries':{'batch':prior,'sync-1':{
                'status':'settled','reserved_usd':'.5','accounted_usd':'.2',
                'evidence_sha256':'request','result_sha256':'raw'}}}
            write_json_atomic(folder/'run/additional-spend.json',snapshot)
            with patch.object(report,'FOLDER',folder),patch.object(report,'CONFIRMATION',confirmation):
                self.assertEqual(report.audit_additional_spend([row]),budget.Decimal('.3'))
                with self.assertRaisesRegex(ValueError,'Duplicate'):
                    report.audit_additional_spend([row,row])
                snapshot['entries']['sync-1']['accounted_usd']='0'
                write_json_atomic(folder/'run/additional-spend.json',snapshot)
                with self.assertRaisesRegex(ValueError,'snapshot differs'):
                    report.audit_additional_spend([row])


if __name__=='__main__':
    unittest.main()
