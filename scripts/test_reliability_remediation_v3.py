"""Saved-failure replay and independent offline application regressions."""
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import json
import tempfile
import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock,patch
from openai.types.chat import ChatCompletion
from scripts.test_application_reliability import OfflineCase
from scripts.test_phase54_post_generation_validation import chunk,candidate,semantic_payload
from apps.api.app import main
from apps.api.app.reasoning import post_generation_validation as pv,evidence_assessment as ea
from apps.api.app.generation import answer_generator as gen
from apps.api.app.core.config import get_settings

FOLDER=ROOT/'data/evaluation/application-reliability-live-v2'
OUT=ROOT/'data/evaluation/reliability-remediation-v3'

def read(path):return json.loads(Path(path).read_bytes())

class Client:
    def __init__(self,response):
        self.response=response;self.requests=[]
        self.chat=SimpleNamespace(completions=SimpleNamespace(create=self.create))
    def create(self,**kwargs):
        self.requests.append(kwargs)
        if isinstance(self.response,Exception):raise self.response
        return self.response

def fake(payload,usage=True):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload),refusal=None))],
        usage=SimpleNamespace(prompt_tokens=137,completion_tokens=61) if usage else None)

def captured(index):return ChatCompletion.model_validate(read(FOLDER/f'run/raw/call-{index:03}.json')['response'])

def saved_validation(index):
    raw=read(FOLDER/f'run/raw/call-{index:03}.json')
    inputs=json.loads(raw['request']['messages'][1]['content'])
    chunks=[replace(chunk(e['chunk_id'],e['content']),document_id=e['document_id'],
        section_heading=e['section_heading']) for e in inputs['authorized_evidence']]
    return inputs,chunks,Client(captured(index))

class Contracts(OfflineCase):
    def setUp(self):
        super().setUp()
        self.enterContext(patch.dict(os.environ,{'POST_GENERATION_VALIDATION_PROMPT_VERSION':REPLAY_VERSION,'EVIDENCE_ASSESSMENT_PROMPT_VERSION':REPLAY_VERSION}))
        get_settings.cache_clear();self.addCleanup(get_settings.cache_clear)

    def test_saved_failures_through_callers(self):
        observations={}
        for index,label in [(4,'numeric_provenance'),(14,'compound_scope')]:
            inputs,chunks,client=saved_validation(index)
            def validate(question,**kwargs):return pv.validate_candidate_answer(question,**kwargs,client=client,emit_telemetry=False)
            with patch.object(main,'validate_candidate_answer',side_effect=validate),patch.object(main,'repair_answer_once',side_effect=AssertionError('No replay generation')):
                result,audit=self.caller(inputs['candidate'],chunks,question=inputs['question'])
            sent=json.loads(client.requests[0]['messages'][1]['content'])
            observations[label]=dict(response_type=result['response_type'],action=audit.action,
                input_tokens=audit.input_tokens,output_tokens=audit.output_tokens,
                reported_cost_usd=audit.estimated_cost_usd,receipt_input_tokens=client.response.usage.prompt_tokens,
                numeric_obligations=sent.get('numeric_obligations'),scope_obligations=sent.get('scope_obligations'))
        from scripts.test_phase53_evidence_assessment import _request_assessment
        raw=read(FOLDER/'run/raw/call-007.json');inputs=json.loads(raw['request']['messages'][1]['content'])
        chunks=[replace(chunk(e['chunk_id'],e['content']),document_id=e['document_id']) for e in inputs['authorized_retrieved_chunks']]
        client=Client(captured(7))
        assessed=ea.assess_evidence(read(FOLDER/'run/check-02.json')['request']['question'],request_assessment=_request_assessment(),authorized_chunks=chunks,
            multi_document=False,mode='hybrid',client=client,emit_telemetry=False)
        observations['false_premise']=dict(action=assessed.recommended_action,
            generation_action=ea.evidence_generation_action(assessed),
            answerability_target=json.loads(client.requests[0]['messages'][1]['content']).get('answerability_target'),
            captured_missing_information=json.loads(client.response.choices[0].message.content)['missing_information'])
        inputs,chunks,_=saved_validation(24);client=Client(captured(23))
        metadata={c['chunk_id']:c for c in read(FOLDER/'run/check-05.json')['authorized_evidence']}
        chunks=[replace(c,access_roles=metadata[c.chunk_id]['access_roles']) for c in chunks]
        with patch.object(gen,'_client',return_value=client):
            answer=gen.generate_answer(inputs['question'],chunks,user_role='IT/Admin',evidence_action='answer')
        observations['malformed_generation']=dict(response_type=answer['response_type'],raw_json_displayed=answer['answer'].lstrip().startswith('{'),
            structured_output=bool(client.requests[0].get('response_format')),input_tokens=answer['input_tokens'])
        self.assertEqual(answer['response_type'],'not_found')
        self.assertFalse(observations['malformed_generation']['raw_json_displayed'])
        self.assertEqual(assessed.recommended_action,'not_found')
        from scripts.application_reliability_live_v2 import Ledger
        from scripts.reliability_payload_budget import reservation
        body=read(FOLDER/'run/raw/call-000.json')['request']
        # Same captured payload, deliberately permuted nested insertion order.
        def reverse_keys(value):
            if isinstance(value,dict):return {k:reverse_keys(v) for k,v in reversed(list(value.items()))}
            if isinstance(value,list):return [reverse_keys(v) for v in value]
            return value
        body=reverse_keys(body)
        with tempfile.TemporaryDirectory() as tmp:
            ledger=Ledger(Path(tmp),Mock());ledger.begin_case('offline')
            ledger.call(lambda **kw:captured(0),body,'chat')
            stored=read(Path(tmp)/'raw/call-000.json')['request']
            observations['payload_order']=dict(before=reservation(body,'chat')[0],after_persistence=reservation(stored,'chat')[0])
        from scripts.reliability_payload_preparation import submit_prepared
        with tempfile.TemporaryDirectory() as tmp:
            ledger=Ledger(Path(tmp),Mock());ledger.begin_case('offline')
            submitted=[]
            submit_prepared(ledger,lambda **kw:(submitted.append(kw) or captured(0)),body,'chat')
            stored=read(Path(tmp)/'raw/call-000.json')['request']
            observations['payload_order']['prepared_bound']=reservation(submitted[0],'chat')[0]
            observations['payload_order']['prepared_persisted_bound']=reservation(stored,'chat')[0]
            self.assertEqual(reservation(submitted[0],'chat'),reservation(stored,'chat'))
        self.observations=observations
        print(json.dumps(observations,indent=2))
        if RECORD:
            OUT.mkdir(parents=True,exist_ok=True)
            destination=OUT/RECORD
            with destination.open('x',encoding='utf-8') as handle:
                handle.write(json.dumps(observations,indent=2)+'\n')

    def payload(self,text,*,numeric=None,scope=True,support='supported'):
        result=semantic_payload(support=support)
        units=pv.candidate_units(text)
        result['claims']=[dict(claim_id=u['claim_id'],claim_text=u['claim_text'],claim_type='semantic',
            support_status=support,evidence_chunk_ids=['c1'] if support=='supported' else []) for u in units]
        result['citation_checks'][0]['supported_claim_ids']=[u['claim_id'] for u in units] if support=='supported' else []
        result['citation_checks'][0]['supports_claims']=support=='supported'
        result['numeric_context']=numeric or []
        result['scope_checks']=[dict(claim_id=u['claim_id'],preserves_scope=scope,explanation='The cited rule has the same condition.' if scope else 'The condition applies only to overnight work.') for u in units]
        return result

    def check(self,text,source,*,question='Explain the applicable rule.',payload=None,repair_count=0):
        client=Client(fake(payload if payload is not None else self.payload(text)))
        result=pv.validate_candidate_answer(question,candidate=candidate(text),authorized_chunks=[chunk(content=source)],
            client=client,repair_count=repair_count,emit_telemetry=False)
        return result,client

    def test_numeric_scenario_positive_and_policy_negative(self):
        text='Your EUR 93 order is below the EUR 240 approval threshold.'
        source='Supply orders above EUR 240 need supervisor approval.'
        question='For my EUR 93 order, does the supply threshold require approval?'
        numeric=[dict(claim_id='claim-1',literal='EUR 93',origin='user_scenario',request_quote='my EUR 93 order')]
        result,client=self.check(text,source,question=question,payload=self.payload(text,numeric=numeric))
        self.assertEqual(result.action,'accept')
        schema=client.requests[0]['response_format']['json_schema']['schema']
        self.assertEqual(schema['properties']['numeric_context']['minItems'],1)
        self.assertEqual(json.loads(client.requests[0]['messages'][1]['content'])['numeric_obligations'],
            [dict(claim_id='claim-1',literal='EUR 93',present_in_request=True)])
        for origin,quote in [('policy','my EUR 93 order'),('unsupported','my EUR 93 order'),('user_scenario','a different EUR 93 order')]:
            with self.subTest(origin=origin,quote=quote):
                n=[{**numeric[0],'origin':origin,'request_quote':quote}]
                rejected,_=self.check(text,source,question=question,payload=self.payload(text,numeric=n))
                self.assertNotEqual(rejected.action,'accept')

    def test_missing_numeric_and_wrong_currency_stay_blocked(self):
        text='Your EUR 93 order is below the limit.'
        for question in ['For my EUR 93 order, what happens?','For my CAD 93 order, what happens?']:
            result,_=self.check(text,'The limit is EUR 240.',question=question)
            self.assertNotEqual(result.action,'accept')

    def test_scope_positive_negative_and_repair_limit(self):
        source='Extended shifts need supervisor review. Overnight shifts need supervisor review and are suspended until review.'
        good='Extended shifts need supervisor review; only overnight shifts are suspended until review.'
        bad='Extended and overnight shifts need supervisor review and such shifts are suspended until review.'
        self.assertEqual(self.check(good,source)[0].action,'accept')
        payload=self.payload(bad,scope=False)
        self.assertEqual(self.check(bad,source,payload=payload)[0].action,'repair')
        self.assertEqual(self.check(bad,source,payload=payload,repair_count=1)[0].action,'downgrade')

    def test_scope_failure_through_caller_repairs_once_or_downgrades(self):
        source='Daytime work needs review; overnight work is suspended until review.'
        bad='Daytime and overnight work are suspended until review.'
        good='Daytime work needs review; overnight work is suspended until review.'
        for repaired_text,expected in [(good,'answer'),(bad,'not_found')]:
            def validate(question,**kwargs):
                text=kwargs['candidate']['answer']
                client=Client(fake(self.payload(text,scope=text!=bad)))
                return pv.validate_candidate_answer(question,**kwargs,client=client,emit_telemetry=False)
            original={**candidate(bad),'input_tokens':10,'output_tokens':10}
            fixed={**candidate(repaired_text),'input_tokens':10,'output_tokens':10}
            with patch.object(main,'validate_candidate_answer',side_effect=validate),patch.object(main,'repair_answer_once',return_value=fixed) as repair:
                result,audit=self.caller(original,[chunk(content=source)])
            self.assertEqual(repair.call_count,1)
            self.assertEqual(audit.repair_count,1)
            self.assertEqual(result['response_type'],expected)
            self.assertEqual(audit.input_tokens,274)

    def test_numeric_obligation_cardinality_and_normalized_repetition(self):
        text='Your EUR 1,230 order (EUR 1230) needs review.'
        source='Supply orders above EUR 1000 need review.'
        question='What about my EUR 1230 order?'
        numeric=[dict(claim_id='claim-1',literal='EUR 1230',origin='user_scenario',request_quote='my EUR 1230 order')]
        result,client=self.check(text,source,question=question,payload=self.payload(text,numeric=numeric))
        self.assertEqual(result.action,'accept')
        self.assertEqual(client.requests[0]['response_format']['json_schema']['schema']['properties']['numeric_context']['minItems'],1)
        for extra in [numeric[0],{**numeric[0],'claim_id':'invented'}]:
            result,_=self.check(text,source,question=question,payload=self.payload(text,numeric=[*numeric,extra]))
            self.assertEqual(result.status,'failed_safe')

    def test_scope_and_numeric_interaction_does_not_override_rejection(self):
        text='Your 9 days of daytime work requires review and is suspended.'
        numeric=[dict(claim_id='claim-1',literal='9 days',origin='user_scenario',request_quote='my 9 days of daytime work')]
        result,_=self.check(text,'Daytime work requires review; only overnight work is suspended.',
            question='What happens for my 9 days of daytime work?',payload=self.payload(text,numeric=numeric,scope=False))
        self.assertNotEqual(result.action,'accept')

    def test_scope_contract_rejects_missing_duplicate_and_rewritten_units(self):
        text='Daytime work requires review. Overnight work is suspended.'
        for variant in ['missing','duplicate','rewrite']:
            payload=self.payload(text)
            if variant=='missing':payload['scope_checks'].pop()
            elif variant=='duplicate':payload['scope_checks'][1]=payload['scope_checks'][0]
            else:payload['claims'][0]['claim_text']='Work requires review.'
            result,_=self.check(text,text,payload=payload)
            self.assertEqual(result.status,'failed_safe')

    def test_overflow_stops_before_provider(self):
        for count in [16,17]:
            text='\n'.join(['Review is required.']*count)
            # Split citation checks to respect the existing per-citation claim cap.
            payload=self.payload(text)
            payload['citation_checks']=[{**payload['citation_checks'][0],'supported_claim_ids':[f'claim-{i}' for i in range(1, min(count,12)+1)]},
                {**payload['citation_checks'][0],'supported_claim_ids':[f'claim-{i}' for i in range(13,count+1)]}]
            result,client=self.check(text,'Review is required.',payload=payload)
            self.assertEqual(len(client.requests),1 if count==16 else 0)
            self.assertEqual(result.action,'accept' if count==16 else 'downgrade')

    def test_validation_usage_survives_invalid_contract_refusal_and_timeout(self):
        text='A supervisor reviews the request.'
        responses=[fake({}),fake(self.payload(text)),TimeoutError('offline timeout')]
        responses[1].choices[0].message.refusal='declined'
        for response in responses:
            client=Client(response)
            result=pv.validate_candidate_answer('Who reviews?',candidate=candidate(text),authorized_chunks=[chunk(content=text)],client=client,emit_telemetry=False)
            self.assertEqual(result.status,'failed_safe')
            self.assertEqual(result.input_tokens,None if isinstance(response,Exception) else 137)
            self.assertEqual(result.output_tokens,None if isinstance(response,Exception) else 61)
            if isinstance(response,Exception):self.assertIsNone(result.estimated_cost_usd)
            else:self.assertGreater(result.estimated_cost_usd,0)

    def test_unknown_usage_remains_unknown_when_combining_attempts(self):
        text='A supervisor reviews the request.'
        known,_=self.check(text,text)
        missing=pv.validate_candidate_answer('Who reviews?',candidate=candidate(text),authorized_chunks=[chunk(content=text)],
            client=Client(fake(self.payload(text),usage=False)),emit_telemetry=False)
        for first,second in [(known,missing),(missing,known)]:
            combined=pv.combine_validation_attempts(first,second)
            self.assertIsNone(combined.input_tokens)
            self.assertIsNone(combined.estimated_cost_usd)
            self.assertEqual(combined.pricing_status,'missing_token_usage')

    def assess(self,payload,source='Portable displays have a EUR 460 allowance.'):
        from scripts.test_phase53_evidence_assessment import _request_assessment
        client=Client(fake(payload))
        result=ea.assess_evidence('Is the portable display allowance EUR 310?',request_assessment=_request_assessment(),
            authorized_chunks=[chunk(content=source)],multi_document=False,mode='hybrid',client=client,emit_telemetry=False)
        return result,client

    def test_source_correction_vs_missing_topical_fact(self):
        from scripts.test_reliability_remediation_v2 import evidence
        for support,ids,expected in [('contradicted',['c1'],'answer'),('supported',['c1'],'answer'),
                ('unsupported',['c1'],'not_found'),('contradicted',['secret'],'not_found')]:
            payload=evidence([(support,ids)]).model_dump()
            payload['required_facts'][0]['description']='What is the portable display allowance?'
            result,client=self.assess(payload)
            self.assertEqual(result.recommended_action,expected)
            self.assertIn('answerability_target',json.loads(client.requests[0]['messages'][1]['content']))

    def test_evidence_invalid_response_keeps_usage(self):
        result,_=self.assess({})
        self.assertEqual(result.recommended_action,'temporary_unavailable')
        self.assertEqual(result.input_tokens,137)
        self.assertGreater(result.estimated_cost_usd,0)

    def generated(self):
        return dict(answer='A supervisor reviews portable display orders.',response_type='answer',
            citations=[dict(chunk_id='c1',citation_text='A supervisor reviews portable display orders.')],
            supported_claims=[],unsupported_claims=[],validation_notes='')

    def test_generation_good_json_and_invalid_shapes(self):
        payload=self.generated();source=chunk(content=payload['answer'])
        for body in [payload,{**payload,'answer':{'unexpected':'object'}},{**payload,'response_type':'unknown'},
                {**payload,'citations':['bad']},{**payload,'supported_claims':'not a list'}]:
            client=Client(fake(body))
            with patch.object(gen,'_client',return_value=client):
                result=gen.generate_answer('Who reviews portable display orders?',[source],user_role='Employee',evidence_action='answer')
            self.assertEqual(result['response_type'],'answer' if body==payload else 'not_found')
            self.assertEqual(result['input_tokens'],137)
            self.assertTrue(client.requests[0]['response_format']['json_schema']['strict'])
            if body!=payload:self.assertEqual(result['citations'],[])

    def test_repair_and_stream_use_structured_output(self):
        payload=self.generated();source=chunk(content=payload['answer'])
        client=Client(fake(payload))
        with patch.object(gen,'_client',return_value=client):
            repaired=gen.repair_answer_once('Who reviews portable display orders?',[source],candidate=candidate('Unsourced answer.'),
                validation_reason_codes=['claim_unsupported'],user_role='Employee')
        self.assertEqual(repaired['response_type'],'answer')
        self.assertTrue(client.requests[0]['response_format']['json_schema']['strict'])
        for raw,expected in [(json.dumps(payload),'answer'),('{broken json','not_found')]:
            events=[SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=raw))],usage=None),
                    SimpleNamespace(choices=[],usage=SimpleNamespace(prompt_tokens=137,completion_tokens=61))]
            client=Client(iter(events))
            with patch.object(gen,'_client',return_value=client):
                result=list(gen.generate_answer_stream('Who reviews portable display orders?',[source],user_role='Employee',evidence_action='answer'))
            self.assertEqual(result[-1]['answer']['response_type'],expected)
            self.assertTrue(client.requests[0]['response_format']['json_schema']['strict'])

    def test_generation_unauthorized_chunks_never_call_provider(self):
        client=Client(fake(self.generated()))
        with patch.object(gen,'_client',return_value=client):
            result=gen.generate_answer('Who reviews portable display orders?',
                [replace(chunk(),access_roles=['IT/Admin'],restricted=True)],user_role='Employee')
        self.assertEqual(result['response_type'],'refuse_no_access')
        self.assertEqual(client.requests,[])

    def test_preparation_preserves_content_and_rejects_unpriced_payloads(self):
        from scripts.reliability_payload_preparation import prepare_request
        from scripts.application_reliability_live import Stop
        body=dict(model='gpt-4.1-mini',messages=[dict(role='user',content='Résumé: £93 / EUR 240')],max_completion_tokens=120)
        original=json.dumps(body,ensure_ascii=False)
        prepared,bound=prepare_request(body,'chat')
        self.assertEqual(prepared,body)
        self.assertEqual(original,json.dumps(body,ensure_ascii=False))
        self.assertEqual(bound,prepare_request(json.loads(json.dumps(prepared,sort_keys=True)),'chat')[1])
        for changed in [{**body,'stream':True},{**body,'max_completion_tokens':2049},{**body,'model':'unpriced'}]:
            with self.assertRaises(Stop):prepare_request(changed,'chat')
        with self.assertRaises(ValueError):prepare_request({**body,'temperature':float('nan')},'chat')

RECORD=None
REPLAY_VERSION='v4'
if __name__=='__main__':
    if '--legacy-replay' in sys.argv:
        sys.argv.remove('--legacy-replay');REPLAY_VERSION='v3'
    if '--record-replay' in sys.argv:
        i=sys.argv.index('--record-replay');RECORD=sys.argv[i+1];del sys.argv[i:i+2]
    unittest.main(verbosity=2)
