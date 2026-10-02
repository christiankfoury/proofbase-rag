"""Offline executor checks, never a model-accuracy measurement."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import json
import tempfile
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
import unittest
from scripts.test_application_reliability import OfflineCase
from scripts import conversational_scenario_diagnostic as run
from openai.types.chat import ChatCompletion


class Diagnostic(OfflineCase):
    def test_preflight_price_bounds_and_frozen_originals(self):
        plan=run.read(run.FOLDER/'preflight.json');suite=run.read(run.FOLDER/'cases.json')
        self.assertEqual(plan['maximum_calls'],8)
        self.assertEqual(plan['provider_retries'],0)
        total=Decimal(0)
        for case,body in zip(suite['cases'],plan['requests'],strict=True):
            canonical,bounds=run.prepare(body)
            self.assertEqual(canonical,body)
            self.assertEqual(json.loads(body['messages'][1]['content'])['current_request'],case['question'])
            total+=bounds[2]
        self.assertEqual(total,Decimal(plan['prepared_upper_bound_usd']))
        self.assertLessEqual(total,Decimal('.50'))
        for relative,sha in plan['bindings'].items():self.assertEqual(run.digest(ROOT/relative),sha)
        self.assertEqual(run.prepare(dict(plan['requests'][0],max_completion_tokens=3000))[0]['max_completion_tokens'],2048)
        for changed in [dict(plan['requests'][0],stream=True),
                        dict(plan['requests'][0],model='unpriced')]:
            with self.assertRaises(Exception):run.prepare(changed)

    def exercise(self, fail):
        original=run.FOLDER;plan=run.read(original/'preflight.json');suite=run.read(original/'cases.json')
        _,chunks,_,_=run.context();cid=next(c.chunk_id for c in chunks if '| Office supplies |' in c.content)
        entries={};calls=[]
        class Journal:
            def load(self):return {'entries':entries}
            def reserve(self,identity,amount,sha):
                if identity in entries or any(e['status']!='settled' for e in entries.values()):raise ValueError('No retry')
                entries[identity]=dict(status='reserved',reserved_usd=str(amount),accounted_usd=str(amount))
            def finish(self,identity,amount,sha,uncertain=False):
                entries[identity].update(status='unknown' if uncertain else 'settled',
                    accounted_usd=entries[identity]['reserved_usd'] if uncertain else str(amount))
        def create(**body):
            index=len(calls);calls.append(body)
            if fail:raise TimeoutError('unknown provider outcome')
            case=suite['cases'][index];positive=case['scope']=='row_comparison'
            proposal=dict(scope=case['scope'],complete_request=True,unhandled_parts=[],
                amount_quote=case.get('amount'),category_quote=case.get('category'),source_chunk_id=cid if positive else None)
            content=dict(answerability='sufficient',required_facts=[dict(fact_id='rule',description='Category limit',support='supported',supporting_chunk_ids=[cid])],
                supporting_chunk_ids=[cid],conflicts=[],missing_information=[],assessment_confidence=.9,scenario=proposal)
            return ChatCompletion.model_validate(dict(id='offline',object='chat.completion',created=0,model='gpt-4.1-mini-2025-04-14',
                choices=[dict(index=0,finish_reason='stop',message=dict(role='assistant',content=json.dumps(content)))],
                usage=dict(prompt_tokens=200,completion_tokens=100,total_tokens=300,prompt_tokens_details=dict(cached_tokens=0))))
        api=SimpleNamespace(base_url='https://api.openai.com/v1/',chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);run.write(folder/'cases.json',suite)
            run.write(folder/'preflight.json',dict(plan,bindings={},initial_journal={'entries':{}}))
            with patch.object(run,'FOLDER',folder),patch.object(run,'budget',return_value={'entries':{}}), \
                 patch.object(run,'SpendJournal',Journal),patch.object(run,'live_policy',return_value=({},run.INITIAL)), \
                 patch.object(run.subprocess,'check_output',side_effect=lambda args,**kwargs:'' if args[1]=='diff' else 'offline-commit'), \
                 patch('openai.OpenAI',return_value=api) as constructor:
                if fail:
                    with self.assertRaises(ValueError):run.run()
                else:run.run()
                self.assertEqual(constructor.call_args.kwargs['max_retries'],0)
            manifest=run.read(folder/'run/manifest.json')
            self.assertEqual(len(calls),1 if fail else 8)
            self.assertEqual(manifest['status'],'stopped' if fail else 'complete')
            if fail:
                self.assertEqual(next(iter(entries.values()))['status'],'unknown')
                self.assertEqual(next(iter(entries.values()))['accounted_usd'],next(iter(entries.values()))['reserved_usd'])
            else:
                self.assertTrue(all(e['status']=='settled' for e in entries.values()))
                rows=[run.read(folder/'run'/(c['id']+'.json')) for c in suite['cases']]
                self.assertTrue(all(r['correct_interpretation'] for r in rows))  # Known stubs only.
            with self.assertRaises(FileExistsError):
                (folder/'run').mkdir()

    def test_eight_synchronous_calls_and_receipt_accounting(self):self.exercise(False)
    def test_timeout_is_not_retried_and_reservation_is_retained(self):self.exercise(True)


if __name__=='__main__':unittest.main(verbosity=2)
