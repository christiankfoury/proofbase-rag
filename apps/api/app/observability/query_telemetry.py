from __future__ import annotations

import hashlib
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from psycopg import Error as PsycopgError

from apps.api.app.observability.platform_telemetry import TelemetrySender, submit_platform_telemetry


def submit_query_telemetry(
    *,
    request_id: str,
    request: Any,
    operation_type: str,
    status: str,
    config: Any | None = None,
    answer: dict[str, Any] | None = None,
    trace: Any | None = None,
    chunks: Iterable[Any] | None = None,
    error_category: str | None = None,
    error_message_redacted: str | None = None,
    settings: Any | None = None,
    sender: TelemetrySender | None = None,
) -> bool:
    event = build_query_telemetry_event(
        request_id=request_id,
        request=request,
        operation_type=operation_type,
        status=status,
        config=config,
        answer=answer,
        trace=trace,
        chunks=chunks,
        error_category=error_category,
        error_message_redacted=error_message_redacted,
    )
    return submit_platform_telemetry(event, settings=settings, sender=sender)


def build_query_telemetry_event(
    *,
    request_id: str,
    request: Any,
    operation_type: str,
    status: str,
    config: Any | None = None,
    answer: dict[str, Any] | None = None,
    trace: Any | None = None,
    chunks: Iterable[Any] | None = None,
    error_category: str | None = None,
    error_message_redacted: str | None = None,
) -> dict[str, Any]:
    answer = answer or {}
    model = str(answer.get("model") or "unknown")
    input_tokens = _safe_int(answer.get("input_tokens"))
    output_tokens = _safe_int(answer.get("output_tokens"))
    total_tokens = (
        input_tokens + output_tokens
        if input_tokens is not None and output_tokens is not None
        else None
    )
    chunk_list = list(chunks or [])
    project_id = _field(config, "project_id") or _field(request, "project_id")
    department_id = _field(config, "department_id") or _field(request, "department_id")

    event: dict[str, Any] = {
        "event_id": f"evt_proofbase_{operation_type}_{request_id.replace('-', '')}",
        "external_request_id": request_id,
        "source_app": "proofbase",
        "operation_type": operation_type,
        "environment": "local",
        "occurred_at": datetime.now(UTC).isoformat(),
        "status": status,
        "provider": _provider_for_model(model),
        "model": model,
        "prompt_name": str(
            answer.get("prompt_name") or _field(request, "prompt_name") or "answer_generation"
        ),
        "prompt_version": str(
            answer.get("prompt_version") or _field(request, "prompt_version") or "unknown"
        ),
        "currency": "USD",
        "pricing_status": str(answer.get("pricing_status") or "unknown"),
        "latency_ms": _safe_int(_field(trace, "total_latency_ms")),
        "retrieval_latency_ms": _safe_int(_field(trace, "retrieval_latency_ms")),
        "generation_latency_ms": _safe_int(_field(trace, "generation_latency_ms")),
        "project_external_id": _optional_str(project_id),
        "department_external_id": _optional_str(department_id),
        "metadata": {
            "retrieval_mode": _field(config, "retrieval_mode") or _field(request, "retrieval_mode"),
            "chunking_strategy": _field(config, "chunking_strategy")
            or _field(request, "chunking_strategy"),
            "top_k": _safe_int(_field(config, "top_k") or _field(request, "top_k")),
            "citation_count": len(answer.get("citations") or []),
            "response_type": answer.get("response_type"),
            "streaming": operation_type == "rag_query_stream",
            "document_count": len(
                {
                    str(_field(chunk, "document_id"))
                    for chunk in chunk_list
                    if _field(chunk, "document_id")
                }
            ),
            "chunk_count": len(chunk_list),
            "question_hash": _question_hash(_field(request, "question")),
            "session_external_id": _field(request, "session_id"),
        },
    }
    _set_optional(event, "input_tokens", input_tokens)
    _set_optional(event, "output_tokens", output_tokens)
    _set_optional(event, "total_tokens", total_tokens)
    _set_optional(event, "estimated_cost_usd", _decimal_string(answer.get("estimated_cost_usd")))
    _set_optional(event, "error_category", error_category)
    _set_optional(event, "error_message_redacted", error_message_redacted)
    event["metadata"] = {
        key: value for key, value in event["metadata"].items() if value not in (None, "")
    }
    return {key: value for key, value in event.items() if value not in (None, "")}


def query_error_category(exc: BaseException) -> str:
    if isinstance(exc, HTTPException):
        return f"http_{exc.status_code}"
    if isinstance(exc, PsycopgError):
        return "database_unavailable"
    if isinstance(exc, ValueError):
        return "validation_error"
    if isinstance(exc, RuntimeError):
        return "generation_error"
    return "unknown"


def redacted_error_message(exc: BaseException) -> str:
    if isinstance(exc, HTTPException):
        return f"HTTP {exc.status_code}"
    if isinstance(exc, PsycopgError):
        return "Database unavailable"
    if isinstance(exc, ValueError):
        return "Invalid query request"
    if isinstance(exc, RuntimeError):
        return "Generation failed"
    return "Query failed"


def _field(source: Any, name: str) -> Any:
    if source is None:
        return None
    if isinstance(source, dict):
        return source.get(name)
    return getattr(source, name, None)


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _decimal_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _set_optional(event: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        event[key] = value


def _provider_for_model(model: str) -> str:
    if model.startswith("mock"):
        return "mock"
    if model == "unknown":
        return "unknown"
    return "openai"


def _question_hash(question: Any) -> str | None:
    if not question:
        return None
    return hashlib.sha256(str(question).encode("utf-8")).hexdigest()[:32]
