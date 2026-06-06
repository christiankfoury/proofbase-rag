from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.observability.logger import get_observability_log_path

OUTPUT_PATH = ROOT / "data" / "observability" / "summary.json"


def _safe_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _avg(values: list) -> float | None:
    real = [v for v in values if v is not None]
    return round(mean(real), 2) if real else None


def main() -> None:
    log_path = get_observability_log_path()
    if not log_path.exists():
        print(f"No log file at {log_path}. Run some queries via POST /query first.")
        return

    entries = []
    with log_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not entries:
        print("Log file is empty.")
        return

    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_requests": len(entries),
        "avg_total_latency_ms": _avg([_safe_float(e.get("total_latency_ms")) for e in entries]),
        "avg_retrieval_latency_ms": _avg([_safe_float(e.get("retrieval_latency_ms")) for e in entries]),
        "avg_generation_latency_ms": _avg([_safe_float(e.get("generation_latency_ms")) for e in entries]),
        "avg_final_confidence": _avg([_safe_float(e.get("final_confidence")) for e in entries]),
        "avg_input_tokens": _avg([_safe_float(e.get("input_tokens")) for e in entries]),
        "avg_output_tokens": _avg([_safe_float(e.get("output_tokens")) for e in entries]),
        "estimated_cost": None,
        "recent_requests": entries[-20:],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"Wrote summary for {len(entries)} request(s) to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
