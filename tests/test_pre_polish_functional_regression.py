import sqlite3
from decimal import Decimal

import pytest

from tests.test_complete_event_inputs_workflow import complete_event_inputs
from tests.test_saved_events_management import latest_ids, save_sibling


def table_counts(database_path):
    with sqlite3.connect(database_path) as database:
        return tuple(
            database.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "events",
                "event_scenarios",
                "event_scenario_employee_labor_entries",
                "event_scenario_additional_costs",
            )
        )


def test_shared_fixture_isolates_complete_application_data_root(
    app, database_path
):
    paths = app.config["DATA_PATHS"]
    assert paths.root == database_path.parent
    assert paths.database == database_path
    assert paths.automatic_recovery.is_relative_to(database_path.parent)
    assert paths.staging.is_relative_to(database_path.parent)


@pytest.mark.parametrize(
    ("changes", "expected_code", "profit_sign", "target_met"),
    (
        ({"manual_food_cost_total": "9000"}, "estimated_loss", -1, False),
        (
            {"minimum_profit_margin": "90"},
            "below_profit_target",
            1,
            False,
        ),
        (
            {"minimum_profit_margin": "10"},
            None,
            1,
            True,
        ),
    ),
)
def test_three_customer_facing_outcomes(
    client, changes, expected_code, profit_sign, target_met
):
    form = complete_event_inputs()
    form.update(changes)

    payload = client.post("/event-analysis/calculate", data=form).get_json()

    assert payload["valid"] is True
    result = payload["result"]
    profit = Decimal(result["business_profit"])
    assert (profit > 0) - (profit < 0) == profit_sign
    assert result["profit_target"]["is_met"] is target_met
    codes = {warning["code"] for warning in result["warnings"]}
    if expected_code is None:
        assert "estimated_loss" not in codes
        assert "below_profit_target" not in codes
    else:
        assert expected_code in codes
    assert "exact_break_even_customers" not in result
    assert isinstance(result["break_even_customers"], int)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("event_name", "", b"Event name is required."),
        ("estimated_attendance", "1.5", b"whole number"),
        ("expected_food_buyer_percentage", "101", b"between 0 and 100"),
        ("other_competing_food_vendors", "-1", b"cannot be negative"),
        ("average_order_sale_amount", "-1", b"cannot be negative"),
        ("food_cost_percentage", "101", b"between 0 and 100"),
        ("card_sales_percentage", "101", b"between 0 and 100"),
        ("minimum_profit_margin", "101", b"between 0 and 100"),
    ),
)
def test_invalid_complete_submission_is_atomic_and_friendly(
    client, database_path, field, value, message
):
    form = complete_event_inputs()
    if field == "food_cost_percentage":
        form.update(
            food_cost_method="sales_percentage",
            food_cost_method_choice="sales_percentage",
            manual_food_cost_total="",
        )
    form[field] = value

    response = client.post("/events/new", data=form)

    assert response.status_code == 200
    assert message in response.data
    assert table_counts(database_path) == (0, 0, 0, 0)
    assert b"Traceback" not in response.data


def test_long_repeatable_content_and_custom_sales_survive_restart(
    client, app, database_path, restart_application
):
    form = complete_event_inputs()
    form.update(
        event_name="E" * 120,
        location="Long location " * 20,
        employee_labor_rate=["18", "22", "30", "45"],
        employee_labor_hours=["2", "4", "6", "8"],
        additional_cost_name=[
            "Long named cost " + str(index) + " " + "x" * 50
            for index in range(4)
        ],
        additional_cost_amount=["10", "20", "30", "40"],
        revenue_method="manual_sales",
        expected_sales_amount="4321.09",
    )
    response = client.post("/events/new", data=form)
    assert response.status_code == 200
    event_id, scenario_id = save_sibling(
        client,
        database_path,
        "Custom long-content scenario",
        employee_labor_rate=form["employee_labor_rate"],
        employee_labor_hours=form["employee_labor_hours"],
        additional_cost_name=form["additional_cost_name"],
        additional_cost_amount=form["additional_cost_amount"],
        revenue_method="manual_sales",
        expected_sales_amount="4321.09",
    )

    restarted = restart_application(app)
    page = restarted.test_client().get(
        f"/events/{event_id}/scenarios/{scenario_id}"
    ).data

    assert ("E" * 120).encode() in page
    assert b'value="4321.09"' in page
    assert page.index(b'value="18"') < page.index(b'value="45"')
    assert page.index(b"Long named cost 0") < page.index(b"Long named cost 3")
    with sqlite3.connect(database_path) as database:
        version = database.execute(
            "SELECT MAX(version) FROM schema_migrations"
        ).fetchone()[0]
    assert version >= 1


def test_deleting_one_event_preserves_another_event(client, database_path):
    first = complete_event_inputs()
    first["event_name"] = "Delete this event"
    client.post("/events/new", data=first)
    first_event, _ = latest_ids(database_path)
    second = complete_event_inputs()
    second["event_name"] = "Keep this event"
    client.post("/events/new", data=second)
    second_event, _ = latest_ids(database_path)

    client.post(
        f"/events/{first_event}/delete",
        data={"confirmed": "yes"},
    )

    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM events WHERE id = ?", (first_event,)
        ).fetchone()[0] == 0
        assert database.execute(
            "SELECT event_name FROM events WHERE id = ?", (second_event,)
        ).fetchone() == ("Keep this event",)


def test_long_scenario_name_is_distinct_and_comparable(client, database_path):
    client.post("/events/new", data=complete_event_inputs())
    long_name = "Scenario " + "planning assumptions " * 8
    event_id, scenario_id = save_sibling(
        client,
        database_path,
        long_name,
        travel_cost="321.09",
    )
    with sqlite3.connect(database_path) as database:
        original_id = database.execute(
            "SELECT MIN(id) FROM event_scenarios WHERE event_id = ?",
            (event_id,),
        ).fetchone()[0]

    comparison = client.post(
        "/comparison",
        data={"scenario_id": [str(original_id), str(scenario_id)]},
    )

    assert comparison.status_code == 200
    assert long_name.strip().encode() in comparison.data
    assert comparison.data.count(b"Open analysis") == 2
