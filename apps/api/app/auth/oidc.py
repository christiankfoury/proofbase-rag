from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Callable


class OidcValidationError(ValueError):
    """A deliberately non-specific OIDC validation failure."""


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, TypeError) as exc:
        raise OidcValidationError("Invalid token encoding.") from exc


def _json_segment(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(_b64url_decode(value))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise OidcValidationError("Invalid token payload.") from exc
    if not isinstance(parsed, dict):
        raise OidcValidationError("Invalid token payload.")
    return parsed


@dataclass(frozen=True)
class OidcVerifierConfig:
    issuer: str
    audience: str
    local_signing_secret: str
    clock_skew_seconds: int = 60
    max_token_age_seconds: int = 3600


class LocalFixtureTokenVerifier:
    """Strict HS256 verifier for local fixtures; never a hosted-provider substitute."""

    def __init__(self, config: OidcVerifierConfig, *, now: Callable[[], float] = time.time):
        if len(config.local_signing_secret.encode("utf-8")) < 32:
            raise ValueError("Local fixture signing secret must be at least 32 bytes.")
        self.config = config
        self._now = now

    def verify(
        self,
        token: str,
        *,
        expected_nonce: str | None = None,
        is_revoked: Callable[[str], bool] | None = None,
    ) -> dict[str, Any]:
        parts = token.split(".")
        if len(parts) != 3:
            raise OidcValidationError("Invalid bearer token.")
        encoded_header, encoded_claims, encoded_signature = parts
        header = _json_segment(encoded_header)
        if header.get("alg") != "HS256" or header.get("typ") not in {None, "JWT"}:
            raise OidcValidationError("Unsupported token algorithm.")
        signed = f"{encoded_header}.{encoded_claims}".encode("ascii")
        expected_signature = hmac.new(
            self.config.local_signing_secret.encode("utf-8"), signed, hashlib.sha256
        ).digest()
        actual_signature = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise OidcValidationError("Invalid bearer token.")

        claims = _json_segment(encoded_claims)
        now = int(self._now())
        skew = self.config.clock_skew_seconds
        if claims.get("iss") != self.config.issuer:
            raise OidcValidationError("Invalid token issuer.")
        audiences = claims.get("aud")
        audiences = [audiences] if isinstance(audiences, str) else audiences
        if not isinstance(audiences, list) or self.config.audience not in audiences:
            raise OidcValidationError("Invalid token audience.")
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise OidcValidationError("Token subject is required.")
        for claim in ("iat", "exp"):
            if not isinstance(claims.get(claim), int):
                raise OidcValidationError(f"Token {claim} claim is required.")
        if claims["exp"] <= now - skew:
            raise OidcValidationError("Bearer token has expired.")
        if claims["iat"] > now + skew or now - claims["iat"] > self.config.max_token_age_seconds + skew:
            raise OidcValidationError("Bearer token age is invalid.")
        if isinstance(claims.get("nbf"), int) and claims["nbf"] > now + skew:
            raise OidcValidationError("Bearer token is not active.")
        if expected_nonce is not None and not hmac.compare_digest(str(claims.get("nonce", "")), expected_nonce):
            raise OidcValidationError("OIDC nonce mismatch.")
        token_id = claims.get("jti")
        if is_revoked is not None and isinstance(token_id, str) and is_revoked(token_id):
            raise OidcValidationError("Bearer token is revoked.")
        return claims


def mint_local_fixture_token(
    config: OidcVerifierConfig,
    *,
    subject: str,
    tenant_ids: list[str],
    now: int | None = None,
    lifetime_seconds: int = 900,
    nonce: str | None = None,
    token_id: str | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    issued_at = int(time.time()) if now is None else now
    header = {"alg": "HS256", "typ": "JWT"}
    claims: dict[str, Any] = {
        "iss": config.issuer,
        "aud": config.audience,
        "sub": subject,
        "iat": issued_at,
        "exp": issued_at + lifetime_seconds,
        "jti": token_id or secrets.token_urlsafe(18),
        "tenant_ids": tenant_ids,
    }
    if nonce is not None:
        claims["nonce"] = nonce
    claims.update(extra_claims or {})
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    encoded_claims = _b64url_encode(json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signed = f"{encoded_header}.{encoded_claims}".encode("ascii")
    signature = hmac.new(config.local_signing_secret.encode("utf-8"), signed, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_claims}.{_b64url_encode(signature)}"


def new_authorization_transaction() -> dict[str, str]:
    """Return opaque state/nonce values; persistence stores only their hashes."""
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    return {"state": state, "nonce": nonce, "state_hash": hash_secret(state), "nonce_hash": hash_secret(nonce)}


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_authorization_transaction(*, state: str, nonce: str, state_hash: str, nonce_hash: str) -> None:
    if not hmac.compare_digest(hash_secret(state), state_hash):
        raise OidcValidationError("OIDC state mismatch.")
    if not hmac.compare_digest(hash_secret(nonce), nonce_hash):
        raise OidcValidationError("OIDC nonce mismatch.")
