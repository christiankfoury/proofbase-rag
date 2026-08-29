from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from typing import Any
from urllib import request
from urllib.error import HTTPError, URLError

from apps.api.app.core.config import Settings, get_settings
from apps.api.app.privacy.redaction import sanitize_for_log

logger = logging.getLogger("proofbase.platform_telemetry")

TelemetrySender = Callable[[str, dict[str, Any], str, float], int]

SAFE_TOP_LEVEL_FIELDS = {
    "event_id",
    "external_request_id",
    "source_app",
    "operation_type",
    "environment",
    "occurred_at",
    "status",
    "provider",
    "model",
    "prompt_name",
    "prompt_version",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "estimated_cost_usd",
    "currency",
    "pricing_status",
    "latency_ms",
    "retrieval_latency_ms",
    "generation_latency_ms",
    "error_category",
    "error_message_redacted",
    "project_external_id",
    "department_external_id",
    "metadata",
}

SAFE_METADATA_FIELDS = {
    "retrieval_mode",
    "chunking_strategy",
    "top_k",
    "citation_count",
    "response_type",
    "streaming",
    "cache_hit",
    "document_count",
    "chunk_count",
    "embedding_count",
    "question_hash",
    "document_external_id",
    "session_external_id",
}

SENSITIVE_FIELD_PARTS = {
    "api_key",
    "authorization",
    "chunk_text",
    "citation_text",
    "cleaned_markdown",
    "content",
    "credential",
    "document_text",
    "extracted_markdown",
    "full_question",
    "markdown",
    "password",
    "prompt_text",
    "provider_payload",
    "raw",
    "rewritten_question",
    "secret",
}


def submit_platform_telemetry(
    event: Mapping[str, Any],
    *,
    settings: Settings | None = None,
    sender: TelemetrySender | None = None,
) -> bool:
    active_settings = settings or get_settings()
    if not active_settings.proofbase_telemetry_enabled:
        return False

    endpoint = active_settings.proofbase_telemetry_endpoint.strip()
    api_key = active_settings.proofbase_telemetry_api_key.strip()
    if not endpoint or not api_key:
        _log_failure("configuration_missing", event)
        return False

    payload = sanitize_telemetry_event(
        event,
        redact_content=active_settings.proofbase_telemetry_redact_content,
        max_metadata_bytes=active_settings.proofbase_telemetry_max_metadata_bytes,
    )
    try:
        status_code = (sender or _send_json)(
            endpoint,
            payload,
            api_key,
            max(0.1, active_settings.proofbase_telemetry_timeout_seconds),
        )
    except (TimeoutError, HTTPError, URLError, OSError) as exc:
        _log_failure(_failure_category(exc), event)
        return False
    except Exception:
        _log_failure("unexpected_error", event)
        return False

    if status_code < 200 or status_code >= 300:
        _log_failure(f"http_{status_code}", event)
        return False

    return True


def sanitize_telemetry_event(
    event: Mapping[str, Any],
    *,
    redact_content: bool,
    max_metadata_bytes: int,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in event.items():
        normalized_key = str(key)
        if normalized_key not in SAFE_TOP_LEVEL_FIELDS:
            continue
        if redact_content and _is_sensitive_key(normalized_key):
            continue
        if normalized_key == "metadata":
            payload["metadata"] = _sanitize_metadata(value, redact_content, max_metadata_bytes)
            continue
        payload[normalized_key] = _sanitize_value(value)

    payload.setdefault("source_app", "proofbase")
    return sanitize_for_log(payload)


def _send_json(endpoint: str, payload: dict[str, Any], api_key: str, timeout: float) -> int:
    body = json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")
    outbound = request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        method="POST",
    )
    with request.urlopen(outbound, timeout=timeout) as response:
        return int(response.status)


def _sanitize_metadata(value: Any, redact_content: bool, max_metadata_bytes: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}

    metadata: dict[str, Any] = {}
    byte_budget = max(0, max_metadata_bytes)
    for key, metadata_value in value.items():
        normalized_key = str(key).strip().lower()
        if normalized_key not in SAFE_METADATA_FIELDS:
            continue
        if redact_content and _is_sensitive_key(normalized_key):
            continue

        sanitized_value = _sanitize_value(metadata_value)
        candidate = {**metadata, normalized_key: sanitized_value}
        if len(json.dumps(candidate, default=str).encode("utf-8")) > byte_budget:
            break
        metadata[normalized_key] = sanitized_value

    return metadata


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value[:240]
    if isinstance(value, int | float | bool) or value is None:
        return value
    return str(value)[:240]


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_FIELD_PARTS)


def _failure_category(exc: BaseException) -> str:
    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, HTTPError):
        return f"http_{exc.code}"
    if isinstance(exc, URLError):
        return "network_error"
    return "transport_error"


def _log_failure(error_category: str, event: Mapping[str, Any]) -> None:
    logger.warning(
        "platform_telemetry_submission_failed error_category=%s operation_type=%s event_id=%s",
        error_category,
        str(event.get("operation_type", "unknown"))[:80],
        str(event.get("event_id", "unknown"))[:80],
        extra={
            "error_category": error_category,
            "source_app": "proofbase",
            "operation_type": str(event.get("operation_type", "unknown"))[:80],
            "event_id": str(event.get("event_id", "unknown"))[:80],
            "external_request_id": str(event.get("external_request_id", "unknown"))[:120],
        },
    )
