from __future__ import annotations

import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.main import app
from apps.api.app.monitoring.security_events import (
    ALERT_RULES,
    LocalHashChainSecuritySink,
    LocalJsonlNotificationSink,
    SecurityMonitor,
    build_security_event,
    evaluate_alerts,
    sanitize_security_metadata,
)

ADMIN_USER = "00000000-0000-0000-0000-000000002706"
EMPLOYEE_USER = "00000000-0000-0000-0000-000000002701"
TENANT_A = "00000000-0000-0000-0000-000000000100"
TENANT_B = "00000000-0000-0000-0000-000000000200"


def event(category: str, tenant: str, **metadata: object) -> dict:
    return build_security_event(
        category=category,
        action="synthetic_tabletop_signal",
        outcome="blocked",
        reason="synthetic_test",
        tenant_id=tenant,
        user_id=f"user-for-{tenant}",
        correlation_id=f"request-for-{tenant}",
        metadata=metadata,
        occurred_at=datetime.now(UTC),
    )


def test_privacy_tenant_filter_alert_delivery_and_integrity() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        event_path = root / "events.jsonl"
        notification_path = root / "notifications.jsonl"
        sink = LocalHashChainSecuritySink(event_path)
        monitor = SecurityMonitor(sink, LocalJsonlNotificationSink(notification_path))
        secret = "phase61-private-prompt password=hunter2"

        for index in range(3):
            assert monitor.emit(
                event(
                    "injection_detection",
                    TENANT_A,
                    question=secret,
                    source_text=secret,
                    project_id=f"project-a-{index}",
                    event_count=index + 1,
                    stage="request_assessment",
                ),
                tenant_id=TENANT_A,
            )
        assert monitor.emit(event("cross_tenant_attempt", TENANT_B, question=secret), tenant_id=TENANT_B)

        stored = event_path.read_text(encoding="utf-8")
        assert TENANT_A not in stored and TENANT_B not in stored
        assert "user-for" not in stored and "request-for" not in stored
        assert secret not in stored and "source_text" not in stored and "question" not in stored
        tenant_a_events = sink.read_events(tenant_id=TENANT_A)
        assert len(tenant_a_events) == 3
        assert all(item["category"] == "injection_detection" for item in tenant_a_events)
        assert sink.read_events(tenant_id=TENANT_B)[0]["category"] == "cross_tenant_attempt"
        assert sink.verify()["valid"] is True

        delivered = [json.loads(line) for line in notification_path.read_text(encoding="utf-8").splitlines()]
        assert any(item["category"] == "injection_detection" for item in delivered)
        assert any(item["category"] == "cross_tenant_attempt" for item in delivered)
        assert all(item["notification_status"] == "local_delivery_only" for item in delivered)

        lines = event_path.read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        first["event"]["outcome"] = "tampered"
        lines[0] = json.dumps(first)
        event_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        assert sink.verify()["valid"] is False
        assert sink.read_events(tenant_id=TENANT_A) == []


def test_taxonomy_thresholds_and_metadata_allowlist() -> None:
    categories = {rule.category for rule in ALERT_RULES}
    assert categories == {
        "authentication_failure", "authorization_denial", "cross_tenant_attempt",
        "injection_detection", "evidence_validation_failure", "rate_limit",
        "malicious_upload", "parser_failure", "admin_change", "secret_config_failure",
        "unusual_cost",
    }
    alerts = evaluate_alerts([event("malicious_upload", TENANT_A)])
    assert alerts[0]["severity"] == "high" and alerts[0]["event_count"] == 1
    safe = sanitize_security_metadata({
        "question": "private", "filename": "private.pdf", "project_id": "raw-id",
        "stage": "scan", "latency_ms": "12.5", "blocked_count": 2,
    })
    encoded = json.dumps(safe)
    assert "private" not in encoded and "raw-id" not in encoded
    assert safe["stage"] == "scan" and safe["blocked_count"] == 2
    assert "project_id_fingerprint" in safe


def test_admin_api_boundary() -> None:
    snapshot = {
        "status": "implemented_local_only",
        "events": [], "alerts": [],
        "integrity": {"valid": True, "record_count": 0, "head_hash": "0" * 64},
        "taxonomy": [], "limitations": ["local only"],
    }
    client = TestClient(app)
    with patch("apps.api.app.main.security_snapshot", return_value=snapshot) as mocked:
        response = client.get("/security/monitoring", headers={"X-Demo-User-Id": ADMIN_USER})
        assert response.status_code == 200 and response.json()["integrity"]["valid"] is True
        assert mocked.call_args.kwargs["tenant_id"]
    denied = client.get("/security/monitoring", headers={"X-Demo-User-Id": EMPLOYEE_USER})
    assert denied.status_code == 403


def test_runbook_tabletop_contracts() -> None:
    required = {"Trigger", "Immediate containment", "Evidence", "Investigation", "Notification", "Recovery", "False positives", "Exit and retest"}
    runbooks = ROOT / "docs" / "phase-61" / "runbooks"
    paths = sorted(runbooks.glob("*.md"))
    assert len(paths) == 6
    for path in paths:
        content = path.read_text(encoding="utf-8")
        assert all(f"## {heading}" in content for heading in required), path
        assert "local tabletop" in content.lower()
        assert "unassigned" in content.lower()


def main() -> None:
    test_privacy_tenant_filter_alert_delivery_and_integrity()
    test_taxonomy_thresholds_and_metadata_allowlist()
    test_admin_api_boundary()
    test_runbook_tabletop_contracts()
    print("Phase 61 security monitoring and tabletop checks passed.")


if __name__ == "__main__":
    main()
