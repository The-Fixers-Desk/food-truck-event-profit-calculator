import sqlite3

import pytest

from app.database import apply_business_defaults_schema


@pytest.fixture()
def connection():
    """Create an isolated in-memory SQLite database."""
    database = sqlite3.connect(":memory:")

    apply_business_defaults_schema(database)

    yield database

    database.close()


def valid_business_defaults() -> tuple:
    """Return a valid database row for business defaults."""
    return (
        1,
        "Example Food Truck",
        1500,
        3000,
        8000,
        300,
        2,
        1800,
        90,
        60,
        75,
        30000,
        2000,
    )


def insert_business_defaults(
    connection: sqlite3.Connection,
    values: tuple,
) -> None:
    """Insert one business-defaults record."""
    connection.execute(
        """
        INSERT INTO business_defaults (
            id,
            business_name,
            average_order_value_cents,
            food_cost_basis_points,
            card_sales_basis_points,
            card_processing_basis_points,
            default_staff_count,
            hourly_labor_cost_cents,
            setup_minutes,
            cleanup_minutes,
            vehicle_cost_per_mile_cents,
            minimum_acceptable_profit_cents,
            minimum_acceptable_margin_basis_points
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )
    connection.commit()


def test_business_defaults_table_is_created(
    connection: sqlite3.Connection,
):
    """Applying the schema should create the expected table."""
    result = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'business_defaults'
        """
    ).fetchone()

    assert result == ("business_defaults",)


def test_valid_business_defaults_can_be_inserted(
    connection: sqlite3.Connection,
):
    """The table should accept a complete valid defaults record."""
    insert_business_defaults(
        connection,
        valid_business_defaults(),
    )

    result = connection.execute(
        """
        SELECT
            business_name,
            average_order_value_cents,
            food_cost_basis_points
        FROM business_defaults
        WHERE id = 1
        """
    ).fetchone()

    assert result == (
        "Example Food Truck",
        1500,
        3000,
    )


def test_optional_thresholds_can_be_null(
    connection: sqlite3.Connection,
):
    """Optional decision thresholds should allow null values."""
    values = list(valid_business_defaults())
    values[11] = None
    values[12] = None

    insert_business_defaults(
        connection,
        tuple(values),
    )

    result = connection.execute(
        """
        SELECT
            minimum_acceptable_profit_cents,
            minimum_acceptable_margin_basis_points
        FROM business_defaults
        WHERE id = 1
        """
    ).fetchone()

    assert result == (None, None)


def test_only_one_defaults_record_can_exist(
    connection: sqlite3.Connection,
):
    """The schema should reject additional defaults records."""
    insert_business_defaults(
        connection,
        valid_business_defaults(),
    )

    second_record = list(valid_business_defaults())
    second_record[0] = 2

    with pytest.raises(sqlite3.IntegrityError):
        insert_business_defaults(
            connection,
            tuple(second_record),
        )


def test_percentage_above_one_hundred_is_rejected(
    connection: sqlite3.Connection,
):
    """Percentage columns should reject values above 100 percent."""
    values = list(valid_business_defaults())
    values[3] = 10001

    with pytest.raises(sqlite3.IntegrityError):
        insert_business_defaults(
            connection,
            tuple(values),
        )


def test_negative_currency_is_rejected(
    connection: sqlite3.Connection,
):
    """Currency columns should reject negative values."""
    values = list(valid_business_defaults())
    values[7] = -1

    with pytest.raises(sqlite3.IntegrityError):
        insert_business_defaults(
            connection,
            tuple(values),
        )