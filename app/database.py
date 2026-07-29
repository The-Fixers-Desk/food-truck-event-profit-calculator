import sqlite3
from decimal import Decimal
from pathlib import Path

from flask import current_app, g

from app.models import BusinessDefaults, LaborDefault


SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "business_defaults.sql"


def apply_business_defaults_schema(connection: sqlite3.Connection) -> None:
    """Create the business-defaults tables on a database connection."""
    connection.execute("PRAGMA foreign_keys = ON")
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    connection.executescript(schema)


def get_database() -> sqlite3.Connection:
    """Return the database connection for the current request."""
    if "database" not in g:
        database_path = Path(current_app.config["DATABASE"])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        g.database = sqlite3.connect(database_path)
        g.database.row_factory = sqlite3.Row
        g.database.execute("PRAGMA foreign_keys = ON")
    return g.database


def close_database(exception: BaseException | None = None) -> None:
    """Close the current request's database connection."""
    database = g.pop("database", None)
    if database is not None:
        database.close()


def initialize_database() -> None:
    """Create the schema, upgrading the uncommitted legacy shape if present."""
    database = get_database()
    columns = {
        row["name"]
        for row in database.execute(
            "PRAGMA table_info(business_defaults)"
        ).fetchall()
    }
    if columns and "average_order_value_cents" in columns:
        _upgrade_legacy_business_defaults(database)
    elif columns and "profit_target_type" not in columns:
        _upgrade_profit_target_schema(database)
    elif columns and "default_owner_labor_pay_cents" not in columns:
        database.execute(
            """
            ALTER TABLE business_defaults
            ADD COLUMN default_owner_labor_pay_cents INTEGER
                CHECK (
                    default_owner_labor_pay_cents IS NULL
                    OR default_owner_labor_pay_cents >= 0
                )
            """
        )
        database.commit()
    apply_business_defaults_schema(database)


def load_business_defaults() -> BusinessDefaults | None:
    """Load the single saved defaults record and its ordered labor entries."""
    database = get_database()
    row = database.execute(
        "SELECT * FROM business_defaults WHERE id = 1"
    ).fetchone()
    if row is None:
        return None
    labor_rows = database.execute(
        """
        SELECT hourly_rate_cents, total_paid_minutes
        FROM business_default_labor_entries
        WHERE business_defaults_id = 1
        ORDER BY position
        """
    ).fetchall()
    return BusinessDefaults(
        business_name=row["business_name"],
        average_order_sale_amount=_cents_to_decimal(
            row["average_order_sale_amount_cents"]
        ),
        food_cost_percentage=_basis_points_to_decimal(
            row["food_cost_basis_points"]
        ),
        card_sales_percentage=_basis_points_to_decimal(
            row["card_sales_basis_points"]
        ),
        card_processing_percentage=_basis_points_to_decimal(
            row["card_processing_basis_points"]
        ),
        labor_entries=tuple(
            LaborDefault(
                hourly_rate=_cents_to_decimal(item["hourly_rate_cents"]),
                total_hours_paid=_minutes_to_hours(
                    item["total_paid_minutes"]
                ),
            )
            for item in labor_rows
        ),
        default_owner_labor_pay=_optional_cents_to_decimal(
            row["default_owner_labor_pay_cents"]
        ),
        default_travel_cost=_optional_cents_to_decimal(
            row["default_travel_cost_cents"]
        ),
        profit_target_type=row["profit_target_type"],
        minimum_profit_amount=_optional_cents_to_decimal(
            row["minimum_profit_amount_cents"]
        ),
        minimum_profit_margin=_optional_basis_points_to_decimal(
            row["minimum_profit_margin_basis_points"]
        ),
    )


def save_business_defaults(defaults: BusinessDefaults) -> None:
    """Atomically save the defaults record and replace its labor entries."""
    database = get_database()
    with database:
        database.execute(
            """
            INSERT INTO business_defaults (
                id, business_name, average_order_sale_amount_cents,
                food_cost_basis_points, card_sales_basis_points,
                card_processing_basis_points, default_travel_cost_cents,
                default_owner_labor_pay_cents,
                profit_target_type, minimum_profit_amount_cents,
                minimum_profit_margin_basis_points
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                business_name = excluded.business_name,
                average_order_sale_amount_cents =
                    excluded.average_order_sale_amount_cents,
                food_cost_basis_points = excluded.food_cost_basis_points,
                card_sales_basis_points = excluded.card_sales_basis_points,
                card_processing_basis_points =
                    excluded.card_processing_basis_points,
                default_travel_cost_cents =
                    excluded.default_travel_cost_cents,
                default_owner_labor_pay_cents =
                    excluded.default_owner_labor_pay_cents,
                profit_target_type = excluded.profit_target_type,
                minimum_profit_amount_cents =
                    excluded.minimum_profit_amount_cents,
                minimum_profit_margin_basis_points =
                    excluded.minimum_profit_margin_basis_points,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                defaults.business_name,
                _decimal_to_cents(defaults.average_order_sale_amount),
                _decimal_to_basis_points(defaults.food_cost_percentage),
                _decimal_to_basis_points(defaults.card_sales_percentage),
                _decimal_to_basis_points(
                    defaults.card_processing_percentage
                ),
                _optional_decimal_to_cents(defaults.default_travel_cost),
                _optional_decimal_to_cents(
                    defaults.default_owner_labor_pay
                ),
                defaults.profit_target_type,
                _optional_decimal_to_cents(
                    defaults.minimum_profit_amount
                ),
                _optional_decimal_to_basis_points(
                    defaults.minimum_profit_margin
                ),
            ),
        )
        database.execute(
            """
            DELETE FROM business_default_labor_entries
            WHERE business_defaults_id = 1
            """
        )
        database.executemany(
            """
            INSERT INTO business_default_labor_entries (
                business_defaults_id, position, hourly_rate_cents,
                total_paid_minutes
            )
            VALUES (1, ?, ?, ?)
            """,
            [
                (
                    position,
                    _decimal_to_cents(entry.hourly_rate),
                    _hours_to_minutes(entry.total_hours_paid),
                )
                for position, entry in enumerate(defaults.labor_entries)
            ],
        )


def _upgrade_legacy_business_defaults(
    database: sqlite3.Connection,
) -> None:
    """Upgrade the earlier uncommitted single-labor schema."""
    legacy_row = database.execute(
        "SELECT * FROM business_defaults WHERE id = 1"
    ).fetchone()
    database.execute("ALTER TABLE business_defaults RENAME TO legacy_defaults")
    apply_business_defaults_schema(database)
    if legacy_row is not None:
        database.execute(
            """
            INSERT INTO business_defaults (
                id, business_name, average_order_sale_amount_cents,
                food_cost_basis_points, card_sales_basis_points,
                card_processing_basis_points,
                profit_target_type, minimum_profit_amount_cents,
                minimum_profit_margin_basis_points
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                legacy_row["business_name"],
                legacy_row["average_order_value_cents"],
                legacy_row["food_cost_basis_points"],
                legacy_row["card_sales_basis_points"],
                legacy_row["card_processing_basis_points"],
                _legacy_target_type(legacy_row),
                legacy_row["minimum_acceptable_profit_cents"]
                if _legacy_target_type(legacy_row) == "profit_amount"
                else None,
                legacy_row["minimum_acceptable_margin_basis_points"]
                if _legacy_target_type(legacy_row) == "profit_margin"
                else None,
            ),
        )
    database.execute("DROP TABLE legacy_defaults")
    database.commit()


def _upgrade_profit_target_schema(database: sqlite3.Connection) -> None:
    """Add the required-choice shape while retaining prior saved defaults."""
    defaults_row = database.execute(
        "SELECT * FROM business_defaults WHERE id = 1"
    ).fetchone()
    labor_rows = database.execute(
        """
        SELECT position, hourly_rate_cents, total_paid_minutes
        FROM business_default_labor_entries ORDER BY position
        """
    ).fetchall()
    database.execute("DROP TABLE business_default_labor_entries")
    database.execute("ALTER TABLE business_defaults RENAME TO prior_defaults")
    apply_business_defaults_schema(database)
    if defaults_row is not None:
        target_type = _legacy_target_type(defaults_row)
        database.execute(
            """
            INSERT INTO business_defaults (
                id, business_name, average_order_sale_amount_cents,
                food_cost_basis_points, card_sales_basis_points,
                card_processing_basis_points, default_travel_cost_cents,
                profit_target_type, minimum_profit_amount_cents,
                minimum_profit_margin_basis_points, created_at, updated_at
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                defaults_row["business_name"],
                defaults_row["average_order_sale_amount_cents"],
                defaults_row["food_cost_basis_points"],
                defaults_row["card_sales_basis_points"],
                defaults_row["card_processing_basis_points"],
                defaults_row["default_travel_cost_cents"],
                target_type,
                defaults_row["minimum_acceptable_profit_cents"]
                if target_type == "profit_amount" else None,
                defaults_row["minimum_acceptable_margin_basis_points"]
                if target_type == "profit_margin" else None,
                defaults_row["created_at"],
                defaults_row["updated_at"],
            ),
        )
        database.executemany(
            """
            INSERT INTO business_default_labor_entries (
                business_defaults_id, position, hourly_rate_cents,
                total_paid_minutes
            )
            VALUES (1, ?, ?, ?)
            """,
            [tuple(row) for row in labor_rows],
        )
    database.execute("DROP TABLE prior_defaults")
    database.commit()


def _legacy_target_type(row: sqlite3.Row) -> str | None:
    if row["minimum_acceptable_profit_cents"] is not None:
        return "profit_amount"
    if row["minimum_acceptable_margin_basis_points"] is not None:
        return "profit_margin"
    return None


def _cents_to_decimal(value: int) -> Decimal:
    return Decimal(value) / Decimal("100")


def _basis_points_to_decimal(value: int) -> Decimal:
    return Decimal(value) / Decimal("10000")


def _minutes_to_hours(value: int) -> Decimal:
    return Decimal(value) / Decimal("60")


def _decimal_to_cents(value: Decimal) -> int:
    return int(value * 100)


def _decimal_to_basis_points(value: Decimal) -> int:
    return int(value * 10000)


def _hours_to_minutes(value: Decimal) -> int:
    return int(value * 60)


def _optional_cents_to_decimal(value: int | None) -> Decimal | None:
    return None if value is None else _cents_to_decimal(value)


def _optional_basis_points_to_decimal(value: int | None) -> Decimal | None:
    return None if value is None else _basis_points_to_decimal(value)


def _optional_decimal_to_cents(value: Decimal | None) -> int | None:
    return None if value is None else _decimal_to_cents(value)


def _optional_decimal_to_basis_points(value: Decimal | None) -> int | None:
    return None if value is None else _decimal_to_basis_points(value)
