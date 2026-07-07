from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from apps.api.app.observability.platform_telemetry import TelemetrySender, submit_platform_telemetry

PLATFORM_PRICING_STATUSES = {"estimated", "unpriced", "cached", "unknown"}


def submit_auxiliary_telemetry(
    *,
    operation_type: str,
    model: str,
    status: str = "succeeded",
    provider: str | None = None,
    prompt_name: str | None = None,
    prompt_version: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    estimated_cost_usd: Any | None = None,
    pricing_status: str | None = None,
    latency_ms: int | None = None,
    project_external_id: str | None = None,
    department_external_id: str | None = None,
    document_external_id: str | None = None,
    question: str | None = None,
    metadata: dict[str, Any] | None = None,
    external_request_id: str | None = None,
    error_category: str | None = None,
    error_message_redacted: str | None = None,
    sender: TelemetrySender | None = None,
) -> bool:
    event = build_auxiliary_telemetry_event(
        operation_type=operation_type,
        model=model,
        status=status,
        provider=provider,
        prompt_name=prompt_name,
        prompt_version=prompt_version,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=estimated_cost_usd,
        pricing_status=pricing_status,
        latency_ms=latency_ms,
        project_external_id=project_external_id,
        department_external_id=department_external_id,
        document_external_id=document_external_id,
        question=question,
        metadata=metadata,
        external_request_id=external_request_id,
        error_category=error_category,
        error_message_redacted=error_message_redacted,
    )
    return submit_platform_telemetry(event, sender=sender)


def build_auxiliary_telemetry_event(
    *,
    operation_type: str,
    model: str,
    status: str = "succeeded",
    provider: str | None = None,
    prompt_name: str | None = None,
    prompt_version: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    estimated_cost_usd: Any | None = None,
    pricing_status: str | None = None,
    latency_ms: int | None = None,
    project_external_id: str | None = None,
    department_external_id: str | None = None,
    document_external_id: str | None = None,
    question: str | None = None,
    metadata: dict[str, Any] | None = None,
    external_request_id: str | None = None,
    error_category: str | None = None,
    error_message_redacted: str | None = None,
) -> dict[str, Any]:
    event_id = f"evt_proofbase_{operation_type}_{uuid4().hex}"
    request_id = external_request_id or f"proofbase_aux_{uuid4().hex}"
    safe_metadata = dict(metadata or {})
    if document_external_id:
        safe_metadata["document_external_id"] = document_external_id
    if question:
        safe_metadata["question_hash"] = hashlib.sha256(question.encode("utf-8")).hexdigest()[:32]

    event: dict[str, Any] = {
        "event_id": event_id,
        "external_request_id": request_id,
        "source_app": "proofbase",
        "operation_type": operation_type,
        "environment": "local",
        "occurred_at": datetime.now(UTC).isoformat(),
        "status": status,
        "provider": provider or _provider_for_model(model),
        "model": model or "unknown",
        "prompt_name": prompt_name,
        "prompt_version": prompt_version,
        "currency": "USD",
        "pricing_status": normalize_pricing_status(pricing_status),
        "latency_ms": latency_ms,
        "project_external_id": project_external_id,
        "department_external_id": department_external_id,
        "metadata": {key: value for key, value in safe_metadata.items() if value not in (None, "")},
    }
    _set_optional(event, "input_tokens", input_tokens)
    _set_optional(event, "output_tokens", output_tokens)
    if input_tokens is not None and output_tokens is not None:
        event["total_tokens"] = input_tokens + output_tokens
    _set_optional(event, "estimated_cost_usd", _decimal_string(estimated_cost_usd))
    _set_optional(event, "error_category", error_category)
    _set_optional(event, "error_message_redacted", error_message_redacted)
    return {key: value for key, value in event.items() if value not in (None, "", {})}


def normalize_pricing_status(status: str | None) -> str:
    if not status:
        return "unknown"
    normalized = status.strip().lower()
    if normalized in PLATFORM_PRICING_STATUSES:
        return normalized
    if normalized == "missing_model_price":
        return "unpriced"
    if normalized == "missing_token_usage":
        return "unknown"
    return "unknown"


def _provider_for_model(model: str) -> str:
    if model.startswith("mock"):
        return "mock"
    if model == "unknown":
        return "unknown"
    return "openai"


def _decimal_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _set_optional(event: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        event[key] = value
