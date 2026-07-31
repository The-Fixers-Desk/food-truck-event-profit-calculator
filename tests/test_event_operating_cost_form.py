import sqlite3

import pytest


OPERATING_COST_FIELDS = {
    "travel_cost": "Travel cost ($)",
    "parking_cost": "Parking cost ($)",
    "permit_cost": "Permit cost ($)",
    "generator_utility_cost": "Generator or utility cost ($)",
}


def valid_event_inputs() -> dict[str, str | list[str]]:
    return {
        "event_name": "Summer Festival",
        "event_date": "2026-08-15",
        "start_time": "11:00",
        "location": "Town Square",
        "estimated_attendance": "1000",
        "other_competing_food_vendors": "5",
        "expected_food_buyer_percentage": "10",
        "average_order_sale_amount": "15.00",
        "weather_outlook": "moderate_adverse",
        "custom_weather_reduction": "",
        "event_protection": "fully_outdoors",
        "revenue_method": "attendance",
        "expected_sales_amount": "",
        "food_cost_method_choice": "average_per_order",
        "food_cost_method": "average_per_order",
        "average_food_cost_per_order": "5.00",
        "food_cost_percentage": "",
        "manual_food_cost_total": "",
        "owner_labor_pay": "",
        "employee_labor_rate": [],
        "employee_labor_hours": [],
        "travel_cost": "",
        "parking_cost": "",
        "permit_cost": "",
        "generator_utility_cost": "",
    }


def test_travel_and_operating_cost_fields_are_present(client):
    response = client.get("/events/new")

    assert b"Travel and operating costs" in response.data
    for name, label in OPERATING_COST_FIELDS.items():
        assert f'name="{name}"'.encode() in response.data
        assert label.encode() in response.data


def test_all_operating_cost_fields_are_optional(client):
    response = client.post("/events/new", data=valid_event_inputs())

    for label in (
        "Travel cost",
        "Parking cost",
        "Permit cost",
        "Generator or utility cost",
    ):
        assert f"{label} is required.".encode() not in response.data


def test_valid_operating_cost_values_are_accepted_and_preserved(client):
    form_data = valid_event_inputs()
    form_data["location"] = ""
    form_data.update(
        {
            "travel_cost": "75.00",
            "parking_cost": "20.50",
            "permit_cost": "100",
            "generator_utility_cost": "35.25",
        }
    )

    response = client.post("/events/new", data=form_data)

    for value in ("75.00", "20.50", "100", "35.25"):
        assert f'value="{value}"'.encode() in response.data
    assert b"Travel cost cannot be negative." not in response.data


@pytest.mark.parametrize(
    ("field_name", "label"),
    (
        ("travel_cost", "Travel cost"),
        ("parking_cost", "Parking cost"),
        ("permit_cost", "Permit cost"),
        ("generator_utility_cost", "Generator or utility cost"),
    ),
)
@pytest.mark.parametrize(
    ("invalid_value", "error_suffix"),
    (
        ("-1", "cannot be negative."),
        ("1.234", "can have at most 2 decimal places."),
    ),
)
def test_invalid_operating_cost_values_are_rejected_and_preserved(
    client, field_name, label, invalid_value, error_suffix
):
    form_data = valid_event_inputs()
    form_data[field_name] = invalid_value

    response = client.post("/events/new", data=form_data)

    assert f"{label} {error_suffix}".encode() in response.data
    assert f'value="{invalid_value}"'.encode() in response.data


def test_operating_cost_values_survive_unrelated_validation_error(client):
    form_data = valid_event_inputs()
    form_data["event_name"] = ""
    form_data.update(
        {
            "travel_cost": "75",
            "parking_cost": "20",
            "permit_cost": "100",
            "generator_utility_cost": "35",
        }
    )

    response = client.post("/events/new", data=form_data)

    assert b"Event name is required." in response.data
    for value in ("75", "20", "100", "35"):
        assert f'value="{value}"'.encode() in response.data


def test_invalid_operating_cost_does_not_save_records(
    client, database_path
):
    form_data = valid_event_inputs()
    form_data["travel_cost"] = "-1"

    client.post("/events/new", data=form_data)

    with sqlite3.connect(database_path) as database:
        event_count = database.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]
        scenario_count = database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0]
    assert (event_count, scenario_count) == (0, 0)
