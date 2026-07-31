import re
import sqlite3
from pathlib import Path

import pytest


def valid_event_inputs() -> dict[str, str]:
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
    }


def opening_tag(response_data: bytes, element_id: str) -> bytes:
    match = re.search(
        rb"<[^>]+id=\"" + element_id.encode() + rb"\"[^>]*>",
        response_data,
        re.DOTALL,
    )
    assert match is not None
    return match.group()


def test_food_cost_section_and_all_method_choices_are_present(client):
    page = client.get("/").data.decode()

    assert "Food and packaging costs" in page
    assert (
        "How do you want to estimate food and packaging costs for this event?"
        in page
    )
    assert "Average cost per order" in page
    assert "Percentage of sales" in page
    assert "Total for this event" in page
    assert "Use this method" in page


def test_food_cost_starts_with_average_selected_and_all_values_hidden(client):
    response = client.get("/")

    select_html = response.data.decode().split(
        'id="event_food_cost_method_choice"', 1
    )[1].split("</select>", 1)[0]
    assert 'value="average_per_order"' in select_html
    assert "selected" in select_html.split(
        'value="average_per_order"', 1
    )[1].split("</option>", 1)[0]
    assert b'value=""' in opening_tag(
        response.data, "event_food_cost_method"
    )
    for element_id in (
        "event-average-food-cost-field",
        "event-food-cost-percentage-field",
        "event-manual-food-cost-field",
    ):
        assert b"hidden" in opening_tag(response.data, element_id)


@pytest.mark.parametrize(
    ("method", "field_name", "value", "visible_field"),
    (
        (
            "average_per_order",
            "average_food_cost_per_order",
            "5.25",
            "event-average-food-cost-field",
        ),
        (
            "sales_percentage",
            "food_cost_percentage",
            "30",
            "event-food-cost-percentage-field",
        ),
        (
            "manual_event_total",
            "manual_food_cost_total",
            "750",
            "event-manual-food-cost-field",
        ),
    ),
)
def test_confirmed_food_cost_method_shows_only_its_matching_field(
    client, method, field_name, value, visible_field
):
    form_data = valid_event_inputs()
    form_data.update(
        {
            "food_cost_method_choice": method,
            "food_cost_method": method,
            "average_food_cost_per_order": "",
            "food_cost_percentage": "",
            "manual_food_cost_total": "",
            field_name: value,
            "location": "",
        }
    )

    response = client.post("/", data=form_data)

    assert b"hidden" not in opening_tag(response.data, visible_field)
    assert f'value="{value}"'.encode() in response.data
    hidden_fields = {
        "event-average-food-cost-field",
        "event-food-cost-percentage-field",
        "event-manual-food-cost-field",
    } - {visible_field}
    for element_id in hidden_fields:
        assert b"hidden" in opening_tag(response.data, element_id)


def test_switching_method_clears_previous_food_cost_value(client):
    form_data = valid_event_inputs()
    form_data.update(
        {
            "food_cost_method_choice": "sales_percentage",
            "food_cost_method": "sales_percentage",
            "average_food_cost_per_order": "99",
            "food_cost_percentage": "30",
            "location": "",
        }
    )

    response = client.post("/", data=form_data)

    assert b'value="30"' in response.data
    assert b'value="99"' not in response.data
    assert b"hidden" in opening_tag(
        response.data, "event-average-food-cost-field"
    )
    assert b"hidden" not in opening_tag(
        response.data, "event-food-cost-percentage-field"
    )


def test_use_method_button_does_not_submit_and_javascript_clears_old_value():
    template = (
        Path(__file__).parents[1] / "app" / "templates" / "calculator.html"
    ).read_text(encoding="utf-8")
    script = (
        Path(__file__).parents[1]
        / "app"
        / "static"
        / "js"
        / "event_inputs.js"
    ).read_text(encoding="utf-8")

    button = template.split(
        'id="confirm-event-food-cost-method"', 1
    )[1].split(">", 1)[0]
    assert 'type="button"' in button
    assert 'field.input.value = "";' in script
    assert "confirmedEventFoodMethod.value = nextMethod;" in script


def test_unconfirmed_food_cost_method_is_required(client):
    form_data = valid_event_inputs()
    form_data["food_cost_method"] = ""

    response = client.post("/", data=form_data)

    assert b"Choose and confirm a food and packaging cost method." in (
        response.data
    )


@pytest.mark.parametrize(
    ("method", "field_name", "invalid_value", "expected_error"),
    (
        (
            "average_per_order",
            "average_food_cost_per_order",
            "-1",
            b"Average food and packaging cost per order cannot be negative.",
        ),
        (
            "average_per_order",
            "average_food_cost_per_order",
            "1.234",
            b"Average food and packaging cost per order can have at most 2 decimal places.",
        ),
        (
            "sales_percentage",
            "food_cost_percentage",
            "101",
            b"Food and packaging cost percentage must be between 0 and 100.",
        ),
        (
            "manual_event_total",
            "manual_food_cost_total",
            "-1",
            b"Total food and packaging cost for this event cannot be negative.",
        ),
    ),
)
def test_food_cost_validation_preserves_invalid_input(
    client, method, field_name, invalid_value, expected_error
):
    form_data = valid_event_inputs()
    form_data.update(
        {
            "food_cost_method_choice": method,
            "food_cost_method": method,
            "average_food_cost_per_order": "",
            "food_cost_percentage": "",
            "manual_food_cost_total": "",
            field_name: invalid_value,
        }
    )

    response = client.post("/", data=form_data)

    assert expected_error in response.data
    assert f'value="{invalid_value}"'.encode() in response.data
    assert f'value="{method}"'.encode() in response.data


def test_confirmed_food_cost_survives_unrelated_validation_error(client):
    form_data = valid_event_inputs()
    form_data.update(
        {
            "location": "",
            "food_cost_method_choice": "sales_percentage",
            "food_cost_method": "sales_percentage",
            "average_food_cost_per_order": "",
            "food_cost_percentage": "30",
        }
    )

    response = client.post("/", data=form_data)

    assert b"Location is required." in response.data
    assert b'value="sales_percentage"' in response.data
    assert b'value="30"' in response.data
    assert b"hidden" not in opening_tag(
        response.data, "event-food-cost-percentage-field"
    )


def test_food_cost_form_does_not_save_events(client, database_path):
    client.post("/", data=valid_event_inputs())

    with sqlite3.connect(database_path) as database:
        event_count = database.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]
        scenario_count = database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0]
    assert (event_count, scenario_count) == (0, 0)
