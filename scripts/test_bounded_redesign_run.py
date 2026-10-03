"""Offline tests for new authorization accounting and at-most-once execution."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.bounded_redesign_run import Ledger, read, FOLDER
from openai.types.chat import ChatCompletion


class RunTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.plan=read(FOLDER/'preflight-complete.json')
        self.policy=dict(total_ceiling_usd='12.50',stage_caps_usd=dict(application='2.00'))
        self.ledger=Ledger(self.temp.name,self.policy,self.plan)
        self.ledger.begin('candidate-mini','dev-01',0)
        self.body=next(b['request'] for b in self.plan['prepared_payloads']
                      if b['profile']=='candidate-mini' and b['stage']=='conversational_producer')

    def reply(self, **body):
        return ChatCompletion(id='offline',object='chat.completion',created=0,model=body['model'],
            choices=[dict(index=0,finish_reason='stop',message=dict(role='assistant',content='{}'))],
            usage=dict(prompt_tokens=100,completion_tokens=50,total_tokens=150,prompt_tokens_details=dict(cached_tokens=80)))

    def test_cached_usage_settles_durable_reservation(self):
        def provider(**body):
            stored=read(Path(self.temp.name)/'api-ledger.json')['calls'][0]
            self.assertEqual(stored['status'],'reserved')
            self.assertGreater(Decimal(stored['accounted_usd']),Decimal(0))
            self.assertIsNone(read(Path(self.temp.name)/stored['raw_path'])['response'])
            return self.reply(**body)
        self.ledger.call(provider,self.body)
        self.assertEqual(self.ledger.accounted,Decimal('.000096'))
        self.assertEqual(self.ledger.data['calls'][0]['status'],'completed')
        with self.assertRaises(ValueError):self.ledger.call(provider,self.body)
        self.assertEqual(len(self.ledger.data['calls']),1)

    def test_unknown_keeps_reservation_and_stops_without_retry(self):
        provider=Mock(side_effect=TimeoutError())
        with self.assertRaises(TimeoutError):self.ledger.call(provider,self.body)
        row=self.ledger.data['calls'][0]
        self.assertEqual(row['reserved_usd'],row['accounted_usd'])
        self.assertTrue(self.ledger.data['unknown_outcome'])
        with self.assertRaises(ValueError):self.ledger.call(provider,self.body)
        with self.assertRaises(ValueError):self.ledger.begin('candidate-mini','dev-02',0)
        provider.assert_called_once()

    def test_budget_blocks_before_provider(self):
        self.policy['stage_caps_usd']['application']='.000001'; provider=Mock()
        with self.assertRaises(ValueError):self.ledger.call(provider,self.body)
        provider.assert_not_called(); self.assertEqual(self.ledger.accounted,0)

    def test_bounds_and_model_are_enforced_before_provider(self):
        body=copy.deepcopy(self.body);body['model']='gpt-5.4-2026-03-05';provider=Mock()
        with self.assertRaises(ValueError):self.ledger.call(provider,body)
        provider.assert_not_called()
        other=Ledger(Path(self.temp.name)/'other',self.policy,self.plan)
        other.begin('candidate-mini','dev-01',0)
        body=copy.deepcopy(self.body);body['messages'][1]['content']='too long '*17000
        with self.assertRaises(ValueError):other.call(provider,body)
        provider.assert_not_called()

    def test_bad_receipt_preserved_and_full_reservation_retained(self):
        def provider(**body):
            response=self.reply(**body);response.model='unexpected-model';return response
        with self.assertRaises(Exception):self.ledger.call(provider,self.body)
        row=self.ledger.data['calls'][0]
        self.assertEqual(row['status'],'unknown')
        self.assertEqual(row['reserved_usd'],row['accounted_usd'])
        raw=read(Path(self.temp.name)/row['raw_path'])
        self.assertEqual(raw['status'],'received')
        self.assertEqual(raw['response']['model'],'unexpected-model')

    def test_turn_guard(self):
        with self.assertRaises(ValueError):self.ledger.begin('candidate-mini','dev-01',0)

    def test_callbacks_stop_before_next_http_turn(self):
        import os
        from scripts.bounded_redesign_preflight import configure
        from scripts.bounded_redesign_support import invoke
        from apps.api.app.reasoning.request_assessment import _base_continue_decision
        from openai.resources.chat.completions import Completions
        suite=read(FOLDER/'development.json');case=copy.deepcopy(suite['cases'][9])
        case['turns']*=2;events=[]
        def create(resource,**body):
            response=self.reply(**body)
            response.choices[0].message.content=json.dumps(_base_continue_decision().model_dump())
            return response
        def before(index):
            events.append(('before',index))
            if index==1:raise ValueError('Stop before next HTTP request')
        def after(turn,evidence):
            self.assertEqual(evidence,[])
            self.assertEqual(turn['status_code'],200)
            events.append(('after',turn['turn']))
        with patch.dict(os.environ,OPENAI_API_KEY='offline-test'),patch.object(Completions,'create',create),\
             patch('httpx.HTTPTransport.handle_request',side_effect=AssertionError('Offline only')):
            configure('v4')
            with self.assertRaises(ValueError):invoke(suite,case,before_turn=before,after_turn=after)
        self.assertEqual(events,[('before',0),('after',0),('before',1)])


if __name__=='__main__':unittest.main()
