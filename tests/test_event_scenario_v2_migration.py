import sqlite3

import pytest

import app.migrations as migration_module
from app import create_app
from app.database import (
    apply_business_defaults_schema,
    apply_event_analysis_schema,
)
from app.migrations import (
    DatabaseMigrationError,
    migrate_database,
    verify_version_1,
    verify_version_2,
)
from tests.test_complete_event_inputs_workflow import complete_event_inputs
from tests.test_event_analysis_schema import (
    insert_event,
    insert_scenario,
    valid_scenario_values,
)


def mixed_version_1_database(path, *, scenario_state="empty"):
    database = sqlite3.connect(path)
    database.execute("PRAGMA foreign_keys = ON")
    apply_business_defaults_schema(database)
    apply_event_analysis_schema(database)
    scenario_id = None
    if scenario_state != "empty":
        event_id = insert_event(database)
        scenario_id = insert_scenario(
            database, valid_scenario_values(event_id)
        )
        database.executemany(
            """
            INSERT INTO event_scenario_employee_labor_entries (
                id, event_scenario_id, position,
                hourly_rate_cents, total_paid_minutes
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ((71, scenario_id, 0, 2000, 480),
             (72, scenario_id, 1, 2500, 120)),
        )
        database.executemany(
            """
            INSERT INTO event_scenario_additional_costs (
                id, event_scenario_id, position, cost_name, amount_cents
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ((81, scenario_id, 0, "Ice", 3000),
             (82, scenario_id, 1, "Security", 9000)),
        )
    database.execute(
        """
        ALTER TABLE event_scenarios
        RENAME COLUMN other_competing_food_vendors
        TO competing_food_vendors
        """
    )
    database.execute(
        """
        ALTER TABLE event_scenarios
        RENAME COLUMN expected_food_buyer_basis_points
        TO expected_buyer_basis_points
        """
    )
    apply_event_analysis_schema(database)
    if scenario_state == "compatible":
        database.execute(
            """
            UPDATE event_scenarios
            SET other_competing_food_vendors = 5,
                expected_food_buyer_basis_points = 1000,
                revenue_method = 'manual_sales',
                average_order_sale_amount_cents = NULL,
                expected_sales_amount_cents = 500000,
                manual_average_order_sale_amount_cents = 1650
            WHERE id = ?
            """,
            (scenario_id,),
        )
    database.executescript(
        """
        CREATE TABLE schema_migrations (
            version INTEGER PRIMARY KEY CHECK (version > 0),
            name TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TRIGGER schema_migrations_no_update
        BEFORE UPDATE ON schema_migrations BEGIN
            SELECT RAISE(ABORT, 'schema migration records are immutable');
        END;
        CREATE TRIGGER schema_migrations_no_delete
        BEFORE DELETE ON schema_migrations BEGIN
            SELECT RAISE(ABORT, 'schema migration records are immutable');
        END;
        INSERT INTO schema_migrations (version, name)
        VALUES (1, 'version_1_baseline');
        """
    )
    database.commit()
    return database, scenario_id


def table_columns(database):
    return {
        row[1]
        for row in database.execute("PRAGMA table_info(event_scenarios)")
    }


def test_mixed_schema_reproduces_current_insert_failure(database_path):
    database, _ = mixed_version_1_database(database_path)

    with pytest.raises(
        sqlite3.IntegrityError,
        match="event_scenarios.competing_food_vendors",
    ):
        event_id = insert_event(database)
        insert_scenario(database, valid_scenario_values(event_id))

    database.rollback()
    assert database.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_empty_mixed_schema_migrates_and_complete_submission_saves(
    database_path,
):
    database, _ = mixed_version_1_database(database_path)
    database.close()

    app = create_app(
        {
            "DATABASE": database_path,
            "DATA_ROOT": database_path.parent,
            "TESTING": True,
            "ENFORCE_SETUP": False,
        }
    )
    response = app.test_client().post(
        "/events/new", data=complete_event_inputs()
    )

    assert response.status_code == 200
    assert b"Event Analysis" in response.data
    database = sqlite3.connect(database_path)
    columns = table_columns(database)
    assert "competing_food_vendors" not in columns
    assert "expected_buyer_basis_points" not in columns
    assert {
        "other_competing_food_vendors",
        "expected_food_buyer_basis_points",
    } <= columns
    assert database.execute(
        "SELECT version FROM schema_migrations ORDER BY version"
    ).fetchall() == [(1,), (2,), (3,)]
    assert database.execute(
        """
        SELECT other_competing_food_vendors,
               expected_food_buyer_basis_points
        FROM event_scenarios
        """
    ).fetchone() == (5, 1000)
    assert database.execute(
        """
        SELECT position, hourly_rate_cents, total_paid_minutes
        FROM event_scenario_employee_labor_entries ORDER BY position
        """
    ).fetchall() == [(0, 2000, 600), (1, 2500, 240)]
    assert database.execute(
        """
        SELECT position, cost_name, amount_cents
        FROM event_scenario_additional_costs ORDER BY position
        """
    ).fetchall()[:2] == [(0, "Ice", 4000), (1, "Extra propane", 6000)]
    assert database.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    assert database.execute("PRAGMA foreign_key_check").fetchall() == []
    assert len(list(
        app.config["DATA_PATHS"].automatic_recovery.glob(
            "recovery-*.ftbackup"
        )
    )) == 1


def test_compatible_existing_scenario_and_children_are_preserved(
    database_path,
):
    database, scenario_id = mixed_version_1_database(
        database_path, scenario_state="compatible"
    )
    before = database.execute(
        "SELECT * FROM event_scenarios WHERE id = ?", (scenario_id,)
    ).fetchone()
    before_names = [item[1] for item in database.execute(
        "PRAGMA table_info(event_scenarios)"
    ).fetchall()]
    preserved = {
        name: before[index]
        for index, name in enumerate(before_names)
        if name not in {
            "competing_food_vendors",
            "expected_buyer_basis_points",
        }
    }
    database.close()

    create_app(
        {
            "DATABASE": database_path,
            "DATA_ROOT": database_path.parent,
            "TESTING": True,
        }
    )
    database = sqlite3.connect(database_path)
    after = database.execute(
        "SELECT * FROM event_scenarios WHERE id = ?", (scenario_id,)
    ).fetchone()
    after_names = [item[1] for item in database.execute(
        "PRAGMA table_info(event_scenarios)"
    ).fetchall()]
    assert dict(zip(after_names, after)) == preserved
    assert database.execute(
        """
        SELECT id, event_scenario_id, position
        FROM event_scenario_employee_labor_entries ORDER BY position
        """
    ).fetchall() == [(71, scenario_id, 0), (72, scenario_id, 1)]
    assert database.execute(
        """
        SELECT id, event_scenario_id, position
        FROM event_scenario_additional_costs ORDER BY position
        """
    ).fetchall() == [(81, scenario_id, 0), (82, scenario_id, 1)]


def test_legacy_only_scenario_refuses_migration_without_changes(database_path):
    database, scenario_id = mixed_version_1_database(
        database_path, scenario_state="legacy_only"
    )
    before_sql = database.execute(
        "SELECT sql FROM sqlite_master WHERE name='event_scenarios'"
    ).fetchone()[0]
    before = database.execute(
        "SELECT * FROM event_scenarios WHERE id = ?", (scenario_id,)
    ).fetchone()
    database.close()

    app = create_app(
        {
            "DATABASE": database_path,
            "DATA_ROOT": database_path.parent,
            "TESTING": True,
        }
    )

    assert app.config["RECOVERY_MODE"] is True
    database = sqlite3.connect(database_path)
    assert database.execute(
        "SELECT version FROM schema_migrations"
    ).fetchall() == [(1,)]
    assert database.execute(
        "SELECT sql FROM sqlite_master WHERE name='event_scenarios'"
    ).fetchone()[0] == before_sql
    assert database.execute(
        "SELECT * FROM event_scenarios WHERE id = ?", (scenario_id,)
    ).fetchone() == before
    assert database.execute("PRAGMA foreign_key_check").fetchall() == []


def test_reconstruction_failure_rolls_back_and_leaves_no_artifacts(
    database_path, monkeypatch
):
    database, _ = mixed_version_1_database(database_path)
    original = migration_module._event_schema_statement
    calls = 0

    def fail_during_table_creation(prefix):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise sqlite3.OperationalError("injected reconstruction failure")
        return original(prefix)

    monkeypatch.setattr(
        migration_module, "_event_schema_statement", fail_during_table_creation
    )
    with pytest.raises(DatabaseMigrationError):
        migrate_database(database)

    assert "competing_food_vendors" in table_columns(database)
    assert database.execute(
        "SELECT version FROM schema_migrations"
    ).fetchall() == [(1,)]
    assert database.execute(
        """
        SELECT name FROM sqlite_master
        WHERE name LIKE '%migration_v2_target'
        """
    ).fetchall() == []


def test_unexpected_version_2_temporary_table_aborts_safely(database_path):
    database, _ = mixed_version_1_database(database_path)
    database.execute(
        """
        CREATE TABLE event_scenarios_migration_v2_target (
            id INTEGER PRIMARY KEY
        )
        """
    )
    database.commit()

    with pytest.raises(DatabaseMigrationError):
        migrate_database(database)

    assert "competing_food_vendors" in table_columns(database)
    assert database.execute(
        "SELECT version FROM schema_migrations"
    ).fetchall() == [(1,)]
    assert database.execute(
        """
        SELECT COUNT(*) FROM event_scenarios_migration_v2_target
        """
    ).fetchone()[0] == 0


def test_schema_verification_rejects_mixed_and_accepts_version_2(
    database_path,
):
    database, _ = mixed_version_1_database(database_path)
    with pytest.raises(DatabaseMigrationError, match="incompatible_extras"):
        verify_version_1(database)
    migrate_database(database)
    verify_version_2(database)


def test_current_version_1_schema_is_stamped_without_rebuild(database_path):
    database = sqlite3.connect(database_path)
    database.execute("PRAGMA foreign_keys = ON")
    apply_business_defaults_schema(database)
    apply_event_analysis_schema(database)
    database.executescript(
        """
        CREATE TABLE schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO schema_migrations (version, name)
        VALUES (1, 'version_1_baseline');
        """
    )
    rootpage = database.execute(
        "SELECT rootpage FROM sqlite_master WHERE name='event_scenarios'"
    ).fetchone()[0]

    migrate_database(database)

    assert database.execute(
        "SELECT rootpage FROM sqlite_master WHERE name='event_scenarios'"
    ).fetchone()[0] == rootpage
    assert database.execute(
        "SELECT version FROM schema_migrations ORDER BY version"
    ).fetchall() == [(1,), (2,), (3,)]
