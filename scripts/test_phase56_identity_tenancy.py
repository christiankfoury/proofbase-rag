from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import HTTPException

from apps.api.app.auth.oidc import (
    LocalFixtureTokenVerifier,
    OidcValidationError,
    OidcVerifierConfig,
    mint_local_fixture_token,
    new_authorization_transaction,
    validate_authorization_transaction,
)
from apps.api.app.auth.session_security import (
    csrf_digest,
    issue_session_envelope,
    new_csrf_token,
    session_is_active,
    validate_csrf_token,
)
from apps.api.app.core.config import Settings
from apps.api.app import main


TENANT_ID = "00000000-0000-0000-0000-000000002801"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000002899"
SECRET = "phase-56-local-fixture-secret-with-32-bytes"
NOW = 1_800_000_000


def _config(**overrides) -> OidcVerifierConfig:
    values = {
        "issuer": "https://identity.local.proofbase.invalid",
        "audience": "proofbase-api",
        "local_signing_secret": SECRET,
        "clock_skew_seconds": 0,
    }
    values.update(overrides)
    return OidcVerifierConfig(**values)


def _token(**overrides) -> str:
    values = {
        "subject": "northstar:00000000-0000-0000-0000-000000002706",
        "tenant_ids": [TENANT_ID],
        "now": NOW,
        "nonce": "nonce-1",
        "token_id": "token-1",
    }
    values.update(overrides)
    return mint_local_fixture_token(_config(), **values)


def _assert_rejected(verifier: LocalFixtureTokenVerifier, token: str, contains: str) -> None:
    try:
        verifier.verify(token, expected_nonce="nonce-1")
    except OidcValidationError as exc:
        assert contains.lower() in str(exc).lower(), (contains, str(exc))
    else:
        raise AssertionError(f"Expected token rejection containing {contains!r}")


def test_strict_local_token_verification() -> None:
    verifier = LocalFixtureTokenVerifier(_config(), now=lambda: NOW + 10)
    claims = verifier.verify(_token(), expected_nonce="nonce-1")
    assert claims["sub"].startswith("northstar:")
    assert claims["tenant_ids"] == [TENANT_ID]

    _assert_rejected(verifier, _token(lifetime_seconds=5), "expired")
    wrong_issuer = mint_local_fixture_token(
        _config(issuer="https://wrong.invalid"), subject="subject", tenant_ids=[TENANT_ID], now=NOW, nonce="nonce-1"
    )
    _assert_rejected(verifier, wrong_issuer, "issuer")
    wrong_audience = mint_local_fixture_token(
        _config(audience="wrong-api"), subject="subject", tenant_ids=[TENANT_ID], now=NOW, nonce="nonce-1"
    )
    _assert_rejected(verifier, wrong_audience, "audience")
    _assert_rejected(verifier, _token()[:-1] + ("A" if _token()[-1] != "A" else "B"), "invalid bearer")
    try:
        verifier.verify(_token(), expected_nonce="wrong-nonce")
    except OidcValidationError as exc:
        assert "nonce" in str(exc).lower()
    else:
        raise AssertionError("Expected nonce mismatch")
    try:
        verifier.verify(_token(), is_revoked=lambda token_id: token_id == "token-1")
    except OidcValidationError as exc:
        assert "revoked" in str(exc).lower()
    else:
        raise AssertionError("Expected revoked token rejection")


def test_state_csrf_and_session_expiry() -> None:
    first = new_authorization_transaction()
    second = new_authorization_transaction()
    assert first["state"] != second["state"]
    assert first["nonce"] != second["nonce"]
    validate_authorization_transaction(
        state=first["state"], nonce=first["nonce"], state_hash=first["state_hash"], nonce_hash=first["nonce_hash"]
    )
    try:
        validate_authorization_transaction(
            state=second["state"], nonce=first["nonce"], state_hash=first["state_hash"], nonce_hash=first["nonce_hash"]
        )
    except OidcValidationError:
        pass
    else:
        raise AssertionError("Expected state mismatch")

    csrf = new_csrf_token()
    assert validate_csrf_token(csrf, csrf_digest(csrf))
    assert not validate_csrf_token("attacker", csrf_digest(csrf))
    issued = datetime(2027, 1, 1, tzinfo=UTC)
    envelope = issue_session_envelope(absolute_minutes=480, idle_minutes=30, now=issued)
    assert session_is_active(envelope, now=issued + timedelta(minutes=29))
    assert not session_is_active(envelope, now=issued + timedelta(minutes=31))


def test_api_auth_boundary() -> None:
    settings = Settings(
        _env_file=None,
        app_environment="test",
        auth_mode="oidc_fixture",
        oidc_local_signing_secret=SECRET,
        oidc_issuer=_config().issuer,
        oidc_audience=_config().audience,
    )
    user = {
        "id": "00000000-0000-0000-0000-000000002706",
        "tenant_id": TENANT_ID,
        "business_role": "Admin",
        "is_admin": True,
        "memberships": [],
    }
    api_token = _token(now=int(time.time()))
    with (
        patch.object(main, "get_settings", return_value=settings),
        patch.object(main, "token_is_revoked", return_value=False),
        patch.object(main, "resolve_oidc_user", return_value=user),
        patch.object(main, "set_request_principal"),
    ):
        resolved = main.current_demo_user(None, TENANT_ID, f"Bearer {api_token}")
        assert resolved == user
        for args, status in [
            (("demo-id", TENANT_ID, f"Bearer {api_token}"), 400),
            ((None, TENANT_ID, None), 401),
            ((None, OTHER_TENANT_ID, f"Bearer {api_token}"), 403),
        ]:
            try:
                main.current_demo_user(*args)
            except HTTPException as exc:
                assert exc.status_code == status
            else:
                raise AssertionError(f"Expected HTTP {status}")
        with patch.object(main, "resolve_oidc_user", side_effect=HTTPException(status_code=401, detail="disabled")):
            try:
                main.current_demo_user(None, TENANT_ID, f"Bearer {api_token}")
            except HTTPException as exc:
                assert exc.status_code == 401
            else:
                raise AssertionError("Expected disabled identity rejection")


def test_production_config_and_schema_contract() -> None:
    try:
        Settings(_env_file=None, app_environment="production", auth_mode="local_demo")
    except ValueError as exc:
        assert "Production requires AUTH_MODE=oidc" in str(exc)
    else:
        raise AssertionError("Production must reject local demo auth")

    schema = Path("apps/api/app/db/schema.sql").read_text(encoding="utf-8")
    for table in (
        "tenants",
        "tenant_memberships",
        "external_identities",
        "auth_sessions",
        "oidc_authorization_transactions",
        "revoked_oidc_tokens",
    ):
        assert f"create table if not exists {table}" in schema
    for table in (
        "projects",
        "project_departments",
        "project_memberships",
        "documents",
        "document_versions",
        "ingestion_jobs",
        "chunks",
        "chunk_embeddings",
        "chat_sessions",
        "chat_messages",
        "feedback",
        "audit_logs",
        "evaluation_runs",
        "evaluation_results",
        "evaluation_reviews",
    ):
        assert f"alter table {table} add column if not exists tenant_id" in schema
    assert "Northstar Analytics Demo" in schema
    assert "where tenant_id is null" in schema


def main_test() -> None:
    test_strict_local_token_verification()
    test_state_csrf_and_session_expiry()
    test_api_auth_boundary()
    test_production_config_and_schema_contract()
    print(json.dumps({"phase": 56, "status": "passed", "sealed_holdouts_touched": False}))


if __name__ == "__main__":
    main_test()
