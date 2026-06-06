from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.costing.estimator import estimate_chat_cost

PROMPT_EXPERIMENT_DIR = ROOT / "data/evaluation/prompt-experiments"
MULTI_DOC_EVAL_PATH = ROOT / "data/evaluation/multi-doc-eval.json"
DASHBOARD_PATH = ROOT / "data/evaluation/dashboard-summary.json"


def _estimate(model: str | None, input_tokens: Any, output_tokens: Any) -> dict[str, Any]:
    return estimate_chat_cost(model=model, input_tokens=input_tokens, output_tokens=output_tokens)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _backfill_prompt_experiments() -> int:
    count = 0
    if not PROMPT_EXPERIMENT_DIR.exists():
        return count
    for path in sorted(PROMPT_EXPERIMENT_DIR.glob("phase11-answer-generation-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        summary = payload.get("summary", {})
        cost = _estimate(summary.get("model"), summary.get("input_tokens"), summary.get("output_tokens"))
        summary["estimated_cost"] = cost["estimated_cost_usd"]
        summary["pricing_status"] = cost["pricing_status"]
        for row in payload.get("rows", []):
            row_model = row.get("model") or summary.get("model")
            row_cost = _estimate(row_model, row.get("input_tokens"), row.get("output_tokens"))
            row.update(row_cost)
        _write_json(path, payload)
        count += 1
    return count


def _backfill_multi_doc() -> bool:
    if not MULTI_DOC_EVAL_PATH.exists():
        return False
    payload = json.loads(MULTI_DOC_EVAL_PATH.read_text(encoding="utf-8"))
    changed = False
    for section in ("baseline", "multi_doc"):
        rows = payload.get(section, {}).get("rows", [])
        for row in rows:
            if row.get("input_tokens") is None or row.get("output_tokens") is None:
                continue
            cost = _estimate("gpt-4.1-mini", row.get("input_tokens"), row.get("output_tokens"))
            row.update(cost)
            changed = True
        costs = [row.get("estimated_cost_usd") for row in rows if row.get("estimated_cost_usd") is not None]
        if costs:
            payload[section].setdefault("summary", {})["estimated_cost"] = round(sum(costs), 6)
            changed = True
    if changed:
        _write_json(MULTI_DOC_EVAL_PATH, payload)
    return changed


def _backfill_dashboard() -> bool:
    if not DASHBOARD_PATH.exists():
        return False
    payload = json.loads(DASHBOARD_PATH.read_text(encoding="utf-8"))
    changed = False
    for run in payload.get("runs", []):
        metrics = run.get("metrics", {})
        if metrics.get("estimated_cost") is not None:
            continue
        cost = _estimate(run.get("model"), metrics.get("input_tokens"), metrics.get("output_tokens"))
        if cost["estimated_cost_usd"] is not None:
            metrics["estimated_cost"] = cost["estimated_cost_usd"]
            changed = True
    if changed:
        payload["notes"] = [
            note.replace(
                "Estimated cost is pending because pricing is not hardcoded.",
                "Estimated cost is calculated from configured chat model pricing where token counts are available.",
            )
            for note in payload.get("notes", [])
        ]
        _write_json(DASHBOARD_PATH, payload)
    return changed


def main() -> None:
    result = {
        "prompt_experiment_files": _backfill_prompt_experiments(),
        "multi_doc_updated": _backfill_multi_doc(),
        "dashboard_updated": _backfill_dashboard(),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
