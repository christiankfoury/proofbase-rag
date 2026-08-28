from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class SessionEnvelope:
    issued_at: datetime
    last_seen_at: datetime
    absolute_expires_at: datetime
    idle_expires_at: datetime


def issue_session_envelope(*, absolute_minutes: int, idle_minutes: int, now: datetime | None = None) -> SessionEnvelope:
    issued_at = now or datetime.now(UTC)
    return SessionEnvelope(
        issued_at=issued_at,
        last_seen_at=issued_at,
        absolute_expires_at=issued_at + timedelta(minutes=absolute_minutes),
        idle_expires_at=issued_at + timedelta(minutes=idle_minutes),
    )


def session_is_active(envelope: SessionEnvelope, *, now: datetime | None = None) -> bool:
    checked_at = now or datetime.now(UTC)
    return checked_at < envelope.absolute_expires_at and checked_at < envelope.idle_expires_at


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def validate_csrf_token(token: str, expected_digest: str) -> bool:
    return hmac.compare_digest(csrf_digest(token), expected_digest)


SESSION_COOKIE_CONTRACT = {
    "http_only": True,
    "secure_in_production": True,
    "same_site": "lax",
    "path": "/",
}
