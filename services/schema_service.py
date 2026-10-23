
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "sample.db"


def get_database_schema() -> str:
    """Return the SQLite tables, columns, and relationships."""

    if not DB_PATH.exists():
        raise FileNotFoundError(
            "Sample database not found. Run database/init_db.py first."
        )

    schema_parts = []

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        for table_row in tables:
            table_name = table_row["name"]

            # Table names come from SQLite metadata.
            # Quote the identifier before using it in PRAGMA.
            quoted_name = '"' + table_name.replace('"', '""') + '"'

            columns = connection.execute(
                f"PRAGMA table_info({quoted_name})"
            ).fetchall()

            column_definitions = [
                f"  {column['name']} {column['type']}"
                + (" PRIMARY KEY" if column["pk"] else "")
                + (" NOT NULL" if column["notnull"] else "")
                for column in columns
            ]

            foreign_keys = connection.execute(
                f"PRAGMA foreign_key_list({quoted_name})"
            ).fetchall()

            relationship_definitions = [
                f"  FOREIGN KEY ({fk['from']}) "
                f"REFERENCES {fk['table']}({fk['to']})"
                for fk in foreign_keys
            ]

            definitions = column_definitions + relationship_definitions

            schema_parts.append(
                f"CREATE TABLE {table_name} (\n"
                + ",\n".join(definitions)
                + "\n);"
            )

    if not schema_parts:
        return "No tables were found in the database."

    return "\n\n".join(schema_parts)
