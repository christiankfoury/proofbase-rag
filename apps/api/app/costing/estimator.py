from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

PRICING_PATH = Path(__file__).with_name("model_pricing.json")


@lru_cache
def load_model_pricing() -> dict[str, dict[str, Any]]:
    return json.loads(PRICING_PATH.read_text(encoding="utf-8"))


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return None


def estimate_chat_cost(
    *,
    model: str | None,
    input_tokens: int | str | None,
    output_tokens: int | str | None,
) -> dict[str, float | str | None]:
    safe_input_tokens = _safe_int(input_tokens)
    safe_output_tokens = _safe_int(output_tokens)
    if safe_input_tokens is None or safe_output_tokens is None:
        return {
            "input_cost_usd": None,
            "output_cost_usd": None,
            "estimated_cost_usd": None,
            "pricing_status": "missing_token_usage",
        }

    pricing = load_model_pricing()
    model_pricing = pricing.get(model or "")
    if not model_pricing:
        return {
            "input_cost_usd": None,
            "output_cost_usd": None,
            "estimated_cost_usd": None,
            "pricing_status": "missing_model_price",
        }

    input_cost = safe_input_tokens * float(model_pricing["input_usd_per_1m_tokens"]) / 1_000_000
    output_cost = safe_output_tokens * float(model_pricing["output_usd_per_1m_tokens"]) / 1_000_000
    return {
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "estimated_cost_usd": round(input_cost + output_cost, 6),
        "pricing_status": "estimated",
    }
