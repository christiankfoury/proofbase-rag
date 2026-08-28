from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from apps.api.app.core.config import get_settings
from apps.api.app.auth.tenant_context import database_security_context


def _apply_runtime_security_context(conn: psycopg.Connection) -> None:
    settings = get_settings()
    if not settings.database_enforce_rls:
        if settings.app_environment == "production":
            raise RuntimeError("DATABASE_ENFORCE_RLS cannot be disabled in production.")
        return
    tenant_id, user_id, platform_admin = database_security_context()
    conn.execute(f"set local role {settings.database_runtime_role}")
    conn.execute("select set_config('app.tenant_id', %s, true)", (tenant_id,))
    conn.execute("select set_config('app.user_id', %s, true)", (user_id,))
    conn.execute("select set_config('app.platform_admin', %s, true)", ("true" if platform_admin else "false",))


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(get_settings().database_url, row_factory=dict_row)
    try:
        _apply_runtime_security_context(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def apply_schema() -> None:
    schema_path = "apps/api/app/db/schema.sql"
    with open(schema_path, "r", encoding="utf-8") as schema_file:
        schema_sql = schema_file.read()

    conn = psycopg.connect(get_settings().database_url, row_factory=dict_row)
    try:
        conn.execute(schema_sql)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
