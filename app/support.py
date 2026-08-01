"""Privacy-safe metadata for customer-directed support diagnostics."""

from datetime import datetime
import platform
import sqlite3

from flask import current_app

from app.data_safety import APPLICATION_VERSION


PRODUCT_NAME = "Food Truck Event Profit Calculator"


def support_information() -> dict[str, str]:
    """Return technical metadata without customer content or private paths."""
    schema_version = "Unavailable"
    if not current_app.config.get("RECOVERY_MODE"):
        from app.database import get_database

        try:
            row = get_database().execute(
                "SELECT MAX(version) FROM schema_migrations"
            ).fetchone()
            schema_version = str(row[0] or 0)
        except sqlite3.Error:
            pass

    marker = current_app.config["DATA_PATHS"].root / "last-export.txt"
    last_export = "Never"
    if marker.exists():
        try:
            value = marker.read_text(encoding="utf-8").strip()
            if value:
                datetime.fromisoformat(value)
                last_export = value
        except (OSError, ValueError):
            last_export = "Unavailable"

    return {
        "app_name": PRODUCT_NAME,
        "app_version": APPLICATION_VERSION,
        "operating_system": f"{platform.system()} {platform.release()}".strip(),
        "data_storage": "Local application data on this device",
        "database_schema_version": schema_version,
        "last_successful_export": last_export,
    }
