from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sqlite3
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from app import create_app
from app.data_paths import ApplicationDataPaths
from app.data_safety import (
    BACKUP_FORMAT_VERSION,
    BackupValidationError,
    create_automatic_recovery_snapshot,
    create_customer_backup,
    stage_restore_backup,
)
from app.database import get_database
from app.migrations import MIGRATIONS, Migration, migrate_database
from tests.test_dashboard_onboarding import valid_defaults


def isolated_app(root: Path):
    return create_app(
        {
            "DATA_ROOT": root,
            "ENFORCE_SETUP": False,
            "SECRET_KEY": "test",
            "TESTING": True,
            "PROPAGATE_EXCEPTIONS": False,
        }
    )


def backup_bytes(app) -> bytes:
    with app.app_context():
        payload, filename = create_customer_backup(
            get_database(), app.config["DATA_PATHS"]
        )
    assert filename.endswith(".ftbackup")
    return payload.getvalue()


def archive_parts(payload: bytes):
    with ZipFile(BytesIO(payload)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        database = archive.read("database.sqlite")
    return manifest, database


def test_backup_archive_manifest_checksum_and_complete_snapshot(tmp_path):
    app = isolated_app(tmp_path / "source")
    app.test_client().post("/defaults", data=valid_defaults())
    with app.app_context():
        before = get_database().execute(
            "SELECT business_name FROM business_defaults"
        ).fetchone()[0]
    payload = backup_bytes(app)
    manifest, database_bytes = archive_parts(payload)

    assert manifest["backup_format_version"] == BACKUP_FORMAT_VERSION
    assert manifest["database_schema_version"] == 1
    assert manifest["database_filename"] == "database.sqlite"
    assert manifest["database_sha256"] == sha256(database_bytes).hexdigest()
    snapshot = tmp_path / "snapshot.sqlite"
    snapshot.write_bytes(database_bytes)
    database = sqlite3.connect(snapshot)
    assert database.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    assert database.execute("PRAGMA foreign_key_check").fetchall() == []
    assert database.execute(
        "SELECT business_name FROM business_defaults"
    ).fetchone()[0] == "Roadside Kitchen"
    database.close()
    with app.app_context():
        assert get_database().execute(
            "SELECT business_name FROM business_defaults"
        ).fetchone()[0] == before


def test_customer_backup_route_downloads_without_temporary_files(tmp_path):
    app = isolated_app(tmp_path / "data")
    response = app.test_client().post("/data-safety/backup")

    assert response.status_code == 200
    assert response.headers["Content-Disposition"].endswith(".ftbackup")
    assert set(ZipFile(BytesIO(response.data)).namelist()) == {
        "manifest.json",
        "database.sqlite",
    }
    assert list(app.config["DATA_PATHS"].staging.iterdir()) == []


def test_failed_backup_returns_no_archive_and_cleans_temporary_files(
    tmp_path, monkeypatch
):
    app = isolated_app(tmp_path / "data")

    def fail_snapshot(live, destination, **kwargs):
        destination.write_bytes(b"partial")
        raise sqlite3.OperationalError("injected backup failure")

    monkeypatch.setattr("app.data_safety._snapshot_database", fail_snapshot)
    response = app.test_client().post("/data-safety/backup")

    assert response.status_code == 500
    assert "application/zip" not in response.headers.get("Content-Type", "")
    assert list(app.config["DATA_PATHS"].staging.iterdir()) == []


def test_restore_completely_replaces_data_and_clears_session(tmp_path):
    source = isolated_app(tmp_path / "source")
    source.test_client().post("/defaults", data=valid_defaults())
    payload = backup_bytes(source)

    target = isolated_app(tmp_path / "target")
    changed = valid_defaults()
    changed["business_name"] = "Replace Me"
    client = target.test_client()
    client.post("/defaults", data=changed)
    with client.session_transaction() as session:
        session["active_event_id"] = 999
        session["temporary_navigation"] = "stale"

    response = client.post(
        "/data-safety/restore",
        data={
            "confirm_restore": "yes",
            "backup_file": (BytesIO(payload), "saved.ftbackup"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    with target.app_context():
        database = get_database()
        assert database.execute(
            "SELECT business_name FROM business_defaults"
        ).fetchone()[0] == "Roadside Kitchen"
    with client.session_transaction() as session:
        assert "active_event_id" not in session
        assert "temporary_navigation" not in session
    recovery = list(
        target.config["DATA_PATHS"].automatic_recovery.glob(
            "recovery-*.ftbackup"
        )
    )
    assert len(recovery) == 1


def test_restore_aborts_when_recovery_snapshot_fails(
    tmp_path, monkeypatch
):
    source = isolated_app(tmp_path / "source")
    payload = backup_bytes(source)
    target = isolated_app(tmp_path / "target")
    client = target.test_client()
    client.post("/defaults", data=valid_defaults())
    before = target.config["DATA_PATHS"].database.read_bytes()
    monkeypatch.setattr(
        "app.routes.create_automatic_recovery_snapshot",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            OSError("injected snapshot failure")
        ),
    )

    response = client.post(
        "/data-safety/restore",
        data={
            "confirm_restore": "yes",
            "backup_file": (BytesIO(payload), "saved.ftbackup"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    assert target.config["DATA_PATHS"].database.read_bytes() == before


def test_atomic_replacement_failure_recovers_original_database(
    tmp_path, monkeypatch
):
    source = isolated_app(tmp_path / "source")
    payload = backup_bytes(source)
    target = isolated_app(tmp_path / "target")
    client = target.test_client()
    changed = valid_defaults()
    changed["business_name"] = "Original Live Data"
    client.post("/defaults", data=changed)
    original_replace = __import__("os").replace
    calls = 0

    def fail_first_replace(source_path, destination_path):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("injected replacement failure")
        return original_replace(source_path, destination_path)

    monkeypatch.setattr("app.routes.os.replace", fail_first_replace)
    response = client.post(
        "/data-safety/restore",
        data={
            "confirm_restore": "yes",
            "backup_file": (BytesIO(payload), "saved.ftbackup"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    with target.app_context():
        assert get_database().execute(
            "SELECT business_name FROM business_defaults"
        ).fetchone()[0] == "Original Live Data"


@pytest.mark.parametrize(
    "payload,error_text",
    (
        (b"not a zip", "not a valid backup"),
        (b"", "empty or too large"),
    ),
)
def test_invalid_restore_is_rejected_without_changing_live_data(
    tmp_path, payload, error_text
):
    app = isolated_app(tmp_path / "data")
    client = app.test_client()
    client.post("/defaults", data=valid_defaults())

    response = client.post(
        "/data-safety/restore",
        data={
            "confirm_restore": "yes",
            "backup_file": (BytesIO(payload), "invalid.ftbackup"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert error_text.encode() in response.data
    with app.app_context():
        assert get_database().execute(
            "SELECT business_name FROM business_defaults"
        ).fetchone()[0] == "Roadside Kitchen"


def repack(manifest: dict | None, database: bytes | None, extra=None) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        if manifest is not None:
            archive.writestr("manifest.json", json.dumps(manifest))
        if database is not None:
            archive.writestr("database.sqlite", database)
        if extra is not None:
            archive.writestr(extra, b"unsafe")
    return output.getvalue()


@pytest.mark.parametrize(
    "change,expected",
    (
        ("missing_manifest", "unexpected contents"),
        ("checksum", "checksum"),
        ("future", "newer application"),
        ("traversal", "unexpected contents"),
        ("extra", "unexpected contents"),
        ("missing_database", "unexpected contents"),
    ),
)
def test_archive_structure_manifest_and_checksum_validation(
    tmp_path, change, expected
):
    app = isolated_app(tmp_path / change)
    manifest, database = archive_parts(backup_bytes(app))
    extra = None
    if change == "missing_manifest":
        manifest = None
    elif change == "checksum":
        manifest["database_sha256"] = "0" * 64
    elif change == "future":
        manifest["database_schema_version"] = 999
    elif change == "traversal":
        extra = "../escape"
    elif change == "extra":
        extra = "notes.txt"
    elif change == "missing_database":
        database = None
    payload = repack(manifest, database, extra)

    with pytest.raises(BackupValidationError, match=expected):
        with pytest.MonkeyPatch.context():
            staging = app.config["DATA_PATHS"].staging / f"stage-{change}"
            staging.mkdir()
            stage_restore_backup(payload, app.config["DATA_PATHS"], staging)
    assert not (tmp_path / "escape").exists()


def test_corrupt_sqlite_and_foreign_key_damage_are_rejected(tmp_path):
    app = isolated_app(tmp_path / "data")
    manifest, database_bytes = archive_parts(backup_bytes(app))
    corrupt = b"SQLite format 3\x00" + b"broken"
    manifest["database_sha256"] = sha256(corrupt).hexdigest()
    with pytest.raises(BackupValidationError):
        staging = app.config["DATA_PATHS"].staging / "corrupt"
        staging.mkdir()
        stage_restore_backup(
            repack(manifest, corrupt), app.config["DATA_PATHS"], staging
        )

    database_path = tmp_path / "orphan.sqlite"
    database_path.write_bytes(database_bytes)
    database = sqlite3.connect(database_path)
    database.execute("PRAGMA foreign_keys=OFF")
    database.execute(
        """
        INSERT INTO event_scenario_additional_costs (
            event_scenario_id, position, cost_name, amount_cents
        ) VALUES (999, 0, 'Orphan', 1)
        """
    )
    database.commit()
    database.close()
    damaged = database_path.read_bytes()
    manifest["database_sha256"] = sha256(damaged).hexdigest()
    with pytest.raises(BackupValidationError, match="relationships"):
        staging = app.config["DATA_PATHS"].staging / "orphan"
        staging.mkdir()
        stage_restore_backup(
            repack(manifest, damaged), app.config["DATA_PATHS"], staging
        )


def test_unversioned_supported_backup_is_migrated_only_in_staging(tmp_path):
    app = isolated_app(tmp_path / "source")
    app.test_client().post("/defaults", data=valid_defaults())
    manifest, database_bytes = archive_parts(backup_bytes(app))
    older = tmp_path / "older.sqlite"
    older.write_bytes(database_bytes)
    database = sqlite3.connect(older)
    database.execute("DROP TRIGGER schema_migrations_no_update")
    database.execute("DROP TRIGGER schema_migrations_no_delete")
    database.execute("DROP TABLE schema_migrations")
    database.commit()
    database.close()
    older_bytes = older.read_bytes()
    manifest["database_schema_version"] = 0
    manifest["database_sha256"] = sha256(older_bytes).hexdigest()
    staging = app.config["DATA_PATHS"].staging / "older"
    staging.mkdir()

    restored = stage_restore_backup(
        repack(manifest, older_bytes), app.config["DATA_PATHS"], staging
    )

    database = sqlite3.connect(restored)
    assert database.execute(
        "SELECT version FROM schema_migrations"
    ).fetchall() == [(1,)]
    assert database.execute(
        "SELECT business_name FROM business_defaults"
    ).fetchone()[0] == "Roadside Kitchen"
    database.close()


def test_already_current_startup_creates_no_recovery_snapshot(tmp_path):
    root = tmp_path / "data"
    isolated_app(root)
    isolated_app(root)

    assert list((root / "automatic-recovery").iterdir()) == []


def test_automatic_recovery_retains_only_five_managed_files(tmp_path):
    app = isolated_app(tmp_path / "data")
    paths = app.config["DATA_PATHS"]
    unrelated = paths.automatic_recovery / "keep.txt"
    unrelated.write_text("keep", encoding="utf-8")
    with app.app_context():
        for _ in range(7):
            create_automatic_recovery_snapshot(
                get_database(), paths, "test"
            )

    assert len(list(paths.automatic_recovery.glob("recovery-*.ftbackup"))) == 5
    assert unrelated.read_text(encoding="utf-8") == "keep"


def test_recovery_cleanup_failure_does_not_invalidate_snapshot(
    tmp_path, monkeypatch
):
    app = isolated_app(tmp_path / "data")
    paths = app.config["DATA_PATHS"]
    with app.app_context():
        for _ in range(5):
            create_automatic_recovery_snapshot(
                get_database(), paths, "test"
            )
        original_unlink = Path.unlink

        def fail_managed_cleanup(path, *args, **kwargs):
            if path.name.startswith("recovery-"):
                raise OSError("injected cleanup failure")
            return original_unlink(path, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", fail_managed_cleanup)
        newest = create_automatic_recovery_snapshot(
            get_database(), paths, "test"
        )

    assert newest.exists()
    assert len(list(paths.automatic_recovery.glob("recovery-*.ftbackup"))) == 6


def test_pending_migration_creates_recovery_snapshot_first(tmp_path):
    app = isolated_app(tmp_path / "data")
    paths = app.config["DATA_PATHS"]

    def apply_v2(connection):
        connection.execute("CREATE TABLE migration_v2_test (id INTEGER)")

    migration_v2 = Migration(
        2,
        "test_future",
        apply_v2,
        lambda connection: connection.execute(
            "SELECT * FROM migration_v2_test"
        ).fetchall(),
    )
    with app.app_context():
        migrate_database(
            get_database(),
            migrations=(*MIGRATIONS, migration_v2),
            latest_version=2,
            before_migrations=lambda connection: (
                create_automatic_recovery_snapshot(
                    connection, paths, "pre-migration"
                )
            ),
        )
    assert len(list(paths.automatic_recovery.glob("recovery-*.ftbackup"))) == 1


def test_failed_pre_migration_snapshot_aborts_migration(tmp_path):
    app = isolated_app(tmp_path / "data")

    def apply_v2(connection):
        connection.execute("CREATE TABLE should_not_exist (id INTEGER)")

    migration_v2 = Migration(
        2, "test_future", apply_v2, lambda connection: None
    )
    with app.app_context(), pytest.raises(OSError):
        migrate_database(
            get_database(),
            migrations=(*MIGRATIONS, migration_v2),
            latest_version=2,
            before_migrations=lambda connection: (_ for _ in ()).throw(
                OSError("injected snapshot failure")
            ),
        )
    database = sqlite3.connect(app.config["DATA_PATHS"].database)
    assert database.execute(
        "SELECT 1 FROM sqlite_master WHERE name='should_not_exist'"
    ).fetchone() is None
    assert database.execute(
        "SELECT version FROM schema_migrations"
    ).fetchall() == [(1,)]
    database.close()


def test_business_defaults_child_interruption_rolls_back_parent(
    tmp_path, monkeypatch
):
    app = isolated_app(tmp_path / "data")
    client = app.test_client()
    client.post("/defaults", data=valid_defaults())
    changed = valid_defaults()
    changed["business_name"] = "Must Roll Back"
    changed["labor_rate"] = ["20", "25"]
    changed["labor_hours"] = ["8", "3"]
    calls = 0
    from app import database as database_module

    original_conversion = database_module._hours_to_minutes

    def fail_second_child(value):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise sqlite3.OperationalError("injected child interruption")
        return original_conversion(value)

    monkeypatch.setattr(
        database_module, "_hours_to_minutes", fail_second_child
    )
    response = client.post("/defaults", data=changed)

    assert response.status_code == 500
    with app.app_context():
        database = get_database()
        assert database.execute(
            "SELECT business_name FROM business_defaults"
        ).fetchone()[0] == "Roadside Kitchen"
        assert database.execute(
            "SELECT COUNT(*) FROM business_default_labor_entries"
        ).fetchone()[0] == 1


def test_data_paths_are_isolated_and_reject_unsafe_names(tmp_path):
    root = tmp_path / "customer-data"
    app = isolated_app(root)
    paths = app.config["DATA_PATHS"]

    assert paths.database == (root / "app.db").resolve()
    assert paths.staging.parent == root.resolve()
    assert paths.automatic_recovery.parent == root.resolve()
    with pytest.raises(ValueError):
        paths.safe_child(paths.staging, "../escape")


def test_damaged_startup_enters_restore_only_recovery_state(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    damaged = root / "app.db"
    damaged.write_bytes(b"damaged customer data")

    app = isolated_app(root)
    client = app.test_client()

    assert app.config["RECOVERY_MODE"] is True
    assert client.get("/").headers["Location"].endswith("/data-safety")
    page = client.get("/data-safety")
    assert b"customer data could not be opened" in page.data
    assert b"Restore backup" in page.data
    assert damaged.read_bytes() == b"damaged customer data"


def test_recovery_state_can_restore_and_preserves_damaged_file(tmp_path):
    source = isolated_app(tmp_path / "source")
    source.test_client().post("/defaults", data=valid_defaults())
    payload = backup_bytes(source)
    root = tmp_path / "damaged"
    root.mkdir()
    (root / "app.db").write_bytes(b"damaged customer data")
    app = isolated_app(root)

    response = app.test_client().post(
        "/data-safety/restore",
        data={
            "confirm_restore": "yes",
            "backup_file": (BytesIO(payload), "saved.ftbackup"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    assert app.config["RECOVERY_MODE"] is False
    with app.app_context():
        assert get_database().execute(
            "SELECT business_name FROM business_defaults"
        ).fetchone()[0] == "Roadside Kitchen"
    damaged_files = list(
        app.config["DATA_PATHS"].automatic_recovery.glob("damaged-*.sqlite")
    )
    assert len(damaged_files) == 1
    assert damaged_files[0].read_bytes() == b"damaged customer data"
