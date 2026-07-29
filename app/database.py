import sqlite3
from pathlib import Path


SCHEMA_PATH = (
    Path(__file__).resolve().parent
    / "schema"
    / "business_defaults.sql"
)


def apply_business_defaults_schema(
    connection: sqlite3.Connection,
) -> None:
    """Create the business-defaults table on a database connection."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    connection.executescript(schema)