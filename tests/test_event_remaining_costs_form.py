import sqlite3
from pathlib import Path

import pytest


DEDICATED_FIELDS = (
    "travel_cost",
    "parking_cost",
    "permit_cost",
    "generator_utility_cost",
    "vendor_booking_fee",
    "organizer_commission_percentage",
    "fixed_card_processing_fee",
)


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
        "vendor_booking_fee": "",
        "organizer_commission_percentage": "",
        "fixed_card_processing_fee": "",
        "additional_cost_name": [],
        "additional_cost_amount": [],
    }


def test_all_dedicated_cost_and_fee_fields_are_present(client):
    response = client.get("/events/new")

    assert b"Travel and operating costs" in response.data
    assert b"Event and payment fees" in response.data
    for field_name in DEDICATED_FIELDS:
        assert f'name="{field_name}"'.encode() in response.data


def test_all_dedicated_cost_and_fee_fields_are_optional(client):
    response = client.post("/events/new", data=valid_event_inputs())

    for label in (
        "Travel cost",
        "Parking cost",
        "Permit cost",
        "Generator or utility cost",
        "Vendor or booking fee",
        "Organizer commission or revenue share",
        "Fixed card-processing fee per card transaction",
    ):
        assert f"{label} is required.".encode() not in response.data


@pytest.mark.parametrize(
    ("value", "expected_error"),
    (
        (
            "-1",
            b"Organizer commission or revenue share must be between 0 and 100.",
        ),
        (
            "101",
            b"Organizer commission or revenue share must be between 0 and 100.",
        ),
        (
            "10.123",
            b"Organizer commission or revenue share can have at most 2 decimal places.",
        ),
    ),
)
def test_organizer_commission_validation_preserves_value(
    client, value, expected_error
):
    form_data = valid_event_inputs()
    form_data["organizer_commission_percentage"] = value

    response = client.post("/events/new", data=form_data)

    assert expected_error in response.data
    assert f'value="{value}"'.encode() in response.data


def test_fixed_processing_fee_wording_is_transaction_based(client):
    response = client.get("/events/new")
    page = " ".join(response.data.decode().split())

    assert "Fixed card-processing fee per card transaction ($)" in page
    assert "Charged once per card transaction, not once per event." in page


@pytest.mark.parametrize(
    ("value", "expected_error"),
    (
        (
            "-1",
            b"Fixed card-processing fee per card transaction cannot be negative.",
        ),
        (
            "0.123",
            b"Fixed card-processing fee per card transaction can have at most 2 decimal places.",
        ),
    ),
)
def test_fixed_processing_fee_validation_preserves_value(
    client, value, expected_error
):
    form_data = valid_event_inputs()
    form_data["fixed_card_processing_fee"] = value

    response = client.post("/events/new", data=form_data)

    assert expected_error in response.data
    assert f'value="{value}"'.encode() in response.data


def test_additional_costs_start_empty_and_have_add_remove_controls(client):
    response = client.get("/events/new")
    entries_html = response.data.split(
        b'id="event-additional-cost-entries"', 1
    )[1].split(b'id="add-additional-cost"', 1)[0]

    assert b"Additional costs" in response.data
    assert b"Add another cost" in response.data
    assert b'class="additional-cost-entry"' not in entries_html

    project_root = Path(__file__).parents[1]
    script = (
        project_root / "app" / "static" / "js" / "event_inputs.js"
    ).read_text(encoding="utf-8")
    assert 'button.closest(".additional-cost-entry").remove();' in script
    assert "additionalCostEntries.append(entry);" in script


def test_multiple_additional_costs_preserve_order_and_values(client):
    form_data = valid_event_inputs()
    form_data["location"] = ""
    form_data["additional_cost_name"] = [
        "Parking overflow",
        "Ice delivery",
    ]
    form_data["additional_cost_amount"] = ["21.50", "42.75"]

    response = client.post("/events/new", data=form_data)
    page = response.data.decode()

    assert page.index('value="Parking overflow"') < page.index(
        'value="Ice delivery"'
    )
    assert page.index('value="21.50"') < page.index('value="42.75"')


def test_removed_additional_cost_is_absent_on_submission(client):
    form_data = valid_event_inputs()
    form_data["location"] = ""
    form_data["additional_cost_name"] = ["Ice delivery"]
    form_data["additional_cost_amount"] = ["42.75"]

    response = client.post("/events/new", data=form_data)

    assert b'value="Ice delivery"' in response.data
    assert b'value="42.75"' in response.data
    assert b'value="Parking overflow"' not in response.data


@pytest.mark.parametrize(
    ("names", "amounts", "expected_error"),
    (
        ([""], ["10"], b"Cost name is required."),
        (["Parking"], [""], b"Miscellaneous cost amount is required."),
        (
            ["Parking"],
            ["0"],
            b"Miscellaneous cost amount must be greater than zero.",
        ),
        (
            ["Parking"],
            ["-1"],
            b"Miscellaneous cost amount must be greater than zero.",
        ),
        (
            ["Parking"],
            ["1.234"],
            b"Miscellaneous cost amount can have at most 2 decimal places.",
        ),
    ),
)
def test_additional_cost_validation_preserves_rows(
    client, names, amounts, expected_error
):
    form_data = valid_event_inputs()
    form_data["additional_cost_name"] = names
    form_data["additional_cost_amount"] = amounts

    response = client.post("/events/new", data=form_data)

    assert expected_error in response.data
    assert f'value="{names[0]}"'.encode() in response.data
    assert f'value="{amounts[0]}"'.encode() in response.data


def test_costs_and_rows_survive_unrelated_validation_error(client):
    form_data = valid_event_inputs()
    form_data["event_name"] = ""
    form_data["vendor_booking_fee"] = "100"
    form_data["organizer_commission_percentage"] = "5"
    form_data["fixed_card_processing_fee"] = "0.30"
    form_data["additional_cost_name"] = ["Ice"]
    form_data["additional_cost_amount"] = ["40"]

    response = client.post("/events/new", data=form_data)

    assert b"Event name is required." in response.data
    for value in ("100", "5", "0.30", "Ice", "40"):
        assert f'value="{value}"'.encode() in response.data


def test_invalid_remaining_costs_do_not_save_records(
    client, database_path
):
    form_data = valid_event_inputs()
    form_data["additional_cost_name"] = [""]
    form_data["additional_cost_amount"] = ["10"]

    client.post("/events/new", data=form_data)

    with sqlite3.connect(database_path) as database:
        event_count = database.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]
        scenario_count = database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0]
    assert (event_count, scenario_count) == (0, 0)
