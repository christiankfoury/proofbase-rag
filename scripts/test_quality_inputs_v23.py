"""No-network custody controls for attribution metadata on real-shaped inputs."""
from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from scripts import quality_inputs_v23 as inputs


class MetadataCapture(unittest.TestCase):
    def fixture(self):
        return {'chunk_id': 'chunk', 'document_id': 'doc', 'content': 'Policy text.',
                'tenant_id': 'tenant', 'project_id': 'project'}

    def test_titles_come_from_authorized_database_rows(self):
        row = self.fixture()
        conn = MagicMock(); conn.__enter__.return_value = conn
        conn.execute.return_value.fetchone.return_value = ('Authoritative title',)
        payload = {'citations': [{'document_title': 'Answer-invented title'}]}
        with patch('scripts.run_fresh_eval.authoritative_evidence', return_value=([row], [])), \
             patch('psycopg.connect', return_value=conn):
            evidence, flags = inputs.authoritative_evidence(SimpleNamespace(database_url='unused'), {}, payload)
        self.assertEqual(evidence[0]['document_title'], 'Authoritative title')
        self.assertEqual(flags, [])
        self.assertEqual(conn.execute.call_args.args[1], ('chunk', 'doc', 'tenant', 'project'))

    def test_unauthorized_rows_are_never_looked_up_for_titles(self):
        conn = MagicMock(); conn.__enter__.return_value = conn
        with patch('scripts.run_fresh_eval.authoritative_evidence', return_value=([], ['unauthorized_returned_evidence'])), \
             patch('psycopg.connect', return_value=conn):
            evidence, flags = inputs.authoritative_evidence(SimpleNamespace(database_url='unused'), {}, {})
        conn.execute.assert_not_called()
        self.assertEqual(evidence, [])
        self.assertEqual(flags, ['unauthorized_returned_evidence'])

    def test_missing_title_is_rejected(self):
        conn = MagicMock(); conn.__enter__.return_value = conn
        conn.execute.return_value.fetchone.return_value = None
        with patch('scripts.run_fresh_eval.authoritative_evidence', return_value=([self.fixture()], [])), \
             patch('psycopg.connect', return_value=conn):
            with self.assertRaisesRegex(ValueError, 'title missing'):
                inputs.authoritative_evidence(SimpleNamespace(database_url='unused'), {}, {})

    def test_inputs_preserve_text_and_bind_metadata(self):
        row = self.fixture(); row['document_title'] = 'Authoritative title'
        text = {'answer': 'Answer', 'factual_sources': [{'source_id': 'R1', 'text': row['content']}]}
        with patch.object(inputs, 'text_inputs', return_value=deepcopy(text)):
            actual = inputs.build_inputs({}, {'authorized_evidence': [row]})
        self.assertEqual(actual['factual_sources'], text['factual_sources'])
        self.assertEqual(actual['source_metadata'], [{'source_id': 'R1', 'document_id': 'doc', 'document_title': 'Authoritative title'}])
        with patch.object(inputs, 'text_inputs', return_value=deepcopy(text)):
            with self.assertRaisesRegex(ValueError, 'titles required'):
                inputs.build_inputs({}, {'authorized_evidence': [self.fixture()]})


if __name__ == '__main__':
    unittest.main()
