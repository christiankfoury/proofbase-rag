from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from typing import Any

REDACTED = "[REDACTED]"

SECRET_KEY_PARTS = {
    "api_key",
    "authorization",
    "client_secret",
    "connection_string",
    "cookie",
    "credential",
    "password",
    "private_key",
    "refresh_token",
    "signing_secret",
}
CONTENT_KEY_PARTS = {
    "answer",
    "chunk_text",
    "citation_text",
    "cleaned_markdown",
    "comment",
    "content",
    "department_name",
    "document_text",
    "email",
    "extracted_markdown",
    "file_name",
    "full_question",
    "markdown",
    "message_text",
    "notes",
    "project_name",
    "prompt_text",
    "provider_payload",
    "question",
    "raw",
    "rewritten_question",
    "source_text",
}

VALUE_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(?:postgres(?:ql)?|redis(?:s)?)://[^\s]+"),
    re.compile(r"(?i)\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
)


def text_fingerprint(value: Any, *, length: int = 16) -> str | None:
    if value in (None, ""):
        return None
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:length]


def redact_string(value: str, *, max_length: int = 240) -> str:
    redacted = value
    for pattern in VALUE_PATTERNS:
        redacted = pattern.sub(REDACTED, redacted)
    return redacted[:max_length]


def bounded_reason_code(value: Any, *, fallback: str = "redacted_reason") -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip().lower()
    if re.fullmatch(r"[a-z0-9_.:-]{1,120}", text):
        return text
    return f"{fallback}:{text_fingerprint(text)}"


def sanitize_for_log(value: Any, *, key: str = "", depth: int = 0) -> Any:
    if depth > 6:
        return "[TRUNCATED]"
    normalized_key = key.strip().lower()
    if _has_part(normalized_key, SECRET_KEY_PARTS):
        return REDACTED
    if not normalized_key.endswith(("_hash", "_id", "_ids")) and _has_part(normalized_key, CONTENT_KEY_PARTS):
        fingerprint = text_fingerprint(value)
        return f"sha256:{fingerprint}" if fingerprint else None
    if isinstance(value, Mapping):
        return {
            str(child_key)[:80]: sanitize_for_log(child_value, key=str(child_key), depth=depth + 1)
            for child_key, child_value in list(value.items())[:64]
        }
    if isinstance(value, (list, tuple, set)):
        return [sanitize_for_log(item, key=key, depth=depth + 1) for item in list(value)[:20]]
    if isinstance(value, str):
        return redact_string(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return redact_string(str(value))


def _has_part(key: str, parts: set[str]) -> bool:
    return any(part == key or part in key for part in parts)
