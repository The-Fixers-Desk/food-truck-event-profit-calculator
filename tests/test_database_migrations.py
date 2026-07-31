import sqlite3

import pytest

from app import create_app
from app.database import (
    apply_business_defaults_schema,
    apply_event_analysis_schema,
)
from app.migrations import (
    DatabaseMigrationError,
    Migration,
    migrate_database,
)


def connect(path=":memory:"):
    database = sqlite3.connect(path)
    database.execute("PRAGMA foreign_keys = ON")
    return database


def ledger_rows(database):
    return database.execute(
        "SELECT version, name, applied_at FROM schema_migrations"
    ).fetchall()


def current_unversioned_database(path):
    database = connect(path)
    apply_business_defaults_schema(database)
    apply_event_analysis_schema(database)
    return database


def insert_customer_data(database):
    database.execute(
        """
        INSERT INTO business_defaults (
            id, business_name, average_order_sale_amount_cents,
            food_cost_method, food_cost_percentage_basis_points,
            card_sales_basis_points, card_processing_basis_points,
            profit_target_type, minimum_profit_amount_cents,
            created_at, updated_at
        ) VALUES (
            1, 'Keep Me', 1750, 'sales_percentage', 3000,
            8000, 290, 'profit_amount', 40000,
            '2025-01-01 10:00:00', '2025-01-02 11:00:00'
        )
        """
    )
    database.executemany(
        """
        INSERT INTO business_default_labor_entries (
            id, business_defaults_id, position,
            hourly_rate_cents, total_paid_minutes
        ) VALUES (?, 1, ?, ?, ?)
        """,
        ((41, 0, 2000, 480), (42, 1, 2500, 120)),
    )
    event_id = database.execute(
        """
        INSERT INTO events (
            id, event_name, event_date, start_time_minutes, location,
            created_at, updated_at
        ) VALUES (
            51, 'Saved Fair', '2026-09-01', 600, 'Park',
            '2025-02-01 10:00:00', '2025-02-02 11:00:00'
        )
        """
    ).lastrowid
    scenario_id = database.execute(
        """
        INSERT INTO event_scenarios (
            id, event_id, scenario_name, estimated_attendance,
            other_competing_food_vendors, expected_food_buyer_basis_points,
            event_protection, weather_outlook, revenue_method,
            average_order_sale_amount_cents, food_cost_method,
            food_cost_percentage_basis_points, card_sales_basis_points,
            card_processing_basis_points, vendor_or_booking_fee_cents,
            profit_target_type, minimum_profit_amount_cents,
            created_at, updated_at
        ) VALUES (
            61, ?, 'Original estimate', 500, 2, 2000,
            'fully_outdoors', 'favorable', 'attendance',
            1750, 'sales_percentage', 3000, 8000, 290, 0,
            'profit_amount', 40000,
            '2025-03-01 10:00:00', '2025-03-02 11:00:00'
        )
        """,
        (event_id,),
    ).lastrowid
    database.executemany(
        """
        INSERT INTO event_scenario_employee_labor_entries (
            id, event_scenario_id, position,
            hourly_rate_cents, total_paid_minutes
        ) VALUES (?, ?, ?, ?, ?)
        """,
        ((71, scenario_id, 0, 2000, 480), (72, scenario_id, 1, 2500, 120)),
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
    database.commit()


def snapshot(database):
    return {
        table: database.execute(
            f'SELECT * FROM "{table}" ORDER BY id'
        ).fetchall()
        for table in (
            "business_defaults",
            "business_default_labor_entries",
            "events",
            "event_scenarios",
            "event_scenario_employee_labor_entries",
            "event_scenario_additional_costs",
        )
    }


def test_fresh_database_reaches_complete_version_1(database_path):
    app = create_app({"DATABASE": database_path, "TESTING": True})
    with app.app_context():
        database = connect(database_path)
        assert ledger_rows(database)[0][:2] == (1, "version_1_baseline")
        tables = {
            row[0]
            for row in database.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert {
            "schema_migrations",
            "business_defaults",
            "business_default_labor_entries",
            "events",
            "event_scenarios",
            "event_scenario_employee_labor_entries",
            "event_scenario_additional_costs",
        } <= tables


def test_current_restart_does_not_rewrite_migration(database_path):
    create_app({"DATABASE": database_path, "TESTING": True})
    database = connect(database_path)
    before = ledger_rows(database)
    database.close()

    create_app({"DATABASE": database_path, "TESTING": True})
    database = connect(database_path)
    assert ledger_rows(database) == before
    assert database.total_changes == 0


def test_migration_ledger_records_are_immutable(database_path):
    create_app({"DATABASE": database_path, "TESTING": True})
    database = connect(database_path)

    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        database.execute(
            "UPDATE schema_migrations SET name='changed' WHERE version=1"
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        database.execute("DELETE FROM schema_migrations WHERE version=1")


def test_compatible_unversioned_database_is_adopted_without_data_changes(
    database_path,
):
    database = current_unversioned_database(database_path)
    insert_customer_data(database)
    before = snapshot(database)
    database.close()

    create_app({"DATABASE": database_path, "TESTING": True})
    database = connect(database_path)

    assert ledger_rows(database)[0][:2] == (1, "version_1_baseline")
    assert snapshot(database) == before


@pytest.mark.parametrize(
    "schema",
    (
        "CREATE TABLE business_defaults (id INTEGER PRIMARY KEY)",
        "CREATE TABLE events (id TEXT PRIMARY KEY)",
    ),
)
def test_incomplete_or_conflicting_unversioned_database_is_rejected(
    database_path, schema
):
    database = connect(database_path)
    database.execute(schema)
    database.commit()
    database.close()

    with pytest.raises(DatabaseMigrationError):
        create_app({"DATABASE": database_path, "TESTING": True})

    database = connect(database_path)
    assert "schema_migrations" not in {
        row[0]
        for row in database.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }


def test_foreign_key_damage_prevents_unversioned_adoption(database_path):
    database = current_unversioned_database(database_path)
    database.execute("PRAGMA foreign_keys = OFF")
    database.execute(
        """
        INSERT INTO event_scenario_additional_costs (
            event_scenario_id, position, cost_name, amount_cents
        ) VALUES (999, 0, 'Orphan', 100)
        """
    )
    database.commit()
    database.close()

    with pytest.raises(DatabaseMigrationError):
        create_app({"DATABASE": database_path, "TESTING": True})


def test_integrity_check_failure_prevents_unversioned_adoption(database_path):
    database = current_unversioned_database(database_path)
    database.execute("PRAGMA ignore_check_constraints = ON")
    database.execute(
        """
        INSERT INTO events (
            event_name, event_date, start_time_minutes, location
        ) VALUES ('Broken', '2026-01-01', -1, 'Park')
        """
    )
    database.commit()
    database.close()

    with pytest.raises(DatabaseMigrationError):
        create_app({"DATABASE": database_path, "TESTING": True})


def test_future_version_is_rejected_without_changes(database_path):
    create_app({"DATABASE": database_path, "TESTING": True})
    database = connect(database_path)
    database.execute("DROP TRIGGER schema_migrations_no_update")
    database.execute("DROP TRIGGER schema_migrations_no_delete")
    database.execute(
        """
        INSERT INTO schema_migrations (version, name)
        VALUES (2, 'future_release')
        """
    )
    database.commit()
    before = database.execute(
        "SELECT * FROM schema_migrations ORDER BY version"
    ).fetchall()
    database.close()

    with pytest.raises(DatabaseMigrationError, match="newer"):
        create_app({"DATABASE": database_path, "TESTING": True})

    database = connect(database_path)
    assert database.execute(
        "SELECT * FROM schema_migrations ORDER BY version"
    ).fetchall() == before


def test_conflicting_migration_ledger_is_rejected(database_path):
    database = connect(database_path)
    database.execute("CREATE TABLE schema_migrations (version TEXT)")
    database.commit()
    database.close()

    with pytest.raises(DatabaseMigrationError, match="ledger"):
        create_app({"DATABASE": database_path, "TESTING": True})


def test_future_migrations_run_in_order_and_stop_with_atomic_rollback():
    database = connect()
    calls = []

    def first(connection):
        calls.append(1)
        connection.execute("CREATE TABLE baseline (id INTEGER)")

    def second(connection):
        calls.append(2)
        connection.execute("CREATE TABLE migration_v2 (id INTEGER)")

    def third(connection):
        calls.append(3)
        connection.execute("CREATE TABLE migration_v3 (id INTEGER)")
        connection.execute("INSERT INTO migration_v3 VALUES (1)")
        raise sqlite3.OperationalError("test failure")

    def fourth(connection):
        calls.append(4)

    def verify_table(name):
        def verify(connection):
            assert connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (name,),
            ).fetchone()
        return verify

    migrations = (
        Migration(1, "baseline", first, verify_table("baseline")),
        Migration(2, "second", second, verify_table("migration_v2")),
        Migration(3, "third", third, verify_table("migration_v3")),
        Migration(4, "never", fourth, lambda connection: None),
    )

    with pytest.raises(DatabaseMigrationError):
        migrate_database(database, migrations=migrations, latest_version=4)

    assert calls == [1, 2, 3]
    assert database.execute(
        "SELECT version FROM schema_migrations ORDER BY version"
    ).fetchall() == [(1,), (2,)]
    assert database.execute(
        "SELECT 1 FROM sqlite_master WHERE name='migration_v3'"
    ).fetchone() is None


def test_migration_logging_reports_detection_and_completion(
    database_path, caplog
):
    caplog.set_level("INFO")

    create_app({"DATABASE": database_path, "TESTING": True})

    messages = [record.getMessage() for record in caplog.records]
    assert "Detected empty database at schema version 0." in messages
    assert any("Beginning database migration 1" in item for item in messages)
    assert any("Completed database migration 1" in item for item in messages)


def test_unexpected_temporary_table_causes_safe_migration_failure():
    database = connect()

    def baseline(connection):
        connection.execute("CREATE TABLE baseline (id INTEGER)")

    def verify_baseline(connection):
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name='baseline'"
        ).fetchone()

    def reconstruct(connection):
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name='baseline_migration_v2'"
        ).fetchone():
            raise DatabaseMigrationError("temporary table conflict")
        connection.execute("CREATE TABLE baseline_migration_v2 (id INTEGER)")

    migrations = (
        Migration(1, "baseline", baseline, verify_baseline),
        Migration(2, "reconstruct", reconstruct, lambda connection: None),
    )
    migrate_database(database, migrations=migrations[:1], latest_version=1)
    database.execute("CREATE TABLE baseline_migration_v2 (id INTEGER)")

    with pytest.raises(DatabaseMigrationError):
        migrate_database(database, migrations=migrations, latest_version=2)

    assert database.execute(
        "SELECT version FROM schema_migrations"
    ).fetchall() == [(1,)]
