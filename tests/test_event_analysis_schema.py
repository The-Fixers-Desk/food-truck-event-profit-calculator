import sqlite3

import pytest

from app.database import (
    apply_business_defaults_schema,
    apply_event_analysis_schema,
)


@pytest.fixture()
def connection():
    database = sqlite3.connect(":memory:")
    database.execute("PRAGMA foreign_keys = ON")
    apply_event_analysis_schema(database)
    yield database
    database.close()


def insert_event(connection, name="Summer Festival") -> int:
    cursor = connection.execute(
        """
        INSERT INTO events (
            event_name, event_date, start_time_minutes, location
        )
        VALUES (?, '2026-08-15', 660, 'Town Square')
        """,
        (name,),
    )
    return cursor.lastrowid


def valid_scenario_values(event_id: int, name="Original estimate") -> dict:
    return {
        "event_id": event_id,
        "scenario_name": name,
        "notes": None,
        "estimated_attendance": 1000,
        "other_competing_food_vendors": 5,
        "expected_food_buyer_basis_points": 1000,
        "event_protection": "covered_reliable_seating",
        "weather_outlook": "minor_concern",
        "custom_weather_reduction_basis_points": None,
        "revenue_method": "attendance",
        "average_order_sale_amount_cents": 1500,
        "expected_sales_amount_cents": None,
        "food_cost_method": "sales_percentage",
        "average_food_cost_per_order_cents": None,
        "food_cost_percentage_basis_points": 3000,
        "manual_food_cost_total_cents": None,
        "card_sales_basis_points": 8000,
        "card_processing_basis_points": 300,
        "fixed_card_processing_fee_cents": 500,
        "vendor_or_booking_fee_cents": 10000,
        "organizer_commission_basis_points": 500,
        "owner_labor_pay_cents": 12500,
        "travel_cost_cents": 7500,
        "profit_target_type": "profit_amount",
        "minimum_profit_amount_cents": 30000,
        "minimum_profit_margin_basis_points": None,
    }


def insert_scenario(connection, values: dict) -> int:
    cursor = connection.execute(
        """
        INSERT INTO event_scenarios (
            event_id, scenario_name, notes, estimated_attendance,
            other_competing_food_vendors, expected_food_buyer_basis_points,
            event_protection, weather_outlook,
            custom_weather_reduction_basis_points, revenue_method,
            average_order_sale_amount_cents, expected_sales_amount_cents,
            food_cost_method, average_food_cost_per_order_cents,
            food_cost_percentage_basis_points,
            manual_food_cost_total_cents, card_sales_basis_points,
            card_processing_basis_points,
            fixed_card_processing_fee_cents,
            vendor_or_booking_fee_cents,
            organizer_commission_basis_points, owner_labor_pay_cents,
            travel_cost_cents, profit_target_type,
            minimum_profit_amount_cents,
            minimum_profit_margin_basis_points
        )
        VALUES (
            :event_id, :scenario_name, :notes, :estimated_attendance,
            :other_competing_food_vendors, :expected_food_buyer_basis_points,
            :event_protection, :weather_outlook,
            :custom_weather_reduction_basis_points, :revenue_method,
            :average_order_sale_amount_cents, :expected_sales_amount_cents,
            :food_cost_method, :average_food_cost_per_order_cents,
            :food_cost_percentage_basis_points,
            :manual_food_cost_total_cents, :card_sales_basis_points,
            :card_processing_basis_points,
            :fixed_card_processing_fee_cents,
            :vendor_or_booking_fee_cents,
            :organizer_commission_basis_points, :owner_labor_pay_cents,
            :travel_cost_cents, :profit_target_type,
            :minimum_profit_amount_cents,
            :minimum_profit_margin_basis_points
        )
        """,
        values,
    )
    return cursor.lastrowid


def test_saved_event_tables_and_important_columns_exist(connection):
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {
        "events",
        "event_scenarios",
        "event_scenario_employee_labor_entries",
        "event_scenario_additional_costs",
    } <= tables

    scenario_columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(event_scenarios)")
    }
    assert {
        "event_id",
        "other_competing_food_vendors",
        "expected_food_buyer_basis_points",
        "manual_average_order_sale_amount_cents",
        "revenue_method",
        "food_cost_method",
        "owner_labor_pay_cents",
        "profit_target_type",
        "created_at",
        "updated_at",
    } <= scenario_columns


def test_one_event_can_own_multiple_scenarios(connection):
    event_id = insert_event(connection)
    insert_scenario(connection, valid_scenario_values(event_id))
    insert_scenario(
        connection, valid_scenario_values(event_id, "Rain forecast")
    )

    count = connection.execute(
        "SELECT COUNT(*) FROM event_scenarios WHERE event_id = ?",
        (event_id,),
    ).fetchone()[0]
    assert count == 2


def test_event_identity_fields_do_not_need_to_be_unique(connection):
    first_id = insert_event(connection, "Community Fair")
    second_id = insert_event(connection, "Community Fair")

    assert first_id != second_id


def test_labor_and_additional_cost_order_is_preserved(connection):
    scenario_id = insert_scenario(
        connection, valid_scenario_values(insert_event(connection))
    )
    connection.executemany(
        """
        INSERT INTO event_scenario_employee_labor_entries (
            event_scenario_id, position, hourly_rate_cents,
            total_paid_minutes
        )
        VALUES (?, ?, ?, ?)
        """,
        ((scenario_id, 1, 2500, 240), (scenario_id, 0, 1800, 720)),
    )
    connection.executemany(
        """
        INSERT INTO event_scenario_additional_costs (
            event_scenario_id, position, cost_name, amount_cents
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            (scenario_id, 1, "Generator fuel", 3000),
            (scenario_id, 0, "Parking", 2000),
        ),
    )

    labor = connection.execute(
        """
        SELECT hourly_rate_cents
        FROM event_scenario_employee_labor_entries
        WHERE event_scenario_id = ? ORDER BY position
        """,
        (scenario_id,),
    ).fetchall()
    costs = connection.execute(
        """
        SELECT cost_name FROM event_scenario_additional_costs
        WHERE event_scenario_id = ? ORDER BY position
        """,
        (scenario_id,),
    ).fetchall()
    assert labor == [(1800,), (2500,)]
    assert costs == [("Parking",), ("Generator fuel",)]


def test_owner_only_scenario_allows_zero_child_rows(connection):
    scenario_id = insert_scenario(
        connection, valid_scenario_values(insert_event(connection))
    )

    labor_count = connection.execute(
        """
        SELECT COUNT(*) FROM event_scenario_employee_labor_entries
        WHERE event_scenario_id = ?
        """,
        (scenario_id,),
    ).fetchone()[0]
    cost_count = connection.execute(
        """
        SELECT COUNT(*) FROM event_scenario_additional_costs
        WHERE event_scenario_id = ?
        """,
        (scenario_id,),
    ).fetchone()[0]
    assert (labor_count, cost_count) == (0, 0)


@pytest.mark.parametrize(
    "changes",
    [
        {"estimated_attendance": -1},
        {"expected_food_buyer_basis_points": 10001},
        {"event_protection": "unknown"},
        {"weather_outlook": "custom"},
        {
            "revenue_method": "attendance",
            "expected_sales_amount_cents": 500000,
        },
        {
            "revenue_method": "manual_sales",
            "average_order_sale_amount_cents": None,
        },
        {
            "food_cost_method": "average_per_order",
            "food_cost_percentage_basis_points": None,
        },
        {"card_processing_basis_points": -1},
        {"owner_labor_pay_cents": -1},
        {"profit_target_type": "unknown"},
        {"minimum_profit_margin_basis_points": 2000},
    ],
)
def test_invalid_scenario_states_are_rejected(connection, changes):
    values = valid_scenario_values(insert_event(connection))
    values.update(changes)

    with pytest.raises(sqlite3.IntegrityError):
        insert_scenario(connection, values)


def test_invalid_child_rows_are_rejected(connection):
    scenario_id = insert_scenario(
        connection, valid_scenario_values(insert_event(connection))
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO event_scenario_employee_labor_entries (
                event_scenario_id, position, hourly_rate_cents,
                total_paid_minutes
            )
            VALUES (?, 0, -1, 60)
            """,
            (scenario_id,),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO event_scenario_additional_costs (
                event_scenario_id, position, cost_name, amount_cents
            )
            VALUES (?, 0, ' ', 100)
            """,
            (scenario_id,),
        )


def test_deleting_scenario_removes_only_its_children(connection):
    event_id = insert_event(connection)
    first_id = insert_scenario(
        connection, valid_scenario_values(event_id, "First")
    )
    second_id = insert_scenario(
        connection, valid_scenario_values(event_id, "Second")
    )
    connection.execute(
        """
        INSERT INTO event_scenario_additional_costs (
            event_scenario_id, position, cost_name, amount_cents
        )
        VALUES (?, 0, 'Parking', 2000)
        """,
        (first_id,),
    )
    connection.execute(
        """
        INSERT INTO event_scenario_employee_labor_entries (
            event_scenario_id, position, hourly_rate_cents,
            total_paid_minutes
        )
        VALUES (?, 0, 1800, 720)
        """,
        (first_id,),
    )

    connection.execute(
        "DELETE FROM event_scenarios WHERE id = ?", (first_id,)
    )

    assert connection.execute(
        "SELECT COUNT(*) FROM events WHERE id = ?", (event_id,)
    ).fetchone()[0] == 1
    assert connection.execute(
        "SELECT COUNT(*) FROM event_scenarios WHERE id = ?", (second_id,)
    ).fetchone()[0] == 1
    assert connection.execute(
        """
        SELECT COUNT(*) FROM event_scenario_additional_costs
        WHERE event_scenario_id = ?
        """,
        (first_id,),
    ).fetchone()[0] == 0
    assert connection.execute(
        """
        SELECT COUNT(*) FROM event_scenario_employee_labor_entries
        WHERE event_scenario_id = ?
        """,
        (first_id,),
    ).fetchone()[0] == 0


def test_deleting_event_cascades_to_all_related_rows(connection):
    event_id = insert_event(connection)
    scenario_id = insert_scenario(
        connection, valid_scenario_values(event_id)
    )
    connection.execute(
        """
        INSERT INTO event_scenario_employee_labor_entries (
            event_scenario_id, position, hourly_rate_cents,
            total_paid_minutes
        )
        VALUES (?, 0, 1800, 720)
        """,
        (scenario_id,),
    )
    connection.execute(
        """
        INSERT INTO event_scenario_additional_costs (
            event_scenario_id, position, cost_name, amount_cents
        )
        VALUES (?, 0, 'Parking', 2000)
        """,
        (scenario_id,),
    )

    connection.execute("DELETE FROM events WHERE id = ?", (event_id,))

    assert connection.execute(
        "SELECT COUNT(*) FROM event_scenarios"
    ).fetchone()[0] == 0
    assert connection.execute(
        "SELECT COUNT(*) FROM event_scenario_employee_labor_entries"
    ).fetchone()[0] == 0
    assert connection.execute(
        "SELECT COUNT(*) FROM event_scenario_additional_costs"
    ).fetchone()[0] == 0


def test_event_schema_initialization_is_repeatable(connection):
    apply_event_analysis_schema(connection)
    apply_event_analysis_schema(connection)

    assert connection.execute(
        "SELECT COUNT(*) FROM events"
    ).fetchone()[0] == 0


def test_legacy_demand_percentage_is_preserved_but_not_reinterpreted():
    database = sqlite3.connect(":memory:")
    apply_event_analysis_schema(database)
    event_id = insert_event(database)
    scenario_id = insert_scenario(
        database, valid_scenario_values(event_id)
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

    row = database.execute(
        """
        SELECT competing_food_vendors, expected_buyer_basis_points,
               other_competing_food_vendors,
               expected_food_buyer_basis_points
        FROM event_scenarios WHERE id = ?
        """,
        (scenario_id,),
    ).fetchone()
    assert row == (5, 1000, None, None)
    database.close()


def test_event_schema_does_not_change_existing_business_defaults():
    database = sqlite3.connect(":memory:")
    apply_business_defaults_schema(database)
    database.execute(
        """
        INSERT INTO business_defaults (
            id, business_name, average_order_sale_amount_cents,
            food_cost_method, average_food_cost_per_order_cents,
            card_sales_basis_points, card_processing_basis_points,
            profit_target_type, minimum_profit_amount_cents
        )
        VALUES (
            1, 'Existing Truck', 1500, 'average_per_order', 500,
            8000, 300, 'profit_amount', 30000
        )
        """
    )
    before = database.execute(
        "SELECT * FROM business_defaults"
    ).fetchone()

    apply_event_analysis_schema(database)
    apply_event_analysis_schema(database)

    after = database.execute("SELECT * FROM business_defaults").fetchone()
    assert after == before
    database.close()
