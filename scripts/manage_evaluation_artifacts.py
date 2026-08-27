from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "data/evaluation/raw-artifact-index.json"
HISTORICAL_COMMIT = "9a22a02"

RETIRED_RAW_ARTIFACTS = {
    "data/evaluation/expanded-baseline/phase52-request-assessment-regression.json": {
        "bytes": 1057562,
        "sha256": "5b3e29eee9c747c5cbee103cbf1bc7d61ed10bb57e69586054fe50a35667e946",
        "row_count": 130,
    },
    "data/evaluation/expanded-baseline/phase52-request-assessment-final-regression.json": {
        "bytes": 1336426,
        "sha256": "fa6c3101a7f7718a598b4f86e0d6393a874771bd671ef42d6768d292104b93d7",
        "row_count": 130,
    },
    "data/evaluation/expanded-baseline/phase52-request-assessment-final-subset.json": {
        "bytes": 22037,
        "sha256": "be98e43d3b56cc8d4954716b077f51b5e975afdce8f765dbeba05829dcb81443",
        "row_count": 2,
    },
    "data/evaluation/expanded-baseline/phase53-live-query-regression-v2.json": {
        "bytes": 1530905,
        "sha256": "44c48796a6ec5969a1687c4650a06e8899e1567b64a52e89f4c52acaa2b67818",
        "row_count": 130,
    },
    "data/evaluation/expanded-baseline/phase53-live-query-regression-v5.json": {
        "bytes": 1550487,
        "sha256": "5d702242910156924aec1c5852240fe2a277090ef4836ad09a50162b66763672",
        "row_count": 130,
    },
    "data/evaluation/expanded-baseline/phase54-live-query-regression-v5.json": {
        "bytes": 1771412,
        "sha256": "b0709dbdcb0673dba01e6de4173332e11411a379d332ffb38fcb5f980e33ad53",
        "row_count": 130,
    },
    "data/evaluation/expanded-baseline/phase54-factual-regression-v1.json": {
        "bytes": 415531,
        "sha256": "94273965231db0f01b65b9d39806e65885bf63e6061982fda9ffed7b4a16013d",
        "row_count": 30,
    },
}

COMPACT_DUPLICATES = {
    "data/evaluation/eval-runs/phase52-request-assessment-baseline.json":
        "data/evaluation/defense/phase52-request-assessment-baseline.json",
    "data/evaluation/eval-runs/phase52-request-assessment-uncertain-only.json":
        "data/evaluation/defense/phase52-request-assessment-uncertain-only.json",
    "data/evaluation/eval-runs/phase52-request-assessment-candidate-v1.json":
        "data/evaluation/defense/phase52-request-assessment-candidate-v1.json",
    "data/evaluation/eval-runs/phase52-request-assessment-candidate-v4.json":
        "data/evaluation/defense/phase52-request-assessment-candidate-v4.json",
    "data/evaluation/eval-runs/phase53-evidence-assessment-deterministic-only.json":
        "data/evaluation/defense/phase53-evidence-assessment-deterministic-only.json",
    "data/evaluation/eval-runs/phase53-evidence-assessment-semantic-always-v1.json":
        "data/evaluation/defense/phase53-evidence-assessment-semantic-always-v1.json",
    "data/evaluation/eval-runs/phase53-evidence-assessment-hybrid-v4.json":
        "data/evaluation/defense/phase53-evidence-assessment-hybrid-v4.json",
    "data/evaluation/eval-runs/phase53-evidence-assessment-hybrid-v11.json":
        "data/evaluation/defense/phase53-evidence-assessment-hybrid-v11.json",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _memory_metrics(rows: list[dict[str, Any]]) -> tuple[int, float]:
    memory_rows = [row for row in rows if row.get("question_type") == "conversation_memory"]
    violations = 0
    for row in memory_rows:
        for citation in row.get("citations") or []:
            rendered_source = " ".join(
                str(citation.get(field) or "")
                for field in ("document_id", "document_title", "source")
            ).casefold()
            if "memory" in rendered_source or "conversation" in rendered_source:
                violations += 1
                break
    return len(memory_rows), round(violations / len(memory_rows), 4) if memory_rows else 0.0


def apply_retention_policy() -> None:
    for relative, expected in RETIRED_RAW_ARTIFACTS.items():
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"Cannot retire missing raw artifact: {relative}")
        if path.stat().st_size != expected["bytes"] or _sha256(path) != expected["sha256"]:
            raise ValueError(f"Raw artifact drifted before retirement: {relative}")
        payload = _load(path)
        if len(payload.get("rows") or []) != expected["row_count"]:
            raise ValueError(f"Raw artifact row count drifted before retirement: {relative}")

    runtime_raw = _load(
        ROOT / "data/evaluation/expanded-baseline/phase54-live-query-regression-v5.json"
    )
    memory_case_count, memory_rate = _memory_metrics(runtime_raw.get("rows") or [])
    runtime_summary_path = ROOT / "data/evaluation/eval-runs/phase54-live-query-regression-v5.json"
    runtime_summary = _load(runtime_summary_path)
    runtime_summary.setdefault("metrics", {})["memory_case_count"] = memory_case_count
    runtime_summary["metrics"]["memory_as_evidence_violation_rate"] = memory_rate
    _write_json(runtime_summary_path, runtime_summary)

    for compact_relative, detail_relative in COMPACT_DUPLICATES.items():
        compact_path = ROOT / compact_relative
        detail_path = ROOT / detail_relative
        payload = _load(compact_path)
        if not detail_path.is_file():
            raise FileNotFoundError(f"Detailed artifact is missing: {detail_relative}")
        payload.pop("results", None)
        payload.pop("rows", None)
        payload["detail_artifact_path"] = detail_relative
        payload["detail_artifact_sha256"] = _sha256(detail_path)
        _write_json(compact_path, payload)

    index = {
        "schema_version": "raw-evaluation-artifact-index.v1",
        "policy": "Raw per-question payloads are local artifacts; compact summaries and provenance remain committed.",
        "historical_commit": HISTORICAL_COMMIT,
        "history_rewritten": False,
        "artifacts": [
            {
                "path": relative,
                **expected,
                "compact_summary_path": (
                    "data/evaluation/eval-runs/" + Path(relative).name
                ),
                "retention": "removed_from_current_tree_recoverable_from_historical_commit",
            }
            for relative, expected in RETIRED_RAW_ARTIFACTS.items()
        ],
    }
    _write_json(INDEX_PATH, index)

    for relative in RETIRED_RAW_ARTIFACTS:
        (ROOT / relative).unlink()


def validate_retention_policy() -> list[str]:
    errors: list[str] = []
    if not INDEX_PATH.is_file():
        return [f"Missing artifact index: {INDEX_PATH.relative_to(ROOT)}"]
    index = _load(INDEX_PATH)
    if index.get("schema_version") != "raw-evaluation-artifact-index.v1":
        errors.append("Artifact index schema is invalid.")
    if index.get("historical_commit") != HISTORICAL_COMMIT or index.get("history_rewritten") is not False:
        errors.append("Artifact history provenance is invalid.")
    indexed = {item.get("path"): item for item in index.get("artifacts") or []}
    for relative, expected in RETIRED_RAW_ARTIFACTS.items():
        if (ROOT / relative).exists():
            errors.append(f"Retired raw artifact is still present: {relative}")
        if indexed.get(relative) != {
            "path": relative,
            **expected,
            "compact_summary_path": "data/evaluation/eval-runs/" + Path(relative).name,
            "retention": "removed_from_current_tree_recoverable_from_historical_commit",
        }:
            errors.append(f"Artifact index entry is invalid: {relative}")
        if not (ROOT / ("data/evaluation/eval-runs/" + Path(relative).name)).is_file():
            errors.append(f"Compact summary is missing for: {relative}")
    for compact_relative, detail_relative in COMPACT_DUPLICATES.items():
        compact = _load(ROOT / compact_relative)
        if "results" in compact or "rows" in compact:
            errors.append(f"Compact summary still contains detailed rows: {compact_relative}")
        detail_path = ROOT / detail_relative
        if compact.get("detail_artifact_path") != detail_relative:
            errors.append(f"Detailed artifact reference is invalid: {compact_relative}")
        if compact.get("detail_artifact_sha256") != _sha256(detail_path):
            errors.append(f"Detailed artifact hash is invalid: {compact_relative}")
    runtime = _load(ROOT / "data/evaluation/eval-runs/phase54-live-query-regression-v5.json")
    metrics = runtime.get("metrics") or {}
    if metrics.get("memory_case_count") != 20:
        errors.append("Runtime compact summary is missing the 20-case memory sample.")
    if metrics.get("memory_as_evidence_violation_rate") is None:
        errors.append("Runtime compact summary is missing the memory-as-evidence metric.")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply or validate committed evaluation-artifact retention.")
    parser.add_argument("--apply", action="store_true", help="Retire the predeclared raw artifacts and compact duplicates.")
    args = parser.parse_args()
    if args.apply:
        apply_retention_policy()
    errors = validate_retention_policy()
    if errors:
        raise SystemExit("Evaluation artifact retention failed:\n- " + "\n- ".join(errors))
    print("Evaluation artifact retention passed.")


if __name__ == "__main__":
    main()
