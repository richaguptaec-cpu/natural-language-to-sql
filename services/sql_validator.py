
import sqlite3

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from services.schema_service import DB_PATH


BLOCKED_FUNCTIONS = {
    "load_extension",
    "readfile",
    "writefile",
}


def _load_schema() -> dict[str, set[str]]:
    """Load actual SQLite table and column names."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            "Database not found. Run python database/init_db.py first."
        )

    schema = {}

    with sqlite3.connect(DB_PATH) as connection:
        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
        """).fetchall()

        for (table_name,) in tables:
            quoted_name = '"' + table_name.replace('"', '""') + '"'
            columns = connection.execute(
                f"PRAGMA table_info({quoted_name})"
            ).fetchall()

            schema[table_name.lower()] = {
                row[1].lower() for row in columns
            }

    return schema


def _invalid(*messages: str) -> dict:
    return {"valid": False, "errors": list(messages)}


def validate_sql(sql: str) -> dict:
    """Validate a single, schema-aware SELECT query. Never execute it."""

    if not sql or not sql.strip():
        return _invalid("SQL query is empty.")

    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except ParseError:
        return _invalid("SQL syntax is invalid for SQLite.")

    statements = [statement for statement in statements if statement]

    if len(statements) != 1:
        return _invalid("Exactly one SQL statement is allowed.")

    query = statements[0]

    # Only support a top-level SELECT in this version.
    # This rejects DML, DDL, PRAGMA, UNION, and other query types.
    if not isinstance(query, exp.Select):
        return _invalid(
            "Only a single SELECT query is supported."
        )

    # Keep the first version intentionally conservative.
    if any(query.find_all(exp.CTE)):
        return _invalid("CTEs (WITH clauses) are not yet supported.")

    if any(query.find_all(exp.Subquery)):
        return _invalid("Subqueries are not yet supported.")

    # Reject known risky functions if they are represented as
    # anonymous function calls by SQLGlot.
    for function in query.find_all(exp.Anonymous):
        if function.name.lower() in BLOCKED_FUNCTIONS:
            return _invalid(
                f"Function '{function.name}' is not allowed."
            )

    try:
        schema = _load_schema()
    except (FileNotFoundError, sqlite3.Error):
        return _invalid("Could not load the SQLite database schema.")

    errors = []
    alias_to_table = {}
    referenced_tables = set()

    for table in query.find_all(exp.Table):
        # Reject table-valued functions and unsupported sources.
        if not isinstance(table.this, exp.Identifier):
            errors.append("Unsupported table source.")
            continue

        table_name = table.name.lower()

        if table_name not in schema:
            errors.append(f"Unknown table: {table.name}")
            continue

        alias = table.alias_or_name.lower()

        if alias in alias_to_table:
            errors.append(f"Duplicate table alias: {alias}")
            continue

        alias_to_table[alias] = table_name
        referenced_tables.add(table_name)

    if errors:
        return _invalid(*dict.fromkeys(errors))

    select_aliases = {
        item.alias.lower()
        for item in query.expressions
        if isinstance(item, exp.Alias)
    }

    for column in query.find_all(exp.Column):
        column_name = column.name.lower()

        # Allow SELECT * and alias.*.
        if column_name == "*":
            continue

        # Permit SELECT aliases, e.g. ORDER BY total_spent.
        if not column.table and column_name in select_aliases:
            continue

        if column.table:
            qualifier = column.table.lower()
            table_name = alias_to_table.get(qualifier)

            if table_name is None:
                errors.append(
                    f"Unknown table alias or qualifier: {column.table}"
                )
            elif column_name not in schema[table_name]:
                errors.append(
                    f"Unknown column '{column.name}' "
                    f"in table '{table_name}'."
                )
        else:
            matching_tables = [
                table_name
                for table_name in referenced_tables
                if column_name in schema[table_name]
            ]

            if not matching_tables:
                errors.append(f"Unknown column: {column.name}")
            elif len(matching_tables) > 1:
                errors.append(
                    f"Ambiguous column '{column.name}'. "
                    "Qualify it with a table name or alias."
                )

    if errors:
        return _invalid(*dict.fromkeys(errors))

    return {
        "valid": True,
        "errors": [],
        "sql": query.sql(dialect="sqlite"),
    }
