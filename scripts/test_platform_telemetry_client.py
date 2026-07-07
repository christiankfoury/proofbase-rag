import io
import logging
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.app.observability.platform_telemetry import (
    sanitize_telemetry_event,
    submit_platform_telemetry,
)


def _settings(**overrides):
    defaults = {
        "proofbase_telemetry_enabled": True,
        "proofbase_telemetry_endpoint": "http://localhost:8000/v1/usage/llm-events",
        "proofbase_telemetry_api_key": "proofbase-local-placeholder-key-not-a-secret",
        "proofbase_telemetry_timeout_seconds": 2.0,
        "proofbase_telemetry_max_metadata_bytes": 2048,
        "proofbase_telemetry_redact_content": True,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _event() -> dict:
    return {
        "event_id": "evt_test",
        "external_request_id": "proofbase_req_test",
        "source_app": "proofbase",
        "operation_type": "rag_query",
        "environment": "local",
        "occurred_at": "2026-07-06T00:00:00Z",
        "status": "succeeded",
        "provider": "openai",
        "model": "gpt-4.1-mini",
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
        "estimated_cost_usd": "0.000010",
        "currency": "USD",
        "latency_ms": 100,
        "metadata": {"streaming": False, "citation_count": 2},
    }


class PlatformTelemetryClientTests(unittest.TestCase):
    def test_disabled_mode_does_not_call_sender(self) -> None:
        def sender(*_args):
            raise AssertionError("sender should not be called")

        self.assertFalse(
            submit_platform_telemetry(
                _event(),
                settings=_settings(proofbase_telemetry_enabled=False),
                sender=sender,
            )
        )

    def test_success_posts_sanitized_payload(self) -> None:
        captured = {}

        def sender(endpoint, payload, api_key, timeout):
            captured.update(
                {
                    "endpoint": endpoint,
                    "payload": payload,
                    "api_key": api_key,
                    "timeout": timeout,
                }
            )
            return 202

        self.assertTrue(submit_platform_telemetry(_event(), settings=_settings(), sender=sender))
        self.assertEqual(captured["endpoint"], "http://localhost:8000/v1/usage/llm-events")
        self.assertEqual(captured["api_key"], "proofbase-local-placeholder-key-not-a-secret")
        self.assertEqual(captured["timeout"], 2.0)
        self.assertEqual(captured["payload"]["source_app"], "proofbase")
        self.assertEqual(captured["payload"]["operation_type"], "rag_query")
        self.assertEqual(captured["payload"]["metadata"], {"streaming": False, "citation_count": 2})

    def test_failure_is_logged_without_secret(self) -> None:
        secret_key = "proofbase-local-placeholder-key-not-a-secret"

        def sender(*_args):
            raise TimeoutError("platform did not respond")

        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("proofbase.platform_telemetry")
        previous_level = logger.level
        logger.setLevel(logging.WARNING)
        logger.addHandler(handler)
        try:
            self.assertFalse(
                submit_platform_telemetry(
                    _event(),
                    settings=_settings(proofbase_telemetry_api_key=secret_key),
                    sender=sender,
                )
            )
        finally:
            logger.removeHandler(handler)
            logger.setLevel(previous_level)

        logs = log_stream.getvalue()
        self.assertIn("platform_telemetry_submission_failed", logs)
        self.assertIn("timeout", logs)
        self.assertNotIn(secret_key, logs)

    def test_sanitization_redacts_sensitive_content_fields(self) -> None:
        event = {
            **_event(),
            "prompt_text": "system prompt",
            "full_question": "What did the user ask?",
            "retrieved_chunks": ["chunk text"],
            "openai_api_key": "fake-openai-key-not-real",
            "metadata": {
                "streaming": True,
                "question_hash": "abc123",
                "full_question": "What did the user ask?",
                "chunk_text": "raw chunk",
                "document_text": "raw document",
            },
        }

        payload = sanitize_telemetry_event(event, redact_content=True, max_metadata_bytes=2048)

        self.assertNotIn("prompt_text", payload)
        self.assertNotIn("full_question", payload)
        self.assertNotIn("retrieved_chunks", payload)
        self.assertNotIn("openai_api_key", payload)
        self.assertEqual(payload["metadata"], {"streaming": True, "question_hash": "abc123"})

    def test_sanitization_enforces_metadata_size(self) -> None:
        payload = sanitize_telemetry_event(
            {
                **_event(),
                "metadata": {
                    "retrieval_mode": "hybrid",
                    "chunking_strategy": "section_based",
                    "document_external_id": "x" * 500,
                },
            },
            redact_content=True,
            max_metadata_bytes=40,
        )

        self.assertEqual(payload["metadata"], {"retrieval_mode": "hybrid"})


if __name__ == "__main__":
    unittest.main()
