import json
import socket
import unittest
from unittest.mock import patch
from scripts import application_diagnosis_v1 as d


class DiagnosisTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(socket.socket,'connect',side_effect=AssertionError('Offline only')))

    def test_complete_trace_replay_and_receipts(self):
        report=d.build()
        self.assertEqual(report,d.read(d.OUT/'ad1/v1/traces.json'))
        self.assertEqual(len(report['rows']),32)
        self.assertEqual([r['tasks'] for r in report['summaries']],[12,14])
        self.assertEqual(sum(r['calls'] for r in report['summaries']),101)
        self.assertTrue(all(r['stages_missing'] and r['annotation']['next_comparison'] for r in report['rows']))

    def test_saved_validator_failure_has_concrete_binding_cause(self):
        from apps.api.app.reasoning import post_generation_validation as v
        raw=d.read(d.OLD/'routing-v3-full-v4/run/raw/call-049.json')
        payload=json.loads(raw['request']['messages'][1]['content'])
        decision=v.SemanticValidationV4.model_validate(d.parsed(raw))
        saved=d.read(d.OLD/'routing-v3-full-v4/run/dev-12.json')
        chunks=[d.RetrievedChunk(**s) for s in saved['authorized_evidence']]
        with self.assertRaisesRegex(v.ValidationContractError,'supported candidate unit lacks a supporting citation'):
            v._validate_candidate_units(decision,payload['question'],payload['candidate'],chunks)
        # No repaired decision or output is produced: preserve the failed evidence.

    def test_private_fixture_source_is_excluded(self):
        report=d.read(d.OUT/'ad1/v1/traces.json')
        rows=[r for r in report['rows'] if r['case_id']=='dev-10']
        self.assertEqual(len(rows),2)
        for r in rows:
            self.assertEqual(r['authorized_sources'],[])
            self.assertNotIn('720',r['delivered']['answer'])

    def test_quote_repair_is_distinct_from_semantic_acceptance(self):
        report=d.read(d.OUT/'ad1/v1/traces.json')
        row=next(r for r in report['rows'] if r['profile']=='v4' and r['case_id']=='dev-08')
        self.assertFalse(row['draft_quote_checks'][0][0]['exact'])
        self.assertTrue(all(q['exact'] for q in row['final_quote_checks']))


if __name__=='__main__': unittest.main()
