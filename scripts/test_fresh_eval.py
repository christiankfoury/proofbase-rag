import copy
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from scripts.fresh_eval_calibration import fixtures
from scripts.fresh_eval_grader import verdict
from scripts.fresh_eval_budget import Ledger, BudgetStop


class GraderTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures()[0]
        self.grade = {"behavior_correct": True, "facts": [{"fact_id": "F1", "status": "correct", "reason": "supported"}],
                      "claims": [{"text": self.f["payload"]["answer"], "kind": "factual", "supported": True, "citation_ids": ["C1"], "reason": "supported"}],
                      "all_factual_claims_enumerated": True, "all_citations_relevant": True,
                      "forbidden_assertion_present": False, "uncertain": False, "reason": "supported"}

    def evaluate(self):
        return verdict(self.f["case"], self.f["payload"], self.f["evidence"], self.grade, [])

    def test_valid_contract(self):
        self.assertTrue(self.evaluate()["passed"])

    def test_contradiction_and_missing_facts_fail(self):
        for status in ("contradicted", "missing", "uncertain"):
            self.grade["facts"][0]["status"] = status
            self.assertFalse(self.evaluate()["passed"])

    def test_invented_quote_and_source_fail(self):
        self.f["payload"]["citations"][0]["citation_text"] = "invented"
        self.assertFalse(self.evaluate()["passed"])
        self.f["payload"]["citations"][0]["chunk_id"] = "other"
        self.assertIn("citation_not_in_authorized_retrieval", self.evaluate()["failure_reasons"])

    def test_omitted_fact_and_claim_fail(self):
        self.grade["facts"] = []
        self.assertFalse(self.evaluate()["grader_valid"])
        self.grade["claims"] = []
        self.assertIn("empty_answer_claims", self.evaluate()["failure_reasons"])

    def test_unsupported_and_irrelevant_fail(self):
        self.grade["claims"][0]["supported"] = False
        self.grade["all_citations_relevant"] = False
        self.assertEqual(set(self.evaluate()["failure_reasons"]), {"unsupported_claim", "irrelevant_citation"})

    def test_invented_claim_fails(self):
        self.grade["claims"][0]["text"] = "not in candidate"
        self.assertFalse(self.evaluate()["grader_valid"])

    def test_nested_malformed_grade_fails_closed(self):
        self.grade["claims"][0]["citation_ids"] = [{}]
        self.assertFalse(self.evaluate()["grader_valid"])

    def test_partial_run_has_no_full_suite_rate(self):
        from scripts.run_fresh_eval import summarize
        cases = [{"case_id": "a", "expected_behavior": "answer"}, {"case_id": "b", "expected_behavior": "not_found"}]
        rows = [{"case_id": "a", "passed": True, "status": "complete", "failure_reasons": []}]
        result = summarize(cases, rows)
        self.assertIsNone(result["full_response"]["rate"])
        self.assertFalse(result["target_met"])

    def test_existing_run_never_restarts(self):
        from scripts.run_fresh_eval import require_unstarted
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                require_unstarted(Path(folder))

    def test_raw_response_survives_grader_failure(self):
        from unittest.mock import patch, MagicMock
        from scripts.run_fresh_eval import measure_case
        import json
        case = {"case_id": "fresh-001", "category": "factual", "user_id": "u", "project_id": "p", "question": "q"}
        client = MagicMock()
        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {"answer": "raw", "citations": []}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "case.json"
            ledger = Ledger(Path(folder) / "ledger.json")
            with patch("scripts.run_fresh_eval.authoritative_evidence", return_value=([], [])), patch("scripts.run_fresh_eval.grade_response", side_effect=ValueError("grader failed")):
                with self.assertRaises(ValueError):
                    measure_case(client, SimpleNamespace(openai_api_key="test-only"), case, path, ledger)
            self.assertEqual(json.loads(path.read_text())["raw_response"]["answer"], "raw")

    def test_budget_stops_before_call(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Ledger(Path(folder) / "ledger.json", 0.0001)
            def forbidden(*args, **kwargs):
                self.fail("Should not call provider")
            with self.assertRaises(BudgetStop):
                ledger.invoke("chat", forbidden, None, (), {"model": "gpt-4.1-mini", "messages": []})

    def test_accounting_and_unknown_outcome(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Ledger(Path(folder) / "ledger.json")
            def success(*args, **kwargs):
                return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20))
            ledger.invoke("chat", success, None, (), {"model": "gpt-4.1-mini", "messages": []})
            self.assertAlmostEqual(ledger.spent, 0.000036)
            def fail(*args, **kwargs):
                raise TimeoutError()
            with self.assertRaises(TimeoutError):
                ledger.invoke("chat", fail, None, (), {"model": "gpt-4.1-mini", "messages": []})
            self.assertTrue(ledger.data["unknown_outcome"])
            with self.assertRaises(BudgetStop):
                ledger.invoke("chat", success, None, (), {"model": "gpt-4.1-mini", "messages": []})


if __name__ == "__main__":
    unittest.main()
