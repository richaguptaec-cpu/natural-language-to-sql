
import sqlite3
import time

from services.schema_service import DB_PATH
from services.sql_validator import validate_sql

DEFAULT_MAX_ROWS = 500
DEFAULT_TIMEOUT_SECONDS = 3

# SQLite operations that can change data, change schema, or
# alter connection/database behavior are not permitted.
BLOCKED_ACTION_NAMES = (
    "SQLITE_INSERT",
    "SQLITE_UPDATE",
    "SQLITE_DELETE",
    "SQLITE_CREATE_INDEX",
    "SQLITE_CREATE_TABLE",
    "SQLITE_CREATE_TEMP_INDEX",
    "SQLITE_CREATE_TEMP_TABLE",
    "SQLITE_CREATE_TEMP_TRIGGER",
    "SQLITE_CREATE_TEMP_VIEW",
    "SQLITE_CREATE_TRIGGER",
    "SQLITE_CREATE_VIEW",
    "SQLITE_CREATE_VTABLE",
    "SQLITE_DROP_INDEX",
    "SQLITE_DROP_TABLE",
    "SQLITE_DROP_TEMP_INDEX",
    "SQLITE_DROP_TEMP_TABLE",
    "SQLITE_DROP_TEMP_TRIGGER",
    "SQLITE_DROP_TEMP_VIEW",
    "SQLITE_DROP_TRIGGER",
    "SQLITE_DROP_VIEW",
    "SQLITE_DROP_VTABLE",
    "SQLITE_ALTER_TABLE",
    "SQLITE_ATTACH",
    "SQLITE_DETACH",
    "SQLITE_PRAGMA",
    "SQLITE_TRANSACTION",
    "SQLITE_SAVEPOINT",
    "SQLITE_ANALYZE",
    "SQLITE_REINDEX",
)

BLOCKED_ACTIONS = {
    getattr(sqlite3, name)
    for name in BLOCKED_ACTION_NAMES
    if hasattr(sqlite3, name)
}

BLOCKED_FUNCTIONS = {"load_extension", "readfile", "writefile"}


def _authorizer(action, arg1, arg2, database_name, trigger_name):
    """Permit reads while denying writes and restricted operations."""
    if action in BLOCKED_ACTIONS:
        return sqlite3.SQLITE_DENY

    if action == sqlite3.SQLITE_FUNCTION:
        function_name = (arg2 or arg1 or "").lower()
        if function_name in BLOCKED_FUNCTIONS:
            return sqlite3.SQLITE_DENY

    return sqlite3.SQLITE_OK


def execute_read_only_query(
    sql: str,
    max_rows: int = DEFAULT_MAX_ROWS,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """
    Validate and execute one read-only query against the sample DB.

    Returns column names, rows, and whether the output was truncated.
    Does not execute SQL unless validation passes.
    """
    if max_rows < 1:
        raise ValueError("max_rows must be at least 1.")

    if timeout_seconds < 1:
        raise ValueError("timeout_seconds must be at least 1.")

    validation = validate_sql(sql)
    if not validation["valid"]:
        raise ValueError(
            "SQL validation failed: " + "; ".join(validation["errors"])
        )

    if not DB_PATH.exists():
        raise FileNotFoundError(
            "Database not found. Run python database/init_db.py first."
        )

    # as_uri() handles absolute paths on Windows and Unix.
    read_only_uri = f"{DB_PATH.resolve().as_uri()}?mode=ro"
    deadline = time.monotonic() + timeout_seconds

    def timed_out():
        return 1 if time.monotonic() > deadline else 0

    try:
        with sqlite3.connect(
            read_only_uri,
            uri=True,
            timeout=timeout_seconds,
        ) as connection:
            connection.set_authorizer(_authorizer)
            connection.set_progress_handler(timed_out, 1000)

            cursor = connection.execute(validation["sql"])
            columns = [item[0] for item in cursor.description or []]
            rows = cursor.fetchmany(max_rows + 1)

            truncated = len(rows) > max_rows
            rows = rows[:max_rows]

            return {
                "columns": columns,
                "rows": [tuple(row) for row in rows],
                "truncated": truncated,
                "row_count": len(rows),
                "sql": validation["sql"],
            }

    except sqlite3.OperationalError as exc:
        if "interrupted" in str(exc).lower():
            raise TimeoutError(
                f"Query exceeded the {timeout_seconds}-second time limit."
            ) from exc

        raise RuntimeError(
            "SQLite could not execute the query. Check the SQL and schema."
        ) from exc
    except sqlite3.DatabaseError as exc:
        raise RuntimeError(
            "SQLite rejected the query. It may contain a restricted operation."
        ) from exc
