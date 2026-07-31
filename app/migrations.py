"""Versioned, transactional SQLite schema migrations."""

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Callable, Iterable


LATEST_SUPPORTED_SCHEMA_VERSION = 1
SCHEMA_DIRECTORY = Path(__file__).resolve().parent / "schema"


class DatabaseMigrationError(RuntimeError):
    """Raised when a database cannot be migrated or safely adopted."""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    apply: Callable[[sqlite3.Connection], None]
    verify: Callable[[sqlite3.Connection], None]


EXPECTED_COLUMNS = {
    "business_defaults": {
        "id": "INTEGER",
        "business_name": "TEXT",
        "average_order_sale_amount_cents": "INTEGER",
        "food_cost_method": "TEXT",
        "average_food_cost_per_order_cents": "INTEGER",
        "food_cost_percentage_basis_points": "INTEGER",
        "typical_food_cost_total_cents": "INTEGER",
        "card_sales_basis_points": "INTEGER",
        "card_processing_basis_points": "INTEGER",
        "default_travel_cost_cents": "INTEGER",
        "default_owner_labor_pay_cents": "INTEGER",
        "profit_target_type": "TEXT",
        "minimum_profit_amount_cents": "INTEGER",
        "minimum_profit_margin_basis_points": "INTEGER",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    },
    "business_default_labor_entries": {
        "id": "INTEGER",
        "business_defaults_id": "INTEGER",
        "position": "INTEGER",
        "hourly_rate_cents": "INTEGER",
        "total_paid_minutes": "INTEGER",
    },
    "events": {
        "id": "INTEGER",
        "event_name": "TEXT",
        "event_date": "TEXT",
        "start_time_minutes": "INTEGER",
        "location": "TEXT",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    },
    "event_scenarios": {
        "id": "INTEGER",
        "event_id": "INTEGER",
        "scenario_name": "TEXT",
        "notes": "TEXT",
        "estimated_attendance": "INTEGER",
        "other_competing_food_vendors": "INTEGER",
        "expected_food_buyer_basis_points": "INTEGER",
        "event_protection": "TEXT",
        "weather_outlook": "TEXT",
        "custom_weather_reduction_basis_points": "INTEGER",
        "revenue_method": "TEXT",
        "average_order_sale_amount_cents": "INTEGER",
        "expected_sales_amount_cents": "INTEGER",
        "manual_average_order_sale_amount_cents": "INTEGER",
        "food_cost_method": "TEXT",
        "average_food_cost_per_order_cents": "INTEGER",
        "food_cost_percentage_basis_points": "INTEGER",
        "manual_food_cost_total_cents": "INTEGER",
        "card_sales_basis_points": "INTEGER",
        "card_processing_basis_points": "INTEGER",
        "fixed_card_processing_fee_cents": "INTEGER",
        "vendor_or_booking_fee_cents": "INTEGER",
        "organizer_commission_basis_points": "INTEGER",
        "owner_labor_pay_cents": "INTEGER",
        "travel_cost_cents": "INTEGER",
        "profit_target_type": "TEXT",
        "minimum_profit_amount_cents": "INTEGER",
        "minimum_profit_margin_basis_points": "INTEGER",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    },
    "event_scenario_employee_labor_entries": {
        "id": "INTEGER",
        "event_scenario_id": "INTEGER",
        "position": "INTEGER",
        "hourly_rate_cents": "INTEGER",
        "total_paid_minutes": "INTEGER",
    },
    "event_scenario_additional_costs": {
        "id": "INTEGER",
        "event_scenario_id": "INTEGER",
        "position": "INTEGER",
        "cost_name": "TEXT",
        "amount_cents": "INTEGER",
    },
}

EXPECTED_INDEXES = {
    "event_scenarios_event_id_index",
    "event_scenario_name_unique",
}

EXPECTED_FOREIGN_KEYS = {
    ("business_default_labor_entries", "business_defaults_id",
     "business_defaults", "id", "CASCADE"),
    ("event_scenarios", "event_id", "events", "id", "CASCADE"),
    ("event_scenario_employee_labor_entries", "event_scenario_id",
     "event_scenarios", "id", "CASCADE"),
    ("event_scenario_additional_costs", "event_scenario_id",
     "event_scenarios", "id", "CASCADE"),
}


def _execute_sql_file(connection: sqlite3.Connection, path: Path) -> None:
    statement = ""
    for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            if statement.strip():
                connection.execute(statement)
            statement = ""
    if statement.strip():
        raise DatabaseMigrationError(f"Incomplete SQL statement in {path.name}.")


def _apply_version_1(connection: sqlite3.Connection) -> None:
    _execute_sql_file(connection, SCHEMA_DIRECTORY / "business_defaults.sql")
    _execute_sql_file(connection, SCHEMA_DIRECTORY / "event_analysis.sql")


def _is_known_pre_v1_defaults_schema(
    connection: sqlite3.Connection,
    tables: set[str],
) -> bool:
    if tables != {
        "business_defaults",
        "business_default_labor_entries",
    }:
        return False
    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(business_defaults)"
        )
    }
    return {
        "id",
        "business_name",
        "average_order_sale_amount_cents",
        "food_cost_basis_points",
        "card_sales_basis_points",
        "card_processing_basis_points",
        "default_travel_cost_cents",
        "default_owner_labor_pay_cents",
        "profit_target_type",
        "minimum_profit_amount_cents",
        "minimum_profit_margin_basis_points",
        "created_at",
        "updated_at",
    } <= columns


def _upgrade_known_pre_v1_defaults(
    connection: sqlite3.Connection,
) -> None:
    """Upgrade the last recognized pre-ledger Defaults-only schema."""
    defaults_temp = "business_defaults_migration_v1_legacy_percentage"
    labor_temp = "business_default_labor_migration_v1_legacy_percentage"
    for name in (defaults_temp, labor_temp):
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone():
            raise DatabaseMigrationError(
                f"Unexpected migration temporary table: {name}"
            )
    defaults_count = connection.execute(
        "SELECT COUNT(*) FROM business_defaults"
    ).fetchone()[0]
    labor_count = connection.execute(
        "SELECT COUNT(*) FROM business_default_labor_entries"
    ).fetchone()[0]
    connection.execute(
        f'ALTER TABLE business_default_labor_entries RENAME TO "{labor_temp}"'
    )
    connection.execute(
        f'ALTER TABLE business_defaults RENAME TO "{defaults_temp}"'
    )
    _apply_version_1(connection)
    connection.execute(
        f"""
        INSERT INTO business_defaults (
            id, business_name, average_order_sale_amount_cents,
            food_cost_method, food_cost_percentage_basis_points,
            card_sales_basis_points, card_processing_basis_points,
            default_travel_cost_cents, default_owner_labor_pay_cents,
            profit_target_type, minimum_profit_amount_cents,
            minimum_profit_margin_basis_points, created_at, updated_at
        )
        SELECT
            id, business_name, average_order_sale_amount_cents,
            'sales_percentage', food_cost_basis_points,
            card_sales_basis_points, card_processing_basis_points,
            default_travel_cost_cents, default_owner_labor_pay_cents,
            profit_target_type, minimum_profit_amount_cents,
            minimum_profit_margin_basis_points, created_at, updated_at
        FROM "{defaults_temp}"
        """
    )
    connection.execute(
        f"""
        INSERT INTO business_default_labor_entries (
            id, business_defaults_id, position,
            hourly_rate_cents, total_paid_minutes
        )
        SELECT
            id, business_defaults_id, position,
            hourly_rate_cents, total_paid_minutes
        FROM "{labor_temp}"
        ORDER BY position
        """
    )
    if connection.execute(
        "SELECT COUNT(*) FROM business_defaults"
    ).fetchone()[0] != defaults_count:
        raise DatabaseMigrationError("Defaults row-count verification failed.")
    if connection.execute(
        "SELECT COUNT(*) FROM business_default_labor_entries"
    ).fetchone()[0] != labor_count:
        raise DatabaseMigrationError("Labor row-count verification failed.")
    connection.execute(f'DROP TABLE "{labor_temp}"')
    connection.execute(f'DROP TABLE "{defaults_temp}"')


def verify_version_1(connection: sqlite3.Connection) -> None:
    """Verify that the complete established Version 1 schema is compatible."""
    tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """
        )
    }
    expected_tables = set(EXPECTED_COLUMNS)
    missing = expected_tables - tables
    unexpected = tables - expected_tables - {"schema_migrations"}
    if missing or unexpected:
        raise DatabaseMigrationError(
            "Version 1 table mismatch: "
            f"missing={sorted(missing)}, unexpected={sorted(unexpected)}"
        )

    for table, expected in EXPECTED_COLUMNS.items():
        actual = {
            row[1]: (row[2] or "").upper()
            for row in connection.execute(f'PRAGMA table_info("{table}")')
        }
        missing_columns = set(expected) - set(actual)
        wrong_types = {
            name
            for name, column_type in expected.items()
            if name in actual and actual[name] != column_type
        }
        if missing_columns or wrong_types:
            raise DatabaseMigrationError(
                f"Incompatible columns in {table}: "
                f"missing={sorted(missing_columns)}, "
                f"wrong_types={sorted(wrong_types)}"
            )

    indexes = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        )
    }
    if not EXPECTED_INDEXES <= indexes:
        raise DatabaseMigrationError(
            f"Missing Version 1 indexes: {sorted(EXPECTED_INDEXES - indexes)}"
        )

    foreign_keys = set()
    for table in EXPECTED_COLUMNS:
        for row in connection.execute(f'PRAGMA foreign_key_list("{table}")'):
            foreign_keys.add((table, row[3], row[2], row[4], row[6]))
    if not EXPECTED_FOREIGN_KEYS <= foreign_keys:
        raise DatabaseMigrationError("Version 1 foreign keys are incomplete.")

    integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
    if integrity != "ok":
        raise DatabaseMigrationError(f"SQLite quick check failed: {integrity}")
    foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_errors:
        raise DatabaseMigrationError("SQLite foreign-key check failed.")


MIGRATIONS = (
    Migration(1, "version_1_baseline", _apply_version_1, verify_version_1),
)


def _create_ledger(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE schema_migrations (
            version INTEGER PRIMARY KEY CHECK (version > 0),
            name TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TRIGGER schema_migrations_no_update
        BEFORE UPDATE ON schema_migrations
        BEGIN
            SELECT RAISE(ABORT, 'schema migration records are immutable');
        END
        """
    )
    connection.execute(
        """
        CREATE TRIGGER schema_migrations_no_delete
        BEFORE DELETE ON schema_migrations
        BEGIN
            SELECT RAISE(ABORT, 'schema migration records are immutable');
        END
        """
    )


def _user_tables(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """
        )
    }


def _verify_ledger(connection: sqlite3.Connection) -> None:
    columns = {
        row[1]: (row[2] or "").upper()
        for row in connection.execute(
            "PRAGMA table_info(schema_migrations)"
        )
    }
    if columns != {
        "version": "INTEGER",
        "name": "TEXT",
        "applied_at": "TEXT",
    }:
        raise DatabaseMigrationError(
            "The schema migration ledger is incompatible."
        )


def _recorded_migrations(
    connection: sqlite3.Connection,
) -> list[tuple[int, str]]:
    rows = connection.execute(
        "SELECT version, name FROM schema_migrations ORDER BY version"
    ).fetchall()
    recorded = [(row[0], row[1]) for row in rows]
    versions = [item[0] for item in recorded]
    if versions != list(range(1, (versions[-1] if versions else 0) + 1)):
        raise DatabaseMigrationError(
            "Schema migration versions are not sequential."
        )
    return recorded


def migrate_database(
    connection: sqlite3.Connection,
    *,
    migrations: Iterable[Migration] = MIGRATIONS,
    latest_version: int = LATEST_SUPPORTED_SCHEMA_VERSION,
    logger=None,
    before_migrations: Callable[[sqlite3.Connection], None] | None = None,
) -> None:
    """Create, adopt, or upgrade a database to the supported schema."""
    registry = tuple(migrations)
    if [item.version for item in registry] != list(
        range(1, latest_version + 1)
    ):
        raise DatabaseMigrationError("Migration registry is not sequential.")

    tables = _user_tables(connection)
    if "schema_migrations" not in tables:
        if tables:
            if logger:
                logger.info("Detected unversioned database; verifying Version 1.")
            try:
                if (
                    before_migrations is not None
                    and _is_known_pre_v1_defaults_schema(connection, tables)
                ):
                    before_migrations(connection)
                connection.execute("BEGIN IMMEDIATE")
                if _is_known_pre_v1_defaults_schema(connection, tables):
                    if logger:
                        logger.info(
                            "Upgrading recognized pre-Version 1 Defaults schema."
                        )
                    _upgrade_known_pre_v1_defaults(connection)
                registry[0].verify(connection)
                _create_ledger(connection)
                connection.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (registry[0].version, registry[0].name),
                )
                connection.commit()
            except Exception as error:
                connection.rollback()
                if logger:
                    logger.error("Unversioned database adoption failed: %s", error)
                raise DatabaseMigrationError(
                    "The existing database is not compatible with Version 1."
                ) from error
            if logger:
                logger.info("Adopted compatible unversioned database as Version 1.")
            return
        migration = registry[0]
        if logger:
            logger.info("Detected empty database at schema version 0.")
            logger.info(
                "Beginning database migration %s: %s.",
                migration.version,
                migration.name,
            )
        try:
            connection.execute("BEGIN IMMEDIATE")
            _create_ledger(connection)
            migration.apply(connection)
            migration.verify(connection)
            connection.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                (migration.version, migration.name),
            )
            connection.commit()
        except Exception as error:
            connection.rollback()
            if logger:
                logger.error("Database migration 1 failed: %s", error)
            raise DatabaseMigrationError(
                "Database migration 1 failed."
            ) from error
        if logger:
            logger.info(
                "Completed database migration %s: %s.",
                migration.version,
                migration.name,
            )
        current_version = 1
    else:
        _verify_ledger(connection)
        recorded = _recorded_migrations(connection)
        current_version = recorded[-1][0] if recorded else 0

    if logger:
        logger.info("Detected database schema version %s.", current_version)
    if current_version > latest_version:
        raise DatabaseMigrationError(
            "This database was created by a newer application version."
        )
    for version, name in recorded if "recorded" in locals() else ():
        if registry[version - 1].name != name:
            raise DatabaseMigrationError(
                f"Migration {version} does not match this application."
            )
    if current_version == latest_version:
        registry[current_version - 1].verify(connection)
        return

    if before_migrations is not None:
        before_migrations(connection)
    for migration in registry[current_version:]:
        if logger:
            logger.info(
                "Beginning database migration %s: %s.",
                migration.version,
                migration.name,
            )
        try:
            connection.execute("BEGIN IMMEDIATE")
            migration.apply(connection)
            migration.verify(connection)
            connection.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                (migration.version, migration.name),
            )
            connection.commit()
        except Exception as error:
            connection.rollback()
            if logger:
                logger.error(
                    "Database migration %s failed: %s",
                    migration.version,
                    error,
                )
            raise DatabaseMigrationError(
                f"Database migration {migration.version} failed."
            ) from error
        if logger:
            logger.info(
                "Completed database migration %s: %s.",
                migration.version,
                migration.name,
            )
