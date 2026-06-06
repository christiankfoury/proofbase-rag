from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.db.session import get_connection


def _request_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 120) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, method=method)
    request.add_header("Accept", "application/json")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"detail": body}
        return exc.code, parsed
    except URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc}") from exc


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _database_counts() -> dict[str, int]:
    with get_connection() as conn:
        row = conn.execute(
            """
            select
              (select count(*) from documents) as documents,
              (select count(*) from chunks) as chunks
            """
        ).fetchone()
    return {"documents": row["documents"], "chunks": row["chunks"]}


def _check_query_shape(response: dict) -> None:
    required_keys = ["response_type", "answer", "citations", "final_confidence"]
    missing = [key for key in required_keys if key not in response]
    _assert(not missing, f"Query response missing keys: {missing}")
    _assert(isinstance(response["answer"], str) and response["answer"], "Query answer must be a non-empty string")
    _assert(isinstance(response["citations"], list), "Query citations must be a list")
    _assert(response["final_confidence"] is None or isinstance(response["final_confidence"], (int, float)), "final_confidence must be numeric or null")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base-url", default="http://localhost:8000")
    parser.add_argument("--skip-query", action="store_true", help="Skip OpenAI-backed query checks.")
    args = parser.parse_args()

    api_base = args.api_base_url.rstrip("/")
    results: dict[str, Any] = {}

    health_status, health = _request_json("GET", f"{api_base}/health")
    _assert(health_status == 200 and health.get("status") == "ok", f"/health failed: {health_status} {health}")
    results["health"] = health

    ready_status, ready = _request_json("GET", f"{api_base}/ready")
    _assert(ready_status == 200 and ready.get("status") == "ready", f"/ready failed: {ready_status} {ready}")
    results["ready"] = ready

    counts = _database_counts()
    _assert(counts["documents"] > 0, "Expected at least one ingested document")
    _assert(counts["chunks"] > 0, "Expected at least one ingested chunk")
    results["database_counts"] = counts

    if args.skip_query:
        results["query_checks"] = "skipped"
    else:
        normal_status, normal_query = _request_json(
            "POST",
            f"{api_base}/query",
            {
                "question": "Where does Northstar Analytics have offices?",
                "user_role": "Employee",
                "retrieval_mode": "vector_only",
                "chunking_strategy": "section_based",
            },
        )
        _assert(normal_status == 200, f"Normal query failed: {normal_status} {normal_query}")
        _check_query_shape(normal_query)

        restricted_status, restricted_query = _request_json(
            "POST",
            f"{api_base}/query",
            {
                "question": "What is the promotion calibration process?",
                "user_role": "Employee",
                "retrieval_mode": "vector_only",
                "chunking_strategy": "section_based",
            },
        )
        _assert(restricted_status == 200, f"Restricted query failed: {restricted_status} {restricted_query}")
        _check_query_shape(restricted_query)
        _assert(
            restricted_query["response_type"] == "refuse_no_access",
            f"Restricted query should refuse access, got {restricted_query['response_type']}",
        )
        permission_check = restricted_query.get("permission_check") or {}
        _assert(
            permission_check.get("unauthorized_chunks_reached_generation") is False,
            "Restricted query exposed unauthorized chunks to generation",
        )
        results["query_checks"] = {
            "normal_response_type": normal_query["response_type"],
            "restricted_response_type": restricted_query["response_type"],
            "restricted_permission_check": permission_check,
        }

    print(json.dumps({"status": "passed", **results}, indent=2))


if __name__ == "__main__":
    main()
