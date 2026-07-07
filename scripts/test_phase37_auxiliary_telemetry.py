# ruff: noqa: E402,I001

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.app.observability.auxiliary_telemetry import (  # noqa: E402
    build_auxiliary_telemetry_event,
    normalize_pricing_status,
)


class AuxiliaryTelemetryTests(unittest.TestCase):
    def test_markdown_cleanup_event_uses_safe_cost_and_document_metadata(self) -> None:
        event = build_auxiliary_telemetry_event(
            operation_type="markdown_cleanup",
            model="gpt-4.1-mini",
            prompt_name="markdown_cleanup",
            input_tokens=100,
            output_tokens=25,
            estimated_cost_usd="0.000080",
            pricing_status="estimated",
            latency_ms=42,
            project_external_id="project-123",
            department_external_id="department-456",
            document_external_id="doc-789",
            metadata={"document_count": 1},
        )

        self.assertEqual(event["operation_type"], "markdown_cleanup")
        self.assertEqual(event["status"], "succeeded")
        self.assertEqual(event["provider"], "openai")
        self.assertEqual(event["total_tokens"], 125)
        self.assertEqual(event["estimated_cost_usd"], "0.000080")
        self.assertEqual(event["pricing_status"], "estimated")
        self.assertEqual(event["project_external_id"], "project-123")
        self.assertEqual(event["department_external_id"], "department-456")
        self.assertEqual(event["metadata"]["document_external_id"], "doc-789")
        self.assertNotIn("source_markdown", str(event))
        self.assertNotIn("cleaned_markdown", str(event))

    def test_query_decomposition_event_hashes_question_without_content(self) -> None:
        question = "Compare policy A with policy B"
        event = build_auxiliary_telemetry_event(
            operation_type="query_decomposition",
            model="gpt-4.1-mini",
            prompt_name="query_decomposition",
            input_tokens=50,
            output_tokens=20,
            pricing_status="estimated",
            question=question,
            status="failed",
            error_category="invalid_provider_response",
            error_message_redacted="Query decomposition returned invalid JSON",
        )

        self.assertEqual(event["operation_type"], "query_decomposition")
        self.assertEqual(event["status"], "failed")
        self.assertIn("question_hash", event["metadata"])
        self.assertEqual(event["error_category"], "invalid_provider_response")
        self.assertNotIn(question, str(event))

    def test_embedding_event_is_unpriced_when_only_usage_exists(self) -> None:
        event = build_auxiliary_telemetry_event(
            operation_type="embedding_generation",
            model="text-embedding-3-small",
            input_tokens=256,
            pricing_status="missing_model_price",
            metadata={"embedding_count": 8, "cache_hit": False},
        )

        self.assertEqual(event["operation_type"], "embedding_generation")
        self.assertEqual(event["input_tokens"], 256)
        self.assertNotIn("estimated_cost_usd", event)
        self.assertEqual(event["pricing_status"], "unpriced")
        self.assertEqual(event["metadata"]["embedding_count"], 8)
        self.assertEqual(event["metadata"]["cache_hit"], False)

    def test_pricing_status_normalization_matches_platform_contract(self) -> None:
        self.assertEqual(normalize_pricing_status("estimated"), "estimated")
        self.assertEqual(normalize_pricing_status("missing_model_price"), "unpriced")
        self.assertEqual(normalize_pricing_status("missing_token_usage"), "unknown")
        self.assertEqual(normalize_pricing_status("unexpected"), "unknown")


if __name__ == "__main__":
    unittest.main()
