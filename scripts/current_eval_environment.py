"""Isolated local database and reproducible, non-secret runtime fingerprint."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DBNAME = "proofbase_eval_phase68"


def configure():
    from apps.api.app.core.config import get_settings
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    original = get_settings()
    parts = conninfo_to_dict(original.database_url)
    if parts.get("host") not in {"localhost", "127.0.0.1"}:
        raise ValueError("Only local evaluation databases are permitted")
    parts["dbname"] = DBNAME
    isolated = make_conninfo(**parts)
    os.environ["DATABASE_URL"] = isolated
    os.environ["PROOFBASE_TELEMETRY_ENABLED"] = "false"
    # Test-process admission capacity for 60 queries plus upload indexing.
    # App defaults stay at $5; Ledger still caps actual external API work at $2.00.
    os.environ["TENANT_DAILY_AI_BUDGET_USD"] = "10"
    for key, filename in {"OBSERVABILITY_LOG_PATH": "requests.jsonl", "AUDIT_LOG_PATH": "audit.jsonl",
                          "SECURITY_EVENT_LOG_PATH": "security.jsonl", "SECURITY_NOTIFICATION_LOG_PATH": "notifications.jsonl",
                          "UPLOAD_STORAGE_DIR": "uploads", "FILE_QUARANTINE_DIR": "quarantine"}.items():
        os.environ[key] = str(ROOT / "data/evaluation/local-runs/current-phase68" / filename)
    # Dedicated Redis namespace prevents evaluation admission from consuming demo quotas.
    if original.rate_limit_backend == "redis":
        from urllib.parse import urlsplit, urlunsplit
        redis = urlsplit(original.redis_url)
        os.environ["REDIS_URL"] = urlunsplit(redis._replace(path="/15"))
    get_settings.cache_clear()
    return get_settings()


def fingerprint(settings):
    import psycopg
    safe = {k: v for k, v in settings.model_dump(mode="json").items()
            if k.startswith(("retrieval_", "request_assessment_", "evidence_assessment_", "post_generation_"))
            or isinstance(v, (bool, int, float))
            or k in {"default_demo_tenant_id", "default_demo_user_id", "database_runtime_role", "openai_chat_model", "openai_embedding_model", "auth_mode", "app_environment", "rate_limit_backend",
                     "file_parser_mode", "file_scanner_mode"}}
    tables = {}
    with psycopg.connect(settings.database_url) as conn:
        for table in ("documents", "document_versions", "chunks", "chunk_embeddings", "demo_users", "projects", "project_departments", "project_memberships", "prompt_versions"):
            # Preserve row content, including embeddings/ACLs, without publishing credentials or user data.
            rows = conn.execute(f"select row_to_json(t)::text from {table} t order by row_to_json(t)::text").fetchall()
            tables[table] = {"count": len(rows), "sha256": hashlib.sha256("\n".join(r[0] for r in rows).encode()).hexdigest()}
    return {"settings": safe, "tables": tables, "database": DBNAME,
            "call_output_cap": 2048, "sdk_retries": 0, "temperature_note": "runtime configuration; grader temperature zero; provider output is not deterministic"}


def prepare():
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    from apps.api.app.core.config import get_settings
    parts = conninfo_to_dict(get_settings().database_url)
    if parts.get("host") not in {"localhost", "127.0.0.1"} or parts.get("dbname") == DBNAME:
        raise ValueError("Expected original local database, not evaluation target")
    source = parts["dbname"]
    parts["dbname"] = "postgres"
    with psycopg.connect(make_conninfo(**parts), autocommit=True) as conn:
        if conn.execute("select 1 from pg_database where datname=%s", (DBNAME,)).fetchone():
            raise ValueError("Isolated database already exists; refuse replacement")
        conn.execute(sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(sql.Identifier(DBNAME), sql.Identifier(source)))
    print("Created isolated local evaluation database; original retained")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    else:
        print(json.dumps(fingerprint(configure()), indent=2))
