from copy import deepcopy
from decimal import Decimal
import socket
import unittest
from unittest.mock import patch
from scripts import controlled_diagnosis_v1 as d


class ControlledTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(socket.socket,'connect',side_effect=AssertionError('Offline only')))
        self.row=deepcopy(d.read(d.OUT/'ad1/v1/traces.json')['rows'][0])
        self.row.update(corpus_binding=d.sha(d.OLD/'development-v2.json'),profile_binding=d.profile_binding(self.row))
        self.spec=dict(d.core(self.row),source_binding=d.traces.fingerprint(self.row['authorized_sources']))

    def test_changed_inputs_cannot_reuse_observation(self):
        for field,value in [('original_question','Different question'),('history',[dict(role='user',content='Correction')]),
                            ('runtime_commit','other'),('profile_binding','other'),('corpus_binding','other'),('expected','Different facts')]:
            row=deepcopy(self.row);row[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError): d.observe(self.spec,row,'reference')

    def test_context_and_output_cannot_be_transplanted(self):
        row=deepcopy(self.row); row['authorized_sources'][0]['content']='A different context.'
        with self.assertRaises(ValueError): d.observe(self.spec,row,'reference')
        row=deepcopy(self.row);row['delivered']['answer']='Invented success'
        with self.assertRaises(ValueError): d.observe(self.spec,row,'reference')

    def test_role_project_department_and_duplicate_guards(self):
        for field,value in [('access_roles',['HR Admin']),('project_id','different'),('department_id','different')]:
            row=deepcopy(self.row)
            if field=='department_id':row['scope']['department_id']='requested'
            row['authorized_sources'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):d.check_authorized(row['authorized_sources'],row['scope'])
        with self.assertRaises(ValueError): d.check_authorized(self.row['authorized_sources']*2,self.row['scope'])

    def test_normal_arm_missing_even_if_flag_is_forged(self):
        self.row['retrieval']['normal_index_observation']=True
        self.assertEqual(d.observe(self.spec,self.row,'normal_retrieval')['status'],'not_executed')

    def test_draft_checker_binding_and_missing_stage(self):
        self.assertEqual(d.chain(self.row)['status'],'executed_saved_evidence')
        row=deepcopy(self.row);row['calls']=[c for c in row['calls'] if c['stage']!='generated_answer_v1']
        self.assertEqual(d.chain(row)['status'],'missing_stages')
        row=deepcopy(self.row)
        next(c for c in row['calls'] if c['stage']=='generated_answer_v1')['response']['answer']='unmatched draft'
        with self.assertRaises(ValueError): d.chain(row)
        row=deepcopy(self.row)
        next(c for c in row['calls'] if c['stage']=='post_generation_validation_v1')['response']['claims']=[]
        with self.assertRaises(ValueError): d.chain(row)

    def test_full_replay_budget_and_no_release_credit(self):
        result=d.build()
        self.assertEqual(result,d.read(d.OUT/'ad2/v1/comparisons.json'))
        self.assertEqual(len(result['comparisons']),24)
        self.assertEqual(result['observed_normal_reference_pairs'],0)
        budget=result['proposal']
        self.assertEqual(sum(s['calls'] for s in budget['stages']),319)
        self.assertEqual(sum(Decimal(s['total_reservation_usd']) for s in budget['stages']),Decimal('2.83623424'))
        self.assertFalse(budget['provider_execution_available'])
        self.assertFalse(result['release_eligible'])
        self.assertEqual(result['new_model_calls'],0)


if __name__=='__main__': unittest.main()
