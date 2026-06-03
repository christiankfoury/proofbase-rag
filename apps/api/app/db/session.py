from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from apps.api.app.core.config import get_settings


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(get_settings().database_url, row_factory=dict_row)
    try:
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

    with get_connection() as conn:
        conn.execute(schema_sql)
