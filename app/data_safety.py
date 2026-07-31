"""Portable backup, restore validation, and automatic recovery snapshots."""

from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo

from app.data_paths import ApplicationDataPaths
from app.migrations import (
    DatabaseMigrationError,
    LATEST_SUPPORTED_SCHEMA_VERSION,
    migrate_database,
    verify_version_1,
)


BACKUP_FORMAT_VERSION = 1
APPLICATION_VERSION = "0.1.0"
DATABASE_ARCHIVE_NAME = "database.sqlite"
MANIFEST_ARCHIVE_NAME = "manifest.json"
MAX_BACKUP_BYTES = 100 * 1024 * 1024
RECOVERY_RETENTION = 5


class BackupValidationError(ValueError):
    """Raised when a supplied backup is unsafe or incompatible."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _filename_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_database(path: Path, *, allow_migration: bool = False) -> None:
    with path.open("rb") as source:
        header = source.read(16)
    if header != b"SQLite format 3\x00":
        raise BackupValidationError("The backup database is not recognizable.")
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise BackupValidationError("The backup database is damaged.")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise BackupValidationError(
                "The backup contains invalid data relationships."
            )
        if allow_migration:
            migrate_database(connection)
        else:
            row = connection.execute(
                "SELECT MAX(version) FROM schema_migrations"
            ).fetchone()
            if row is None or row[0] != LATEST_SUPPORTED_SCHEMA_VERSION:
                raise BackupValidationError(
                    "The backup database version is not current."
                )
            verify_version_1(connection)
    except sqlite3.Error as error:
        raise BackupValidationError(
            "The backup database could not be read."
        ) from error
    except DatabaseMigrationError as error:
        message = str(error)
        if "newer" in message:
            raise BackupValidationError(
                "This backup requires a newer application version."
            ) from error
        raise BackupValidationError(
            "The backup database schema is incompatible."
        ) from error
    finally:
        connection.close()


def _snapshot_database(
    live: sqlite3.Connection,
    destination: Path,
    *,
    allow_older_supported: bool = False,
) -> None:
    snapshot = sqlite3.connect(destination)
    try:
        live.backup(snapshot)
    finally:
        snapshot.close()
    try:
        _validate_database(destination)
    except BackupValidationError:
        if not allow_older_supported:
            raise
        from app.migrations import (
            _is_known_pre_v1_defaults_schema,
            _recorded_migrations,
            _user_tables,
            _verify_ledger,
            _verify_version_2_source,
        )

        connection = sqlite3.connect(destination)
        try:
            tables = _user_tables(connection)
            if _is_known_pre_v1_defaults_schema(connection, tables):
                return
            if "schema_migrations" in tables:
                _verify_ledger(connection)
                recorded = _recorded_migrations(connection)
                if recorded and recorded[-1][0] == 1:
                    _verify_version_2_source(connection)
                    return
            raise
        finally:
            connection.close()


def _database_schema_version(path: Path) -> int:
    connection = sqlite3.connect(path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "schema_migrations" not in tables:
            return 0
        return connection.execute(
            "SELECT MAX(version) FROM schema_migrations"
        ).fetchone()[0] or 0
    finally:
        connection.close()


def _manifest(database_path: Path, *, kind: str) -> dict:
    return {
        "backup_format_version": BACKUP_FORMAT_VERSION,
        "application_version": APPLICATION_VERSION,
        "database_schema_version": _database_schema_version(database_path),
        "created_at": _timestamp(),
        "database_filename": DATABASE_ARCHIVE_NAME,
        "database_sha256": _checksum(database_path),
        "kind": kind,
    }


def _write_archive(database_path: Path, target: Path, *, kind: str) -> None:
    manifest = _manifest(database_path, kind=kind)
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(database_path, DATABASE_ARCHIVE_NAME)
        archive.writestr(
            MANIFEST_ARCHIVE_NAME,
            json.dumps(manifest, sort_keys=True, indent=2),
        )


def create_customer_backup(
    live: sqlite3.Connection,
    paths: ApplicationDataPaths,
) -> tuple[BytesIO, str]:
    """Return a validated portable backup without exposing local paths."""
    with tempfile.TemporaryDirectory(dir=paths.staging) as temporary:
        working = Path(temporary)
        snapshot = working / DATABASE_ARCHIVE_NAME
        archive_path = working / "customer.ftbackup"
        _snapshot_database(live, snapshot)
        _write_archive(snapshot, archive_path, kind="customer")
        payload = BytesIO(archive_path.read_bytes())
    filename = f"food-truck-backup-{_filename_timestamp()}.ftbackup"
    return payload, filename


def create_automatic_recovery_snapshot(
    live: sqlite3.Connection,
    paths: ApplicationDataPaths,
    reason: str,
    *,
    logger=None,
) -> Path:
    """Create a validated managed snapshot and retain the newest five."""
    filename = f"recovery-{_filename_timestamp()}.ftbackup"
    target = paths.safe_child(paths.automatic_recovery, filename)
    with tempfile.TemporaryDirectory(dir=paths.staging) as temporary:
        snapshot = Path(temporary) / DATABASE_ARCHIVE_NAME
        pending = Path(temporary) / filename
        _snapshot_database(
            live, snapshot, allow_older_supported=True
        )
        _write_archive(snapshot, pending, kind=reason)
        os.replace(pending, target)
    try:
        managed = sorted(
            paths.automatic_recovery.glob("recovery-*.ftbackup"),
            key=lambda item: item.stat().st_mtime_ns,
            reverse=True,
        )
        for old in managed[RECOVERY_RETENTION:]:
            old.unlink()
    except OSError as error:
        if logger:
            logger.warning("Automatic recovery retention cleanup failed: %s", error)
    return target


def _validate_archive_member(member: ZipInfo) -> None:
    if (
        member.filename not in {MANIFEST_ARCHIVE_NAME, DATABASE_ARCHIVE_NAME}
        or member.is_dir()
        or member.file_size > MAX_BACKUP_BYTES
        or (member.external_attr >> 16) & 0o170000 == 0o120000
    ):
        raise BackupValidationError("The backup archive contains unsafe files.")


def stage_restore_backup(
    payload: bytes,
    paths: ApplicationDataPaths,
    staging_directory: Path,
) -> Path:
    """Validate an uploaded archive and return its migrated staged database."""
    if not payload or len(payload) > MAX_BACKUP_BYTES:
        raise BackupValidationError("The backup file is empty or too large.")
    upload = staging_directory / "uploaded.ftbackup"
    upload.write_bytes(payload)
    try:
        with ZipFile(upload) as archive:
            members = archive.infolist()
            if {item.filename for item in members} != {
                MANIFEST_ARCHIVE_NAME,
                DATABASE_ARCHIVE_NAME,
            } or len(members) != 2:
                raise BackupValidationError(
                    "The backup archive has unexpected contents."
                )
            for member in members:
                _validate_archive_member(member)
            try:
                manifest = json.loads(archive.read(MANIFEST_ARCHIVE_NAME))
            except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
                raise BackupValidationError(
                    "The backup manifest is invalid."
                ) from error
            required = {
                "backup_format_version",
                "application_version",
                "database_schema_version",
                "created_at",
                "database_filename",
                "database_sha256",
            }
            if not isinstance(manifest, dict) or not required <= manifest.keys():
                raise BackupValidationError("The backup manifest is incomplete.")
            if (
                not isinstance(manifest["backup_format_version"], int)
                or not isinstance(manifest["application_version"], str)
                or not isinstance(manifest["database_schema_version"], int)
                or manifest["database_schema_version"] < 0
                or not isinstance(manifest["created_at"], str)
                or not manifest["created_at"]
                or not isinstance(manifest["database_filename"], str)
                or not isinstance(manifest["database_sha256"], str)
                or len(manifest["database_sha256"]) != 64
                or any(
                    character not in "0123456789abcdef"
                    for character in manifest["database_sha256"].lower()
                )
            ):
                raise BackupValidationError("The backup manifest is invalid.")
            if manifest["backup_format_version"] != BACKUP_FORMAT_VERSION:
                raise BackupValidationError(
                    "This backup format is not supported."
                )
            if manifest["database_filename"] != DATABASE_ARCHIVE_NAME:
                raise BackupValidationError("The backup manifest is invalid.")
            if manifest["database_schema_version"] > (
                LATEST_SUPPORTED_SCHEMA_VERSION
            ):
                raise BackupValidationError(
                    "This backup requires a newer application version."
                )
            database = staging_directory / "restored.sqlite"
            database.write_bytes(archive.read(DATABASE_ARCHIVE_NAME))
    except BadZipFile as error:
        raise BackupValidationError("The selected file is not a valid backup.") from error
    if _checksum(database) != manifest["database_sha256"]:
        raise BackupValidationError("The backup checksum does not match.")
    _validate_database(database, allow_migration=True)
    _validate_database(database)
    return database


def database_from_recovery_archive(archive_path: Path, destination: Path) -> None:
    with ZipFile(archive_path) as archive:
        destination.write_bytes(archive.read(DATABASE_ARCHIVE_NAME))
    _validate_database(destination)
