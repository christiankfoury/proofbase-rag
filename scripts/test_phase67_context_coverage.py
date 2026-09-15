"""Offline development variants; never execute or relabel a sealed case."""
import unittest
from dataclasses import replace
from unittest.mock import patch

from apps.api.app.memory.query_rewriter import rewrite_followup_question
from apps.api.app.reasoning.multi_doc_detector import is_multi_document_question
from apps.api.app.reasoning.query_decomposer import retrieve_multi_doc
from apps.api.app.retrieval.config import default_retrieval_config
from scripts.test_phase39_multi_doc_orchestration import _chunk


class ContextCoverageTests(unittest.TestCase):
    def test_excluded_topic_does_not_replace_requested_topic(self):
        context = "I mean the relocation allowance, not vacation days."
        result = rewrite_followup_question("Can I carry it forward?", [
            {"role": "user", "content": context},
            {"role": "assistant", "content": "Vacation days last forever."},
        ])
        self.assertIn(context, result["rewritten_question"])
        self.assertTrue(result["rewritten_question"].startswith("Can I carry it forward?"))

    def test_new_unknown_topic_beats_older_known_topic(self):
        result = rewrite_followup_question("Who approves that?", [
            {"role": "user", "content": "Actually, parental leave is my topic."},
            {"role": "user", "content": "Explain the relocation allowance."},
        ])
        self.assertIn("relocation allowance", result["previous_topic"])
        self.assertNotIn("parental leave", result["previous_topic"])

    def test_return_to_first_preserves_unknown_first_topic(self):
        result = rewrite_followup_question("Going back to the first topic, who approves it?", [
            {"role": "user", "content": "Explain the relocation allowance."},
            {"role": "user", "content": "Explain parental leave."},
        ])
        self.assertIn("relocation allowance", result["previous_topic"])

    def test_multiple_topics_are_not_collapsed(self):
        context = "Compare vacation days and parental leave."
        result = rewrite_followup_question("Does that apply to adoptive parents?", [
            {"role": "user", "content": context}])
        self.assertIn(context, result["rewritten_question"])

    def test_simple_positive_topic_keeps_existing_fast_path(self):
        result = rewrite_followup_question("Can I carry those forward?", [
            {"role": "user", "content": "Explain vacation days."}])
        self.assertEqual("vacation_carryover", result["rewrite_strategy"])

    def test_followup_chain_retains_user_anchor_without_assistant_claims(self):
        result = rewrite_followup_question("Does that expire?", [
            {"role": "user", "content": "Explain the relocation allowance."},
            {"role": "assistant", "content": "A made-up policy permits everything."},
            {"role": "user", "content": "Who approves it?"},
        ])
        self.assertIn("relocation allowance", result["rewritten_question"])
        self.assertNotIn("made-up", result["rewritten_question"])

    def test_independent_questions_trigger_multi_retrieval(self):
        for question in (
            "Who approves conference travel and when must incident reports be filed?",
            "What is the equipment allowance? Who approves conference travel?",
        ):
            with self.subTest(question=question):
                self.assertTrue(is_multi_document_question(question))
        self.assertFalse(is_multi_document_question("Where is the research and development office?"))

    def test_unplanned_subquery_survives_cross_query_score_imbalance(self):
        high = [_chunk(f"a-{i}", "A", 0.99 - i / 100) for i in range(8)]
        medium = [_chunk(f"b-{i}", "B", 0.7 - i / 100) for i in range(8)]
        low = [_chunk("c", "C", 0.1)]
        config = replace(default_retrieval_config(), project_id="project-test", department_id="department-test")
        with patch("apps.api.app.reasoning.query_decomposer.plan_multi_document_sources", return_value=[]), \
             patch("apps.api.app.reasoning.query_decomposer.decompose_question", return_value=["one", "two", "three"]), \
             patch("apps.api.app.reasoning.query_decomposer.retrieve_chunks", side_effect=[high, medium, low]) as retrieval:
            results = retrieve_multi_doc("Three independent requests", "Employee", config)
        self.assertEqual({"A", "B", "C"}, {c.document_id for c in results})
        self.assertLessEqual(len(results), 10)
        self.assertEqual(len(results), len({c.chunk_id for c in results}))
        for call in retrieval.call_args_list:
            self.assertEqual("Employee", call.args[1])
            self.assertEqual(config.project_id, call.args[2].project_id)
            self.assertEqual(config.department_id, call.args[2].department_id)


if __name__ == "__main__":
    unittest.main()
