import sqlite3

import pytest

from app.database import apply_business_defaults_schema


@pytest.fixture()
def connection():
    database = sqlite3.connect(":memory:")
    apply_business_defaults_schema(database)
    yield database
    database.close()


def insert_defaults(connection, travel_cost=7500):
    connection.execute(
        """
        INSERT INTO business_defaults (
            id, business_name, average_order_sale_amount_cents,
            food_cost_basis_points, card_sales_basis_points,
            card_processing_basis_points, default_travel_cost_cents
        )
        VALUES (1, 'Example Food Truck', 1500, 3000, 8000, 300, ?)
        """,
        (travel_cost,),
    )


def test_business_defaults_and_labor_tables_are_created(connection):
    tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table'
            """
        )
    }
    assert "business_defaults" in tables
    assert "business_default_labor_entries" in tables


def test_multiple_labor_entries_can_be_saved(connection):
    insert_defaults(connection)
    connection.executemany(
        """
        INSERT INTO business_default_labor_entries (
            business_defaults_id, position, hourly_rate_cents,
            total_paid_minutes
        )
        VALUES (1, ?, ?, ?)
        """,
        ((0, 1800, 720), (1, 2500, 240)),
    )

    rows = connection.execute(
        """
        SELECT hourly_rate_cents, total_paid_minutes
        FROM business_default_labor_entries ORDER BY position
        """
    ).fetchall()
    assert rows == [(1800, 720), (2500, 240)]


def test_optional_travel_cost_can_be_null(connection):
    insert_defaults(connection, travel_cost=None)
    value = connection.execute(
        "SELECT default_travel_cost_cents FROM business_defaults"
    ).fetchone()[0]
    assert value is None


def test_optional_owner_labor_pay_uses_nullable_cents(connection):
    insert_defaults(connection)
    connection.execute(
        """
        UPDATE business_defaults
        SET default_owner_labor_pay_cents = 12500
        WHERE id = 1
        """
    )
    value = connection.execute(
        "SELECT default_owner_labor_pay_cents FROM business_defaults"
    ).fetchone()[0]
    assert value == 12500

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            UPDATE business_defaults
            SET default_owner_labor_pay_cents = -1
            WHERE id = 1
            """
        )


def test_negative_labor_values_are_rejected(connection):
    insert_defaults(connection)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO business_default_labor_entries (
                business_defaults_id, position, hourly_rate_cents,
                total_paid_minutes
            )
            VALUES (1, 0, -1, 60)
            """
        )


def test_percentage_above_one_hundred_is_rejected(connection):
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO business_defaults (
                id, average_order_sale_amount_cents,
                food_cost_basis_points, card_sales_basis_points,
                card_processing_basis_points
            )
            VALUES (1, 1500, 10001, 8000, 300)
            """
        )


def test_profit_target_stores_only_its_matching_value(connection):
    connection.execute(
        """
        INSERT INTO business_defaults (
            id, average_order_sale_amount_cents,
            food_cost_basis_points, card_sales_basis_points,
            card_processing_basis_points, profit_target_type,
            minimum_profit_amount_cents
        )
        VALUES (1, 1500, 3000, 8000, 300, 'profit_amount', 30000)
        """
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            UPDATE business_defaults
            SET minimum_profit_margin_basis_points = 2000
            WHERE id = 1
            """
        )
