"""Replay the stopped preparation; no new payload run or provider calls."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.bounded_redesign_preflight import FOLDER, prepare, c


class PreflightTests(unittest.TestCase):
    def test_complete_stage_arithmetic_and_stop(self):
        plan=json.loads((FOLDER/'preflight-complete.json').read_bytes())
        total=Decimal(0)
        for profile,rows in plan['bounds'].items():
            expected=({'request_assessment_v1','evidence_assessment_v1','generated_answer_v1','post_generation_validation_v1'}
                if profile=='v4' else {'request_assessment_v1','conversational_producer','conversational_checker'})
            self.assertEqual({r['stage'] for r in rows},expected)
            subtotal=Decimal(0)
            for row in rows:
                ri,_,ro=map(Decimal,c.PRICES[row['model']])
                amount=row['count']*(row['input_bound']*ri+row['output_cap']*ro)/1000000
                self.assertEqual(amount,Decimal(row['reservation_usd']));subtotal+=amount
            self.assertEqual(subtotal,Decimal(plan['profiles'][profile]));total+=subtotal
        self.assertEqual(total,Decimal('1.7965755'))
        self.assertGreater(total,Decimal(plan['application_stage_cap_usd']))
        self.assertEqual(plan['status'],'stopped_budget_preflight')
        self.assertEqual(plan['suite_sha256'],hashlib.sha256((FOLDER/'development.json').read_bytes()).hexdigest())
        self.assertEqual(Decimal(plan['prior_remainder_usd'])+Decimal(plan['additional_allowance_usd']),Decimal('10'))

    def test_each_prepared_payload_replays_and_unpriced_requests_fail(self):
        plan=json.loads((FOLDER/'preflight-complete.json').read_bytes())
        for row in plan['prepared_payloads']:
            body,bound=prepare(row['request'])
            self.assertEqual(body,row['request'])
            self.assertEqual(bound,prepare(json.loads(json.dumps(body,sort_keys=True)))[1])
            stage=next(s for s in plan['bounds'][row['profile']] if s['stage']==row['stage'])
            self.assertLessEqual(bound['input_bound'],stage['input_bound'])
            self.assertEqual(bound['output_cap'],stage['output_cap'])
        for changes in [dict(model='unapproved'),dict(stream=True),dict(max_completion_tokens=9000)]:
            with self.assertRaises(ValueError):prepare(dict(plan['prepared_payloads'][0]['request'],**changes))


if __name__=='__main__':unittest.main()
