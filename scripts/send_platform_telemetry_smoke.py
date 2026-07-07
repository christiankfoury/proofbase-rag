from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from apps.api.app.observability.platform_telemetry import submit_platform_telemetry


def main() -> None:
    event = {
        "event_id": f"evt_proofbase_smoke_{uuid4().hex}",
        "external_request_id": f"proofbase_req_smoke_{uuid4().hex}",
        "source_app": "proofbase",
        "operation_type": "rag_query",
        "environment": "local",
        "occurred_at": datetime.now(UTC).isoformat(),
        "status": "succeeded",
        "provider": "mock",
        "model": "mock-proofbase-smoke",
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
        "estimated_cost_usd": "0.000000",
        "currency": "USD",
        "pricing_status": "estimated",
        "latency_ms": 1,
        "metadata": {"streaming": False, "citation_count": 0},
    }
    sent = submit_platform_telemetry(event)
    print("submitted" if sent else "not submitted")


if __name__ == "__main__":
    main()
