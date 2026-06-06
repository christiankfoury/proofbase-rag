from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
LOG_PATH = ROOT / "data" / "observability" / "request-logs.jsonl"

_lock = threading.Lock()


def log_request(entry: dict[str, Any]) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, default=str) + "\n"
        with _lock:
            with LOG_PATH.open("a", encoding="utf-8") as fh:
                fh.write(line)
    except Exception:
        return


def build_request_entry(
    *,
    request_id: str,
    timestamp: str,
    user_role: str,
    session_id: str | None,
    question_truncated: str,
    rewritten_question: str | None,
    retrieval_mode: str,
    chunking_strategy: str,
    top_k: int,
    retrieved_chunk_ids: list[str],
    retrieved_document_ids: list[str],
    response_type: str | None,
    citation_count: int,
    final_confidence: float | None,
    retrieval_latency_ms: int | None,
    generation_latency_ms: int | None,
    total_latency_ms: int | None,
    prompt_version: str | None,
    model: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
    error: str | None,
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "timestamp": timestamp,
        "user_role": user_role,
        "session_id": session_id,
        "question": question_truncated,
        "rewritten_question": rewritten_question,
        "retrieval_mode": retrieval_mode,
        "chunking_strategy": chunking_strategy,
        "top_k": top_k,
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "retrieved_document_ids": retrieved_document_ids,
        "response_type": response_type,
        "citation_count": citation_count,
        "final_confidence": final_confidence,
        "retrieval_latency_ms": retrieval_latency_ms,
        "generation_latency_ms": generation_latency_ms,
        "total_latency_ms": total_latency_ms,
        "prompt_version": prompt_version,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": None,
        "error": error,
    }
