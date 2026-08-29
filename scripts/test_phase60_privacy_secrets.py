from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.audit.audit_logger import log_audit_event
from apps.api.app.core.config import Settings
from apps.api.app.main import app
from apps.api.app.observability.logger import build_request_entry, log_request
from apps.api.app.observability.platform_telemetry import sanitize_telemetry_event
from apps.api.app.privacy.redaction import REDACTED, sanitize_for_log
from apps.api.app.privacy.retention import purge_jsonl
from apps.api.app.secrets.provider import MountedFileSecretProvider, SecretProviderError
from scripts.scan_phase60_secrets import scan_path

ADMIN_USER = "00000000-0000-0000-0000-000000002706"
EMPLOYEE_USER = "00000000-0000-0000-0000-000000002701"


def test_recursive_redaction_and_audit_boundary() -> None:
    api_key = "sk-" + "Phase60FakeKeyMaterial1234567890"
    bearer = "Bearer " + "header.payload.signature"
    email = "alex.phase60@example.invalid"
    database_url = "postgresql://" + "person:StrongCredential@db.example/proofbase"
    question = "What is Alex's private compensation?"
    payload = {
        "authorization": bearer,
        "cookie": "session=phase60-private",
        "api_key": api_key,
        "database": database_url,
        "question": question,
        "nested": {"source_content": "Private source body", "contact": email, "count": 4},
        "request_id": "request-safe-id",
    }
    sanitized = sanitize_for_log(payload)
    encoded = json.dumps(sanitized)
    for secret in (api_key, bearer, email, database_url, question, "Private source body"):
        assert secret not in encoded
    assert sanitized["authorization"] == REDACTED
    assert sanitized["request_id"] == "request-safe-id"
    assert sanitized["nested"]["count"] == 4

    captured: dict[str, object] = {}

    class FakeConnection:
        def execute(self, _sql, params):
            captured["params"] = params

    @contextmanager
    def fake_connection():
        yield FakeConnection()

    with patch("apps.api.app.audit.audit_logger.get_connection", fake_connection):
        assert log_audit_event(
            action="phase60_test",
            user_role="Admin",
            user_id=ADMIN_USER,
            outcome="failed",
            reason=f"Provider exposed {api_key}",
            metadata={"question": question, "project_name": "Private project", "request_id": "safe-id"},
        )
    params = captured["params"]
    assert isinstance(params, tuple)
    audit_json = str(params[-1])
    assert question not in audit_json and "Private project" not in audit_json and api_key not in str(params)
    assert str(params[-2]).startswith("redacted_reason:")


def _request_entry(question: str, rewritten: str, error: str | None = None) -> dict:
    return build_request_entry(
        request_id="phase60-request",
        timestamp=datetime.now(UTC).isoformat(),
        tenant_id="00000000-0000-0000-0000-000000002801",
        user_role="Employee",
        session_id=None,
        question_truncated=question,
        rewritten_question=rewritten,
        retrieval_mode="hybrid",
        chunking_strategy="section_based",
        top_k=5,
        project_id=None,
        department_id=None,
        retrieved_chunk_ids=[],
        retrieved_document_ids=[],
        response_type="answer",
        citation_count=0,
        final_confidence=0.5,
        retrieval_latency_ms=1,
        generation_latency_ms=2,
        total_latency_ms=3,
        prompt_version="v8",
        model="mock-model",
        input_tokens=10,
        output_tokens=5,
        input_cost_usd=0.0,
        output_cost_usd=0.0,
        estimated_cost_usd=0.0,
        pricing_status="estimated",
        error=error,
    )


def test_privacy_safe_request_logs_and_telemetry() -> None:
    question = "Phase 60 private prompt for Alex"
    rewritten = "Phase 60 private rewritten prompt"
    api_key = "sk-" + "AnotherFakePhase60Key123456789"
    entry = _request_entry(question, rewritten, error=f"Bearer abc.def.ghi {api_key} alex@example.invalid")
    assert "question" not in entry and "rewritten_question" not in entry
    assert entry["question_hash"] and entry["rewritten_question_hash"]

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "requests.jsonl"
        with patch("apps.api.app.observability.logger.get_observability_log_path", return_value=path):
            log_request(entry)
        stored = path.read_text(encoding="utf-8")
        for value in (question, rewritten, api_key, "abc.def.ghi", "alex@example.invalid"):
            assert value not in stored
        if os.name != "nt":
            assert stat.S_IMODE(path.stat().st_mode) == 0o600

    telemetry = sanitize_telemetry_event(
        {
            "event_id": "safe-event",
            "operation_type": f"query {api_key}",
            "error_message_redacted": "Contact alex@example.invalid with password=hunter2",
            "metadata": {"question_hash": "abc123", "content": question},
        },
        redact_content=True,
        max_metadata_bytes=2048,
    )
    encoded = json.dumps(telemetry)
    assert api_key not in encoded and "alex@example.invalid" not in encoded and "hunter2" not in encoded
    assert telemetry["metadata"]["question_hash"] == "abc123"


def test_secret_provider_rotation_revocation_and_production_guards() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        secret_path = root / "openai_api_key"
        first = "sk-" + "A" * 40
        second = "sk-" + "B" * 40
        secret_path.write_text(first, encoding="utf-8")
        (root / "file_access_signing_secret").write_text("S" * 64, encoding="utf-8")
        provider = MountedFileSecretProvider(root)
        assert provider.get("openai_api_key") == first
        secret_path.write_text(second, encoding="utf-8")
        assert provider.get("openai_api_key") == second

        mounted = Settings(
            _env_file=None,
            app_environment="development",
            auth_mode="oidc",
            database_url="postgresql://" + "proofbase_runtime:StrongDatabaseCredential123@db/proofbase",
            database_enforce_rls=True,
            rate_limit_backend="redis",
            redis_url="rediss://" + "default:StrongRedisCredential123@redis:6380/0",
            file_parser_mode="isolated_worker",
            file_scanner_mode="hosted",
            secret_provider_mode="mounted_files",
            secret_mount_dir=str(root),
        )
        assert mounted.openai_api_key == second
        assert second not in repr(mounted) and "S" * 64 not in repr(mounted)

        production_values = mounted.model_dump()
        production_values.update({
            "_env_file": None,
            "app_environment": "production",
            "security_event_sink_mode": "external",
            "secret_provider_mode": "mounted_files",
            "secret_mount_dir": str(root),
        })
        try:
            Settings(**production_values)
        except ValueError as exc:
            assert "no destination adapter" in str(exc)
            assert second not in str(exc)
        else:
            raise AssertionError("Production claimed an unconnected security-event destination")

        secret_path.unlink()
        assert provider.get("openai_api_key") is None
        try:
            provider.get("../escape")
        except SecretProviderError as exc:
            assert str(exc) == "invalid_secret_name"
        else:
            raise AssertionError("Traversal secret name was accepted")

        common = mounted.model_dump()
        common["app_environment"] = "production"
        common["security_event_sink_mode"] = "external"
        common.update({"_env_file": None, "openai_api_key": second, "file_access_signing_secret": "S" * 64})
        common.pop("secret_provider_mode", None)
        common.pop("secret_mount_dir", None)
        try:
            Settings(**common, secret_provider_mode="environment")
        except ValueError as exc:
            assert "environment-only" in str(exc)
            assert second not in str(exc) and "StrongDatabaseCredential123" not in str(exc)
        else:
            raise AssertionError("Production accepted environment-only secrets")
        try:
            Settings(**common, secret_provider_mode="managed")
        except ValueError as exc:
            assert "no adapter" in str(exc)
        else:
            raise AssertionError("Production claimed an unconnected managed provider")

        try:
            Settings(
                **common,
                secret_provider_mode="mounted_files",
                secret_mount_dir=str(root),
            )
        except ValueError as exc:
            assert "OpenAI credential" in str(exc)
            assert second not in str(exc)
        else:
            raise AssertionError("Production fell back to an environment secret when the mounted file was revoked")


def test_retention_hold_and_role_access() -> None:
    now = datetime(2026, 8, 28, tzinfo=UTC)
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "retention.jsonl"
        rows = [
            {"timestamp": (now - timedelta(days=31)).isoformat(), "request_id": "old"},
            {"timestamp": now.isoformat(), "request_id": "new"},
        ]
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\ninvalid-evidence\n", encoding="utf-8")
        held = purge_jsonl(path, timestamp_field="timestamp", retention_days=30, now=now, incident_hold=True)
        assert held["deleted"] == 0 and "old" in path.read_text(encoding="utf-8")
        result = purge_jsonl(path, timestamp_field="timestamp", retention_days=30, now=now)
        stored = path.read_text(encoding="utf-8")
        assert result == {"scanned": 3, "retained": 2, "deleted": 1, "incident_hold": False}
        assert '"old"' not in stored and '"new"' in stored and "invalid-evidence" in stored

    client = TestClient(app)
    denied = client.get("/observability/summary", headers={"X-Demo-User-Id": EMPLOYEE_USER})
    assert denied.status_code == 403
    allowed = client.get("/observability/summary", headers={"X-Demo-User-Id": ADMIN_USER})
    assert allowed.status_code == 200


def test_request_validation_and_repository_scan() -> None:
    sensitive_input = "phase60-private-validation-input"
    response = TestClient(app).post(
        "/query",
        headers={"X-Demo-User-Id": EMPLOYEE_USER},
        json={"question": sensitive_input + "x" * 4_100},
    )
    assert response.status_code == 422
    assert sensitive_input not in response.text
    assert "input" not in response.text.lower()
    assert scan_path(ROOT) == []


def main() -> None:
    test_recursive_redaction_and_audit_boundary()
    test_privacy_safe_request_logs_and_telemetry()
    test_secret_provider_rotation_revocation_and_production_guards()
    test_retention_hold_and_role_access()
    test_request_validation_and_repository_scan()
    print("Phase 60 privacy and secret-control checks passed.")


if __name__ == "__main__":
    main()
