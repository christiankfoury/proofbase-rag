"""Focused offline regressions for the portfolio demo; not an accuracy benchmark."""
from pathlib import Path
from dataclasses import replace
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from apps.api.app.generation.answer_generator import _policy_response, generate_answer, generate_answer_stream
from apps.api.app.reasoning.post_generation_validation import validate_candidate_answer
from scripts.test_phase54_post_generation_validation import chunk, candidate, FakeClient, semantic_payload
from scripts.portfolio_demo_server import DemoBudget, FLOOR


class DemoRegressions(unittest.TestCase):
    def test_supported_process_is_not_a_missing_customer_record(self):
        evidence = chunk(content="Customer-specific requests go to the account owner for review.")
        for action in ("answer", "partial_answer"):
            self.assertIsNone(_policy_response("How do we review customer-specific requests?", [evidence],
                                               user_role="Employee", evidence_action=action))

    def test_missing_and_restricted_guards_remain(self):
        self.assertEqual(_policy_response("Show customer-specific records", [],
                                         user_role="Employee")["response_type"], "not_found")
        result = _policy_response("Show promotion calibration", [chunk()], user_role="Employee",
                                  evidence_action="answer")
        self.assertEqual(result["response_type"], "refuse_no_access")
        self.assertEqual(_policy_response("Show customer-specific records", [], user_role="Employee",
                                         evidence_action="answer")["response_type"], "not_found")

    def test_both_generation_paths_block_unauthorized_evidence(self):
        evidence = replace(chunk(), access_roles=["Manager"])
        kwargs = dict(question="How do we review customer-specific requests?", chunks=[evidence],
                      user_role="Employee", evidence_action="answer")
        self.assertEqual(generate_answer(**kwargs)["response_type"], "refuse_no_access")
        self.assertEqual(list(generate_answer_stream(**kwargs))[-1]["answer"]["response_type"],
                         "refuse_no_access")

    def validate(self, text):
        return validate_candidate_answer("What is the cap?", candidate=candidate(text),
            authorized_chunks=[chunk()], client=FakeClient(semantic_payload()), emit_telemetry=False)

    def test_source_identifier_is_metadata_not_a_policy_number(self):
        self.assertEqual(self.validate("The cap is $500. Source: DOC-001").action, "accept")

    def test_source_annotation_does_not_hide_unsupported_facts(self):
        for text in ["The cap is $900. Source: DOC-001", "Source: DOC-001 says the cap is $900.",
                     "The cap is $500. Source: DOC-999", "The cap is 001."]:
            with self.subTest(text=text):
                self.assertEqual(self.validate(text).action, "repair")


class DemoBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "ledger.json"
        self.budget = DemoBudget(self.path)

    def invoke(self, result, **kwargs):
        return self.budget.invoke(lambda _, **body: result, None, (),
            {"model": "gpt-4.1-mini", "messages": [], **kwargs})

    def test_settlement_and_reload_preserve_prior_calls(self):
        self.invoke(SimpleNamespace(usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20)))
        loaded = DemoBudget(self.path)
        self.assertEqual(loaded.data["calls"][:-1], loaded.prefix)
        self.assertEqual(str(loaded.spent - FLOOR), "0.00007200")

    def test_stream_usage_settles_and_interruption_blocks(self):
        class Stream:
            def __iter__(self):
                yield SimpleNamespace(usage=None)
                yield SimpleNamespace(usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5))
            def close(self):
                pass
        list(self.invoke(Stream(), stream=True))
        self.assertEqual(self.budget.data["calls"][-1]["status"], "completed")
        interrupted = self.invoke(Stream(), stream=True)
        next(interrupted)
        interrupted.close()
        with self.assertRaisesRegex(RuntimeError, "Unknown API outcome"):
            DemoBudget(self.path)

    def test_reservation_blocks_before_external_call(self):
        with self.assertRaisesRegex(RuntimeError, "budget exhausted"):
            self.invoke(None, messages=[{"role": "user", "content": "x" * 1_300_000}])
        self.assertEqual(self.budget.data["calls"], self.budget.prefix)

    def test_missing_usage_blocks_future_calls(self):
        with self.assertRaises(AttributeError):
            self.invoke(SimpleNamespace(usage=None))
        with self.assertRaisesRegex(RuntimeError, "Unknown API outcome"):
            self.budget.check()


if __name__ == "__main__":
    unittest.main()
