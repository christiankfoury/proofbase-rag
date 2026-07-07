# ruff: noqa: E402,I001

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.app.observability.auxiliary_telemetry import submit_auxiliary_telemetry  # noqa: E402
from apps.api.app.observability.query_telemetry import submit_query_telemetry  # noqa: E402
from apps.api.app.observability.tracing import RequestTrace  # noqa: E402


def _settings(enabled: bool = True):
    return SimpleNamespace(
        proofbase_telemetry_enabled=enabled,
        proofbase_telemetry_endpoint="http://mock-platform.local/v1/usage/llm-events",
        proofbase_telemetry_api_key="proofbase-local-placeholder-key-not-a-secret",
        proofbase_telemetry_timeout_seconds=0.5,
        proofbase_telemetry_max_metadata_bytes=2048,
        proofbase_telemetry_redact_content=True,
    )


def _query_request():
    return SimpleNamespace(
        question="What policy applies?",
        session_id="session-123",
        retrieval_mode="hybrid",
        chunking_strategy="section_based",
        top_k=5,
        prompt_name="answer_generation",
        prompt_version="v5",
        project_id="project-123",
        department_id="department-456",
    )


def _config():
    return SimpleNamespace(
        retrieval_mode="hybrid",
        chunking_strategy="section_based",
        top_k=5,
        project_id="project-123",
        department_id="department-456",
    )


def _trace():
    trace = RequestTrace()
    trace.retrieval_latency_ms = 6
    trace.generation_latency_ms = 13
    trace.total_latency_ms = 21
    return trace


class MockedPlatformReceiverTests(unittest.TestCase):
    def test_query_telemetry_posts_to_mocked_receiver_without_network(self) -> None:
        captured = []

        def sender(endpoint, payload, api_key, timeout):
            captured.append((endpoint, payload, api_key, timeout))
            return 202

        sent = submit_query_telemetry(
            request_id="req-123",
            request=_query_request(),
            operation_type="rag_query",
            status="succeeded",
            config=_config(),
            answer={
                "response_type": "answer",
                "citations": [],
                "prompt_name": "answer_generation",
                "prompt_version": "v5",
                "model": "gpt-4.1-mini",
                "input_tokens": 12,
                "output_tokens": 6,
                "estimated_cost_usd": "0.000014",
                "pricing_status": "estimated",
            },
            trace=_trace(),
            chunks=[],
            settings=_settings(),
            sender=sender,
        )

        self.assertTrue(sent)
        self.assertEqual(len(captured), 1)
        endpoint, payload, api_key, timeout = captured[0]
        self.assertEqual(endpoint, "http://mock-platform.local/v1/usage/llm-events")
        self.assertEqual(api_key, "proofbase-local-placeholder-key-not-a-secret")
        self.assertEqual(timeout, 0.5)
        self.assertEqual(payload["operation_type"], "rag_query")
        self.assertNotIn("What policy applies?", str(payload))

    def test_auxiliary_telemetry_posts_to_mocked_receiver(self) -> None:
        captured = []

        def sender(_endpoint, payload, _api_key, _timeout):
            captured.append(payload)
            return 202

        sent = submit_auxiliary_telemetry(
            operation_type="embedding_generation",
            model="text-embedding-3-small",
            input_tokens=20,
            pricing_status="unpriced",
            metadata={"embedding_count": 2, "cache_hit": False},
            settings=_settings(),
            sender=sender,
        )

        self.assertTrue(sent)
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]["operation_type"], "embedding_generation")
        self.assertEqual(captured[0]["pricing_status"], "unpriced")

    def test_receiver_failure_does_not_raise_or_block_workflow(self) -> None:
        def sender(*_args):
            raise TimeoutError("mock receiver unavailable")

        sent = submit_auxiliary_telemetry(
            operation_type="markdown_cleanup",
            model="gpt-4.1-mini",
            input_tokens=10,
            output_tokens=5,
            estimated_cost_usd="0.000012",
            pricing_status="estimated",
            settings=_settings(),
            sender=sender,
        )

        self.assertFalse(sent)


if __name__ == "__main__":
    unittest.main()
