"""Persistent local profile and restrained in-app notifications."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
import sqlite3

from app.database import get_database


NOTIFICATION_RETENTION = 50
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass(frozen=True)
class LocalProfile:
    display_name: str
    email_address: str


def profile_initials(name: str) -> str:
    words = [word for word in name.split() if word]
    return "".join(word[0].upper() for word in words[:2]) or "L"


def validate_profile(display_name: str, email_address: str) -> dict[str, str]:
    errors = {}
    if not display_name.strip():
        errors["display_name"] = "Enter a display name."
    elif len(display_name.strip()) > 120:
        errors["display_name"] = "Keep the display name to 120 characters or fewer."
    if not email_address.strip():
        errors["email_address"] = "Enter an email address."
    elif len(email_address.strip()) > 254 or not EMAIL_PATTERN.fullmatch(email_address.strip()):
        errors["email_address"] = "Enter an email address in a valid format."
    return errors


def load_local_profile() -> LocalProfile | None:
    row = get_database().execute(
        "SELECT display_name, email_address FROM local_profile WHERE id = 1"
    ).fetchone()
    return LocalProfile(row["display_name"], row["email_address"]) if row else None


def save_local_profile(display_name: str, email_address: str) -> LocalProfile:
    profile = LocalProfile(display_name.strip(), email_address.strip().lower())
    errors = validate_profile(profile.display_name, profile.email_address)
    if errors:
        raise ValueError(errors)
    database = get_database()
    with database:
        database.execute(
            """
            INSERT INTO local_profile (id, display_name, email_address)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                display_name = excluded.display_name,
                email_address = excluded.email_address,
                updated_at = CURRENT_TIMESTAMP
            """,
            (profile.display_name, profile.email_address),
        )
    return profile


def create_notification(code: str, message: str, *, severity: str = "info", action_url: str | None = None, action_label: str | None = None, deduplicate: bool = False) -> int:
    if severity not in {"info", "success", "warning", "critical"}:
        raise ValueError("Invalid notification severity.")
    database = get_database()
    with database:
        if deduplicate:
            existing = database.execute(
                "SELECT id FROM notifications WHERE code = ? AND dismissed_at IS NULL",
                (code,),
            ).fetchone()
            if existing:
                return existing["id"]
        cursor = database.execute(
            """
            INSERT INTO notifications
                (code, message, severity, action_url, action_label)
            VALUES (?, ?, ?, ?, ?)
            """,
            (code, message, severity, action_url, action_label),
        )
        database.execute(
            """
            DELETE FROM notifications WHERE id NOT IN (
                SELECT id FROM notifications ORDER BY created_at DESC, id DESC LIMIT ?
            )
            """,
            (NOTIFICATION_RETENTION,),
        )
    return cursor.lastrowid


def list_notifications() -> list[dict]:
    return [dict(row) for row in get_database().execute(
        """
        SELECT id, code, message, severity, action_url, action_label,
               created_at, read_at
        FROM notifications WHERE dismissed_at IS NULL
        ORDER BY created_at DESC, id DESC
        """
    ).fetchall()]


def mark_notification_read(notification_id: int) -> bool:
    database = get_database()
    with database:
        cursor = database.execute(
            "UPDATE notifications SET read_at = COALESCE(read_at, CURRENT_TIMESTAMP) WHERE id = ? AND dismissed_at IS NULL",
            (notification_id,),
        )
    return bool(cursor.rowcount)


def mark_all_notifications_read() -> None:
    database = get_database()
    with database:
        database.execute(
            "UPDATE notifications SET read_at = COALESCE(read_at, CURRENT_TIMESTAMP) WHERE dismissed_at IS NULL"
        )


def dismiss_notification(notification_id: int) -> bool:
    database = get_database()
    with database:
        cursor = database.execute(
            "UPDATE notifications SET dismissed_at = CURRENT_TIMESTAMP WHERE id = ? AND dismissed_at IS NULL",
            (notification_id,),
        )
    return bool(cursor.rowcount)


def maybe_create_backup_reminder(*, last_export: str | None) -> None:
    database = get_database()
    meaningful = database.execute(
        "SELECT EXISTS(SELECT 1 FROM business_defaults) OR EXISTS(SELECT 1 FROM events)"
    ).fetchone()[0]
    if not meaningful:
        return
    recent_reminder = database.execute(
        """
        SELECT 1 FROM notifications
        WHERE code = 'backup_reminder'
          AND created_at >= datetime('now', '-30 days')
        LIMIT 1
        """
    ).fetchone()
    if recent_reminder:
        return
    due = last_export is None
    if last_export:
        try:
            exported = datetime.fromisoformat(last_export)
            if exported.tzinfo is None:
                exported = exported.replace(tzinfo=timezone.utc)
            due = datetime.now(timezone.utc) - exported.astimezone(timezone.utc) >= timedelta(days=30)
        except ValueError:
            due = True
    if due:
        create_notification(
            "backup_reminder",
            "Consider exporting a current backup of your local data.",
            severity="info",
            action_url="/data-safety",
            action_label="Open Data Safety",
            deduplicate=True,
        )
