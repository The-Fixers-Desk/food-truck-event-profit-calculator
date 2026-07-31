import sqlite3
from pathlib import Path

import pytest


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
    }


def test_labor_section_starts_without_employee_rows(client):
    response = client.get("/events/new")
    entries_html = response.data.split(
        b'id="event-employee-labor-entries"', 1
    )[1].split(b'id="add-event-labor"', 1)[0]

    assert b"<legend>Labor</legend>" in response.data
    assert b"Add employee labor" in response.data
    assert b'class="labor-entry"' not in entries_html
    assert b'name="owner_labor_pay"' in response.data


def test_labor_help_explains_combined_hours(client):
    response = client.get("/events/new")
    page_text = " ".join(response.data.decode().split())

    assert "Combined hours include all employees paid at the same rate" in (
        page_text
    )
    assert "including setup and cleanup when applicable" in page_text
    assert (
        b"Optional flat amount you plan to pay yourself for working this event."
        in response.data
    )


def test_add_and_remove_employee_labor_controls_are_client_side():
    project_root = Path(__file__).parents[1]
    template = (
        project_root / "app" / "templates" / "calculator.html"
    ).read_text(encoding="utf-8")
    script = (
        project_root / "app" / "static" / "js" / "event_inputs.js"
    ).read_text(encoding="utf-8")

    add_button = template.split('id="add-event-labor"', 1)[1].split(
        ">", 1
    )[0]
    assert 'type="button"' in add_button
    assert 'class="remove-event-labor button-secondary"' in template
    assert 'button.closest(".labor-entry").remove();' in script
    assert "employeeLaborEntries.append(entry);" in script


def test_multiple_employee_labor_entries_preserve_order_and_values(client):
    form_data = valid_event_inputs()
    form_data["location"] = ""
    form_data["employee_labor_rate"] = ["18.00", "25.00"]
    form_data["employee_labor_hours"] = ["12", "4"]

    response = client.post("/events/new", data=form_data)

    page = response.data.decode()
    assert page.index('value="18.00"') < page.index('value="25.00"')
    assert page.index('value="12"') < page.index('value="4"')
    assert response.data.count(b'class="labor-entry"') >= 3


def test_removed_employee_labor_row_is_absent_on_submission(client):
    form_data = valid_event_inputs()
    form_data["location"] = ""
    form_data["employee_labor_rate"] = ["25.00"]
    form_data["employee_labor_hours"] = ["4"]

    response = client.post("/events/new", data=form_data)

    assert b'value="25.00"' in response.data
    assert b'value="4"' in response.data
    assert b'value="18.00"' not in response.data


def test_owner_only_event_allows_zero_employee_labor(client):
    form_data = valid_event_inputs()
    form_data["location"] = ""
    form_data["owner_labor_pay"] = "125.00"

    response = client.post("/events/new", data=form_data)

    assert b'value="125.00"' in response.data
    assert b"Hourly labor rate is required." not in response.data


def test_owner_labor_pay_is_optional(client):
    form_data = valid_event_inputs()
    form_data["location"] = ""

    response = client.post("/events/new", data=form_data)

    assert b"Owner labor pay for this event is required." not in response.data
    assert b'name="owner_labor_pay"' in response.data


@pytest.mark.parametrize(
    ("rates", "hours", "expected_error"),
    (
        ([""], ["4"], b"Hourly labor rate is required."),
        (["18"], [""], b"Combined total hours paid is required."),
        (["0"], ["4"], b"Hourly labor rate must be greater than zero."),
        (["18"], ["0"], b"Combined total hours paid must be greater than zero."),
        (["-1"], ["4"], b"Hourly labor rate must be greater than zero."),
        (["18"], ["-1"], b"Combined total hours paid must be greater than zero."),
        (
            ["18.123"],
            ["4"],
            b"Hourly labor rate can have at most 2 decimal places.",
        ),
    ),
)
def test_employee_labor_validation_preserves_rows(
    client, rates, hours, expected_error
):
    form_data = valid_event_inputs()
    form_data["employee_labor_rate"] = rates
    form_data["employee_labor_hours"] = hours

    response = client.post("/events/new", data=form_data)

    assert expected_error in response.data
    assert f'value="{rates[0]}"'.encode() in response.data
    assert f'value="{hours[0]}"'.encode() in response.data


@pytest.mark.parametrize(
    ("value", "expected_error"),
    (
        ("-1", b"Owner labor pay for this event cannot be negative."),
        (
            "12.345",
            b"Owner labor pay for this event can have at most 2 decimal places.",
        ),
    ),
)
def test_owner_labor_validation_preserves_value(
    client, value, expected_error
):
    form_data = valid_event_inputs()
    form_data["owner_labor_pay"] = value

    response = client.post("/events/new", data=form_data)

    assert expected_error in response.data
    assert f'value="{value}"'.encode() in response.data


def test_invalid_labor_does_not_save_event_records(client, database_path):
    form_data = valid_event_inputs()
    form_data["employee_labor_rate"] = ["0"]
    form_data["employee_labor_hours"] = ["4"]

    client.post("/events/new", data=form_data)

    with sqlite3.connect(database_path) as database:
        event_count = database.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]
        scenario_count = database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0]
    assert (event_count, scenario_count) == (0, 0)
