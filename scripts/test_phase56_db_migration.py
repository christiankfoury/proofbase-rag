from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app import main as api_main
from apps.api.app.auth.oidc import OidcVerifierConfig, mint_local_fixture_token
from apps.api.app.core.config import Settings, get_settings


TENANT_TABLES = (
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
)


def main() -> None:
    schema_sql = (ROOT / "apps/api/app/db/schema.sql").read_text(encoding="utf-8")
    conn = psycopg.connect(get_settings().database_url, row_factory=dict_row)
    try:
        conn.execute(schema_sql)
        missing = {}
        for table in TENANT_TABLES:
            count = conn.execute(f"select count(*) as n from {table} where tenant_id is null").fetchone()["n"]
            if count:
                missing[table] = count
        assert not missing, missing
        demo = conn.execute(
            """
            select t.slug, t.is_demo, p.tenant_id::text
            from tenants t
            join projects p on p.tenant_id = t.id
            where p.seeded_data_key = 'northstar_synthetic'
            """
        ).fetchone()
        assert demo == {
            "slug": "northstar-demo",
            "is_demo": True,
            "tenant_id": "00000000-0000-0000-0000-000000002801",
        }
        identity_count = conn.execute("select count(*) as n from external_identities").fetchone()["n"]
        assert identity_count >= 7
        conn.rollback()
    finally:
        conn.close()
    fixture_secret = "phase-56-local-fixture-secret-with-32-bytes"
    fixture_settings = Settings(
        _env_file=None,
        app_environment="test",
        auth_mode="oidc_fixture",
        oidc_local_signing_secret=fixture_secret,
        oidc_issuer="https://identity.local.proofbase.invalid",
        oidc_audience="proofbase-api",
    )
    token = mint_local_fixture_token(
        OidcVerifierConfig(
            issuer=fixture_settings.oidc_issuer,
            audience=fixture_settings.oidc_audience,
            local_signing_secret=fixture_secret,
        ),
        subject="northstar:00000000-0000-0000-0000-000000002706",
        tenant_ids=["00000000-0000-0000-0000-000000002801"],
        now=int(time.time()),
    )
    with patch.object(api_main, "get_settings", return_value=fixture_settings):
        response = TestClient(api_main.app).get(
            "/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-Id": "00000000-0000-0000-0000-000000002801",
            },
        )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["auth_mode"] == "oidc_fixture"
    assert payload["user"]["identity_source"] == "oidc"
    print(json.dumps({"phase": 56, "migration_rehearsal": "passed_and_rolled_back", "null_tenant_rows": 0}))


if __name__ == "__main__":
    main()
