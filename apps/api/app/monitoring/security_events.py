from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

from apps.api.app.core.config import get_settings
from apps.api.app.privacy.redaction import bounded_reason_code, sanitize_for_log

ROOT = Path(__file__).resolve().parents[4]
GENESIS_HASH = "0" * 64
_lock = threading.Lock()


@dataclass(frozen=True)
class AlertRule:
    category: str
    severity: str
    threshold: int
    window_minutes: int
    owner: str


ALERT_RULES = (
    AlertRule("authentication_failure", "high", 5, 5, "security_on_call_unassigned"),
    AlertRule("authorization_denial", "medium", 10, 5, "security_on_call_unassigned"),
    AlertRule("cross_tenant_attempt", "critical", 1, 60, "security_on_call_unassigned"),
    AlertRule("injection_detection", "high", 3, 10, "ai_security_owner_unassigned"),
    AlertRule("evidence_validation_failure", "high", 3, 10, "ai_security_owner_unassigned"),
    AlertRule("rate_limit", "medium", 20, 5, "service_owner_unassigned"),
    AlertRule("malicious_upload", "high", 1, 60, "security_on_call_unassigned"),
    AlertRule("parser_failure", "medium", 3, 10, "service_owner_unassigned"),
    AlertRule("admin_change", "info", 1, 60, "service_owner_unassigned"),
    AlertRule("secret_config_failure", "critical", 1, 60, "security_on_call_unassigned"),
    AlertRule("unusual_cost", "high", 1, 60, "service_owner_unassigned"),
)

ADMIN_ACTIONS = {
    "project_created", "project_updated", "project_archived", "department_created",
    "department_updated", "department_archived", "project_membership_updated",
    "project_membership_removed", "tenant_access_revoked", "prompt_version_changed",
}

SAFE_METADATA_STRING_KEYS = {
    "stage", "retrieval_mode", "response_type", "operation", "limit_scope",
    "assessment_mode", "validator_action", "scanner_mode", "parser_mode",
}


class SecurityEventSink(Protocol):
    def emit(self, event: dict[str, Any]) -> bool: ...


class NotificationSink(Protocol):
    def deliver(self, alert: dict[str, Any]) -> bool: ...


def opaque_fingerprint(value: str | None) -> str:
    return hashlib.sha256(f"proofbase-security-v1:{value or 'unresolved'}".encode()).hexdigest()[:24]


def sanitize_security_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Keep operational signals while preventing content and raw identifiers from entering the sink."""
    cleaned: dict[str, Any] = {}
    for key, value in sanitize_for_log(metadata or {}).items():
        safe_key = str(key)[:80]
        if safe_key.endswith("_id") or safe_key.endswith("_ids"):
            cleaned[f"{safe_key}_fingerprint"] = opaque_fingerprint(str(value))
        elif isinstance(value, (bool, int, float)) or value is None:
            cleaned[safe_key] = value
        elif safe_key in SAFE_METADATA_STRING_KEYS:
            cleaned[safe_key] = str(value)[:80]
        elif safe_key.endswith("_hash") or safe_key.endswith("_fingerprint"):
            cleaned[safe_key] = str(value)[:128]
        elif safe_key.endswith("_count") or safe_key.endswith("_ms"):
            try:
                cleaned[safe_key] = float(value)
            except (TypeError, ValueError):
                continue
    return cleaned


def classify_audit_event(action: str, outcome: str, reason: str | None) -> str | None:
    if action in ADMIN_ACTIONS:
        return "admin_change"
    if action in {"project_access_denied", "unauthorized_candidate_blocked"}:
        return "authorization_denial"
    if action == "unauthorized_chunks_reached_generation":
        return "cross_tenant_attempt"
    if action == "user_prompt_override_blocked":
        return "injection_detection"
    if action in {
        "request_assessment_failed_safe", "evidence_assessment_failed_safe",
        "post_generation_validation_downgraded",
    }:
        return "evidence_validation_failure"
    if action == "rate_limit_denied":
        return "unusual_cost" if "budget" in str(reason or "") else "rate_limit"
    if action == "file_processing_rejected":
        return "malicious_upload" if reason == "known_test_signature" else "parser_failure"
    if action in {"identity_validation_failed", "http_authentication_failed"}:
        return "authentication_failure"
    if action == "cross_tenant_identity_attempt":
        return "cross_tenant_attempt"
    if action == "secret_configuration_failed":
        return "secret_config_failure"
    return None


def build_security_event(
    *,
    category: str,
    action: str,
    outcome: str,
    tenant_id: str | None,
    user_id: str | None = None,
    reason: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    occurred_at: datetime | None = None,
) -> dict[str, Any]:
    rule = next((item for item in ALERT_RULES if item.category == category), None)
    safe_metadata = sanitize_security_metadata(metadata)
    return {
        "schema_version": "security_event.v1",
        "event_id": str(uuid.uuid4()),
        "occurred_at": (occurred_at or datetime.now(UTC)).isoformat(),
        "category": category,
        "severity": rule.severity if rule else "info",
        "action": action[:120],
        "outcome": outcome[:40],
        "reason_code": bounded_reason_code(reason),
        "tenant_fingerprint": opaque_fingerprint(tenant_id),
        "user_fingerprint": opaque_fingerprint(user_id) if user_id else None,
        "correlation_fingerprint": opaque_fingerprint(correlation_id) if correlation_id else None,
        "metadata": safe_metadata,
    }


class LocalHashChainSecuritySink:
    """Local tamper-evident JSONL; not immutable storage or a live SIEM."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def emit(self, event: dict[str, Any]) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            previous_hash, sequence = self._tail()
            canonical_event = json.dumps(sanitize_for_log(event), sort_keys=True, separators=(",", ":"), default=str)
            record_hash = hashlib.sha256(f"{previous_hash}:{sequence}:{canonical_event}".encode()).hexdigest()
            record = {
                "sequence": sequence,
                "previous_hash": previous_hash,
                "record_hash": record_hash,
                "event": json.loads(canonical_event),
            }
            line = (json.dumps(record, separators=(",", ":")) + "\n").encode()
            descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(descriptor, "ab") as handle:
                handle.write(line)
            return True

    def _tail(self) -> tuple[str, int]:
        if not self.path.exists():
            return GENESIS_HASH, 1
        try:
            lines = [line for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
            tail = json.loads(lines[-1]) if lines else None
            return (str(tail["record_hash"]), int(tail["sequence"]) + 1) if tail else (GENESIS_HASH, 1)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("security_event_chain_unreadable") from exc

    def verify(self) -> dict[str, Any]:
        previous_hash = GENESIS_HASH
        count = 0
        if not self.path.exists():
            return {"valid": True, "record_count": 0, "head_hash": previous_hash}
        try:
            for raw_line in self.path.read_text(encoding="utf-8").splitlines():
                if not raw_line.strip():
                    continue
                record = json.loads(raw_line)
                count += 1
                event_json = json.dumps(record["event"], sort_keys=True, separators=(",", ":"), default=str)
                expected = hashlib.sha256(f"{previous_hash}:{count}:{event_json}".encode()).hexdigest()
                if record.get("sequence") != count or record.get("previous_hash") != previous_hash or record.get("record_hash") != expected:
                    return {"valid": False, "record_count": count, "head_hash": previous_hash}
                previous_hash = expected
        except (OSError, KeyError, TypeError, json.JSONDecodeError):
            return {"valid": False, "record_count": count, "head_hash": previous_hash}
        return {"valid": True, "record_count": count, "head_hash": previous_hash}

    def read_events(self, *, tenant_id: str, limit: int = 100) -> list[dict[str, Any]]:
        if not self.verify()["valid"] or not self.path.exists():
            return []
        tenant_fingerprint = opaque_fingerprint(tenant_id)
        events = []
        for raw_line in self.path.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            event = json.loads(raw_line)["event"]
            if event.get("tenant_fingerprint") == tenant_fingerprint:
                events.append(event)
        return events[-max(1, min(limit, 500)):]


class LocalJsonlNotificationSink:
    def __init__(self, path: Path) -> None:
        self.path = path

    def deliver(self, alert: dict[str, Any]) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = (json.dumps(sanitize_for_log(alert), separators=(",", ":"), default=str) + "\n").encode()
        with _lock:
            descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(descriptor, "ab") as handle:
                handle.write(line)
        return True


class SecurityMonitor:
    def __init__(self, event_sink: LocalHashChainSecuritySink, notification_sink: NotificationSink) -> None:
        self.event_sink = event_sink
        self.notification_sink = notification_sink
        self._delivered: set[str] = set()

    def emit(self, event: dict[str, Any], *, tenant_id: str) -> bool:
        if not self.event_sink.emit(event):
            return False
        for alert in evaluate_alerts(self.event_sink.read_events(tenant_id=tenant_id, limit=500)):
            key = f"{alert['rule_id']}:{alert['tenant_fingerprint']}:{alert['window_end'][:16]}"
            if key not in self._delivered and self.notification_sink.deliver(alert):
                self._delivered.add(key)
        return True


def evaluate_alerts(events: list[dict[str, Any]], *, now: datetime | None = None) -> list[dict[str, Any]]:
    current = now or datetime.now(UTC)
    alerts: list[dict[str, Any]] = []
    for rule in ALERT_RULES:
        cutoff = current - timedelta(minutes=rule.window_minutes)
        matching = [
            event for event in events
            if event.get("category") == rule.category
            and _parse_time(event.get("occurred_at")) >= cutoff
        ]
        if len(matching) >= rule.threshold:
            tenant = matching[-1]["tenant_fingerprint"]
            alerts.append({
                "schema_version": "security_alert.v1",
                "alert_id": str(uuid.uuid4()),
                "rule_id": f"{rule.category}:{rule.threshold}:{rule.window_minutes}",
                "category": rule.category,
                "severity": rule.severity,
                "owner": rule.owner,
                "tenant_fingerprint": tenant,
                "event_count": len(matching),
                "window_minutes": rule.window_minutes,
                "window_end": current.isoformat(),
                "notification_status": "local_delivery_only",
            })
    return alerts


def _parse_time(value: Any) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return datetime.min.replace(tzinfo=UTC)


def emit_security_event(**kwargs: Any) -> bool:
    tenant_id = str(kwargs.get("tenant_id") or "unresolved")
    event = build_security_event(**kwargs)
    try:
        return get_security_monitor().emit(event, tenant_id=tenant_id)
    except Exception:
        return False


def emit_audit_security_event(*, action: str, outcome: str, reason: str | None, tenant_id: str | None, user_id: str | None, metadata: dict[str, Any] | None) -> bool:
    category = classify_audit_event(action, outcome, reason)
    if not category:
        return False
    return emit_security_event(
        category=category,
        action=action,
        outcome=outcome,
        reason=reason,
        tenant_id=tenant_id,
        user_id=user_id,
        correlation_id=str((metadata or {}).get("request_id") or "") or None,
        metadata=metadata,
    )


def security_snapshot(*, tenant_id: str, limit: int = 100) -> dict[str, Any]:
    monitor = get_security_monitor()
    events = monitor.event_sink.read_events(tenant_id=tenant_id, limit=limit)
    integrity = monitor.event_sink.verify()
    return {
        "status": "implemented_local_only",
        "events": list(reversed(events)),
        "alerts": evaluate_alerts(events),
        "integrity": integrity,
        "taxonomy": [
            {
                "category": rule.category,
                "severity": rule.severity,
                "threshold": rule.threshold,
                "window_minutes": rule.window_minutes,
                "owner": rule.owner,
            }
            for rule in ALERT_RULES
        ],
        "limitations": [
            "Local JSONL delivery is not a live SIEM, pager, or immutable external audit store.",
            "Monitoring destination, named on-call owner, escalation policy, and notification channel require an external integration decision.",
        ],
    }


def _configured_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


@lru_cache
def get_security_monitor() -> SecurityMonitor:
    settings = get_settings()
    if settings.security_event_sink_mode != "local_jsonl":
        raise RuntimeError("external_security_sink_not_connected")
    return SecurityMonitor(
        LocalHashChainSecuritySink(_configured_path(settings.security_event_log_path)),
        LocalJsonlNotificationSink(_configured_path(settings.security_notification_log_path)),
    )
