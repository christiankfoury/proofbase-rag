from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from openai import OpenAI

from apps.api.app.core.config import get_settings
from apps.api.app.costing.estimator import estimate_chat_cost


FORBIDDEN_CLEANUP_PATTERNS = (
    "ignore previous instructions",
    "system prompt",
    "developer message",
    "hidden instruction",
    "i can't help",
    "i cannot help",
)


def hash_markdown(markdown: str) -> str:
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()


def _client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for AI Markdown cleanup")
    return OpenAI(api_key=settings.openai_api_key)


def _validate_cleaned_markdown(cleaned_markdown: str, source_markdown: str) -> str:
    cleaned = cleaned_markdown.strip()
    if not cleaned:
        raise ValueError("AI cleanup returned empty Markdown.")

    lowered = cleaned.lower()
    if any(pattern in lowered for pattern in FORBIDDEN_CLEANUP_PATTERNS):
        raise ValueError("AI cleanup returned unsafe Markdown.")

    source = source_markdown.strip()
    if len(source) >= 500 and len(cleaned) < max(120, int(len(source) * 0.25)):
        raise ValueError("AI cleanup returned too little content to preserve the source.")

    return cleaned


def cleanup_uploaded_markdown(
    *,
    document: dict[str, Any],
    requested_by: str,
    model: str | None = None,
) -> dict[str, Any]:
    ingestion_status = document.get("version", {}).get("ingestion_status")
    if ingestion_status not in {"pending_review", "failed"}:
        raise ValueError("Only pending-review or failed document versions can be cleaned up.")

    source_markdown = (document.get("review_markdown") or document.get("markdown_preview") or "").strip()
    if not source_markdown:
        raise ValueError("AI cleanup requires extracted Markdown.")

    settings = get_settings()
    selected_model = model or settings.openai_chat_model
    system_prompt = (
        "You clean deterministic PDF extraction output into readable Markdown for a human editor. "
        "Preserve all source facts, numbers, obligations, names, dates, and caveats. "
        "Do not add new facts, policy claims, citations, summaries, or commentary. "
        "Return only Markdown."
    )
    user_prompt = (
        "Clean up this extracted Markdown. Keep meaning unchanged, fix headings, spacing, bullets, "
        "line breaks, and obvious OCR artifacts only.\n\n"
        f"{source_markdown}"
    )
    response = _client().chat.completions.create(
        model=selected_model,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    cleaned_markdown = _validate_cleaned_markdown(response.choices[0].message.content or "", source_markdown)
    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else None
    output_tokens = usage.completion_tokens if usage else None
    cost = estimate_chat_cost(model=selected_model, input_tokens=input_tokens, output_tokens=output_tokens)
    cleanup_timestamp = datetime.now(UTC).isoformat()
    source_hash = hash_markdown(source_markdown)
    cleaned_hash = hash_markdown(cleaned_markdown)
    metadata = {
        "status": "draft_returned_not_indexed",
        "model": selected_model,
        "cleanup_timestamp": cleanup_timestamp,
        "requested_by": requested_by,
        "source_content_hash": source_hash,
        "cleaned_content_hash": cleaned_hash,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        **cost,
    }
    return {
        "cleaned_markdown": cleaned_markdown,
        "metadata": metadata,
    }
