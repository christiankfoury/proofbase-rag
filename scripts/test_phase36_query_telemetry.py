# ruff: noqa: E402,I001

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.app.observability.query_telemetry import (  # noqa: E402
    build_query_telemetry_event,
    query_error_category,
    redacted_error_message,
    submit_query_telemetry,
)
from apps.api.app.observability.tracing import RequestTrace  # noqa: E402


def _request(**overrides):
    defaults = {
        "question": "What contract terms apply to employees?",
        "session_id": "session-123",
        "retrieval_mode": "vector_lexical_rerank",
        "chunking_strategy": "section_based",
        "top_k": 5,
        "prompt_name": "answer_generation",
        "prompt_version": "v5",
        "project_id": "project-123",
        "department_id": "department-456",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _config():
    return SimpleNamespace(
        retrieval_mode="hybrid",
        chunking_strategy="section_based",
        top_k=3,
        project_id="project-123",
        department_id="department-456",
    )


def _answer():
    return {
        "response_type": "answer",
        "citations": [{"document_id": "doc-1"}],
        "prompt_name": "answer_generation",
        "prompt_version": "v5",
        "model": "gpt-4.1-mini",
        "input_tokens": 120,
        "output_tokens": 45,
        "estimated_cost_usd": "0.000120",
        "pricing_status": "estimated",
    }


def _trace():
    trace = RequestTrace()
    trace.retrieval_latency_ms = 7
    trace.generation_latency_ms = 11
    trace.total_latency_ms = 20
    return trace


def _settings():
    return SimpleNamespace(
        proofbase_telemetry_enabled=True,
        proofbase_telemetry_endpoint="http://localhost:8000/v1/usage/llm-events",
        proofbase_telemetry_api_key="proofbase-local-placeholder-key-not-a-secret",
        proofbase_telemetry_timeout_seconds=2.0,
        proofbase_telemetry_max_metadata_bytes=2048,
        proofbase_telemetry_redact_content=True,
    )


class QueryTelemetryTests(unittest.TestCase):
    def test_non_streaming_query_event_maps_safe_operational_fields(self) -> None:
        event = build_query_telemetry_event(
            request_id="req-123",
            request=_request(),
            operation_type="rag_query",
            status="succeeded",
            config=_config(),
            answer=_answer(),
            trace=_trace(),
            chunks=[SimpleNamespace(document_id="doc-1"), SimpleNamespace(document_id="doc-1")],
        )

        self.assertEqual(event["event_id"], "evt_proofbase_rag_query_req123")
        self.assertEqual(event["external_request_id"], "req-123")
        self.assertEqual(event["source_app"], "proofbase")
        self.assertEqual(event["operation_type"], "rag_query")
        self.assertEqual(event["status"], "succeeded")
        self.assertEqual(event["provider"], "openai")
        self.assertEqual(event["model"], "gpt-4.1-mini")
        self.assertEqual(event["prompt_version"], "v5")
        self.assertEqual(event["input_tokens"], 120)
        self.assertEqual(event["output_tokens"], 45)
        self.assertEqual(event["total_tokens"], 165)
        self.assertEqual(event["estimated_cost_usd"], "0.000120")
        self.assertEqual(event["project_external_id"], "project-123")
        self.assertEqual(event["department_external_id"], "department-456")
        self.assertEqual(event["metadata"]["streaming"], False)
        self.assertEqual(event["metadata"]["document_count"], 1)
        self.assertEqual(event["metadata"]["chunk_count"], 2)
        self.assertIn("question_hash", event["metadata"])
        self.assertNotIn("question", event)
        self.assertNotIn("rewritten_question", event)
        self.assertNotIn("retrieved_chunks", event)

    def test_streaming_query_submits_one_completed_event(self) -> None:
        captured = []

        def sender(_endpoint, payload, _api_key, _timeout):
            captured.append(payload)
            return 202

        sent = submit_query_telemetry(
            request_id="req-stream",
            request=_request(),
            operation_type="rag_query_stream",
            status="succeeded",
            config=_config(),
            answer=_answer(),
            trace=_trace(),
            chunks=[],
            settings=_settings(),
            sender=sender,
        )

        self.assertTrue(sent)
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]["operation_type"], "rag_query_stream")
        self.assertEqual(captured[0]["metadata"]["streaming"], True)
        self.assertEqual(captured[0]["status"], "succeeded")

    def test_failure_event_is_redacted_and_classified(self) -> None:
        exc = RuntimeError("provider leaked raw payload")
        event = build_query_telemetry_event(
            request_id="req-failed",
            request=_request(),
            operation_type="rag_query",
            status="failed",
            config=_config(),
            answer={},
            trace=_trace(),
            error_category=query_error_category(exc),
            error_message_redacted=redacted_error_message(exc),
        )

        self.assertEqual(event["status"], "failed")
        self.assertEqual(event["error_category"], "generation_error")
        self.assertEqual(event["error_message_redacted"], "Generation failed")
        self.assertEqual(event["model"], "unknown")
        self.assertNotIn("provider leaked raw payload", str(event))
        self.assertNotIn("What contract terms apply", str(event))


if __name__ == "__main__":
    unittest.main()
