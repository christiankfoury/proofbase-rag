from __future__ import annotations

import json
from datetime import UTC, datetime
from statistics import mean
from typing import Any

from apps.api.app.observability.logger import LOG_PATH


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _avg(values: list) -> float | None:
    real = [v for v in values if v is not None]
    return round(mean(real), 2) if real else None


def compute_live_summary(limit: int = 20) -> dict[str, Any]:
    if not LOG_PATH.exists():
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
            "recent_requests": [],
        }

    entries: list[dict] = []
    try:
        with LOG_PATH.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
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
            "recent_requests": [],
        }

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_requests": len(entries),
        "avg_total_latency_ms": _avg([_safe_float(e.get("total_latency_ms")) for e in entries]),
        "avg_retrieval_latency_ms": _avg([_safe_float(e.get("retrieval_latency_ms")) for e in entries]),
        "avg_generation_latency_ms": _avg([_safe_float(e.get("generation_latency_ms")) for e in entries]),
        "avg_final_confidence": _avg([_safe_float(e.get("final_confidence")) for e in entries]),
        "avg_input_tokens": _avg([_safe_float(e.get("input_tokens")) for e in entries]),
        "avg_output_tokens": _avg([_safe_float(e.get("output_tokens")) for e in entries]),
        "estimated_cost": None,
        "recent_requests": entries[-limit:],
    }
