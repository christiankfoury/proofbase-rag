from __future__ import annotations

import json
from datetime import UTC, datetime
from statistics import mean
from typing import Any

from apps.api.app.costing.estimator import estimate_chat_cost
from apps.api.app.observability.logger import get_observability_log_path
from apps.api.app.auth.tenant_context import current_tenant_id
from apps.api.app.privacy.redaction import sanitize_for_log


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _avg(values: list) -> float | None:
    real = [v for v in values if v is not None]
    return round(mean(real), 2) if real else None


def _sum_cost(values: list) -> float | None:
    real = [v for v in values if v is not None]
    return round(sum(real), 6) if real else None


def _avg_cost(values: list) -> float | None:
    real = [v for v in values if v is not None]
    return round(mean(real), 6) if real else None


def _entry_cost(entry: dict) -> float | None:
    explicit = _safe_float(entry.get("estimated_cost_usd", entry.get("estimated_cost")))
    if explicit is not None:
        return explicit
    return estimate_chat_cost(
        model=entry.get("model"),
        input_tokens=entry.get("input_tokens"),
        output_tokens=entry.get("output_tokens"),
    )["estimated_cost_usd"]


def compute_live_summary(limit: int = 20) -> dict[str, Any]:
    tenant_id = current_tenant_id()
    log_path = get_observability_log_path()
    if not log_path.exists():
        return {
            "status": "not_generated",
            "message": "No request logs yet. Send queries via POST /query first.",
            "total_requests": None,
            "avg_total_latency_ms": None,
            "avg_retrieval_latency_ms": None,
            "avg_generation_latency_ms": None,
            "avg_final_confidence": None,
            "avg_input_tokens": None,
            "avg_output_tokens": None,
            "estimated_cost": None,
            "total_estimated_cost_usd": None,
            "avg_estimated_cost_usd": None,
            "recent_requests": [],
        }

    entries: list[dict] = []
    try:
        with log_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        entry = sanitize_for_log(json.loads(line))
                        if entry.get("tenant_id") == tenant_id:
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue
    except OSError:
        return {
            "status": "error",
            "message": "Could not read request log file.",
            "total_requests": None,
            "avg_total_latency_ms": None,
            "avg_retrieval_latency_ms": None,
            "avg_generation_latency_ms": None,
            "avg_final_confidence": None,
            "avg_input_tokens": None,
            "avg_output_tokens": None,
            "estimated_cost": None,
            "total_estimated_cost_usd": None,
            "avg_estimated_cost_usd": None,
            "recent_requests": [],
        }

    for entry in entries:
        if entry.get("estimated_cost_usd") is None:
            cost = estimate_chat_cost(
                model=entry.get("model"),
                input_tokens=entry.get("input_tokens"),
                output_tokens=entry.get("output_tokens"),
            )
            entry.setdefault("input_cost_usd", cost["input_cost_usd"])
            entry.setdefault("output_cost_usd", cost["output_cost_usd"])
            entry["estimated_cost_usd"] = cost["estimated_cost_usd"]
            entry.setdefault("pricing_status", cost["pricing_status"])
    cost_values = [_entry_cost(e) for e in entries]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_requests": len(entries),
        "avg_total_latency_ms": _avg([_safe_float(e.get("total_latency_ms")) for e in entries]),
        "avg_retrieval_latency_ms": _avg([_safe_float(e.get("retrieval_latency_ms")) for e in entries]),
        "avg_generation_latency_ms": _avg([_safe_float(e.get("generation_latency_ms")) for e in entries]),
        "avg_final_confidence": _avg([_safe_float(e.get("final_confidence")) for e in entries]),
        "avg_input_tokens": _avg([_safe_float(e.get("input_tokens")) for e in entries]),
        "avg_output_tokens": _avg([_safe_float(e.get("output_tokens")) for e in entries]),
        "estimated_cost": _sum_cost(cost_values),
        "total_estimated_cost_usd": _sum_cost(cost_values),
        "avg_estimated_cost_usd": _avg_cost(cost_values),
        "recent_requests": entries[-limit:],
    }
