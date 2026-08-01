import re

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
    }


def opening_tag(response_data: bytes, element_id: str) -> bytes:
    match = re.search(
        rb"<[^>]+id=\"" + element_id.encode() + rb"\"[^>]*>",
        response_data,
        re.DOTALL,
    )
    assert match is not None
    return match.group()


def test_demand_fields_present_with_conditional_custom_sales(client):
    response = client.get("/events/new")
    page = response.data.decode()

    assert "Revenue inputs" in page
    assert "Estimated attendance" in page
    assert "Other competing food vendors" in page
    assert "Do not include your own business." in page
    assert "Percentage of attendees expected to buy food" in page
    assert "Average order sale amount ($)" in page
    assert "Estimated sales preview" not in page
    assert "Use a custom expected sales amount" not in page
    assert "Early demand estimate" not in page
    script = client.get("/static/js/event_inputs.js").data.decode()
    assert "/event-inputs/warnings" in script


def test_about_estimates_is_collapsed_and_can_be_toggled(client):
    response = client.get("/events/new")

    assert b"About estimates" in response.data
    assert b"<details" in response.data
    assert b"<details open" not in response.data


def test_weather_percentage_guidance_and_accessible_disclosure(client):
    page = client.get("/events/new").data.decode()

    assert "What do the weather percentages mean?" in page
    assert "estimated reduction in event attendance caused" in page
    assert "final estimated attendance reduction after" in page
    assert "5% base reduction" in page
    assert "Partially covered applies 75%" in page
    assert "3.75%" in page
    assert "planning estimates, not guaranteed attendance outcomes" in page


def test_warning_preview_is_structured_and_performs_no_writes(client, app):
    from tests.test_complete_event_inputs_workflow import complete_event_inputs

    form_data = complete_event_inputs()
    form_data["manual_food_cost_total"] = "9000"
    response = client.post("/event-inputs/warnings", data=form_data)

    payload = response.get_json()
    assert payload["ready"] is True
    assert all(set(item) == {"code", "severity", "message"}
               for item in payload["warnings"])
    with app.app_context():
        from app.database import get_database
        database = get_database()
        assert database.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0] == 0


def test_incomplete_warning_preview_returns_no_stale_warning(client):
    response = client.post(
        "/event-inputs/warnings",
        data={"estimated_attendance": "1000"},
    )
    assert response.get_json() == {"ready": False, "warnings": []}


def test_warning_javascript_debounces_and_rejects_stale_responses(client):
    script = client.get("/static/js/event_inputs.js").data.decode()
    assert "AbortController" in script
    assert "warningRequestNumber" in script
    assert "requestNumber !== warningRequestNumber" in script


def test_weather_choices_show_selected_reductions(client):
    page = client.get("/events/new").data.decode()

    assert "Favorable / normal — 0%" in page
    assert "Minor concern — 5%" in page
    assert "Moderate adverse weather — 15%" in page
    assert "Significant adverse weather — 30%" in page
    assert "Severe disruption risk — 50%" in page
    assert ">Custom<" not in page
    assert "Custom" in page


def test_event_protection_is_hidden_until_weather_is_valid(client):
    response = client.get("/events/new")

    assert b"hidden" in opening_tag(response.data, "custom-weather-field")
    assert b"hidden" in opening_tag(response.data, "event-protection-field")

    form_data = valid_event_inputs()
    form_data["weather_outlook"] = ""
    response = client.post("/events/new", data=form_data)
    assert b"Choose the weather outlook." in response.data
    assert b"hidden" in opening_tag(
        response.data, "event-protection-field"
    )


def test_effective_reductions_are_displayed_for_selected_weather(client):
    form_data = valid_event_inputs()
    form_data["location"] = ""

    page = client.post("/events/new", data=form_data).data.decode()

    assert "Fully indoors — <span" in page
    assert 'data-protection="fully_indoors">2.25</span>%' in page
    assert (
        'data-protection="covered_reliable_seating">7.5</span>%'
        in page
    )
    assert 'data-protection="partially_covered">11.25</span>%' in page
    assert 'data-protection="fully_outdoors">15</span>%' in page
    assert "applies 15%" not in page


def test_custom_weather_requires_valid_reduction_before_protection(client):
    form_data = valid_event_inputs()
    form_data["weather_outlook"] = "custom"
    form_data["custom_weather_reduction"] = ""

    response = client.post("/events/new", data=form_data)

    assert b"Custom weather reduction is required." in response.data
    assert b"hidden" not in opening_tag(
        response.data, "custom-weather-field"
    )
    assert b"hidden" in opening_tag(
        response.data, "event-protection-field"
    )


def test_custom_weather_displays_effective_reductions_and_preserves_value(
    client,
):
    form_data = valid_event_inputs()
    form_data["location"] = ""
    form_data["weather_outlook"] = "custom"
    form_data["custom_weather_reduction"] = "20"
    form_data["event_protection"] = "fully_indoors"

    response = client.post("/events/new", data=form_data)
    page = response.data.decode()

    assert 'value="20"' in page
    assert b"hidden" not in opening_tag(
        response.data, "event-protection-field"
    )
    assert 'data-protection="fully_indoors">3</span>%' in page
    assert 'data-protection="fully_outdoors">20</span>%' in page


def test_event_protection_is_required_after_weather_selection(client):
    form_data = valid_event_inputs()
    form_data["event_protection"] = ""

    response = client.post("/events/new", data=form_data)

    assert b"Choose the event protection." in response.data


def test_initial_submission_preserves_custom_expected_sales(client):
    form_data = valid_event_inputs()
    form_data["revenue_method"] = "manual_sales"
    form_data["expected_sales_amount"] = "5000"
    form_data["location"] = ""
    response = client.post("/events/new", data=form_data)
    assert b'value="manual_sales"' in response.data
    assert b'value="5000"' in response.data
    custom_field = response.data.split(b'id="custom-sales-field"', 1)[1].split(b">", 1)[0]
    assert b"hidden" not in custom_field


def test_calculated_estimate_state_clears_hidden_custom_sales(client):
    form_data = valid_event_inputs()
    form_data["location"] = ""
    form_data["revenue_method"] = "attendance"
    form_data["expected_sales_amount"] = "9999"

    response = client.post("/events/new", data=form_data)

    assert b'value="attendance"' in response.data
    assert b'value="9999"' not in response.data
    custom_field = response.data.split(b'id="custom-sales-field"', 1)[1].split(b">", 1)[0]
    assert b"hidden" in custom_field


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "expected_error"),
    (
        (
            "estimated_attendance",
            "-1",
            b"Estimated attendance cannot be negative.",
        ),
        (
            "estimated_attendance",
            "1.5",
            b"Estimated attendance must be a whole number.",
        ),
        (
            "other_competing_food_vendors",
            "-1",
            b"Other competing food vendors cannot be negative.",
        ),
        (
            "expected_food_buyer_percentage",
            "101",
            b"Percentage expected to buy food must be between 0 and 100.",
        ),
        (
            "expected_food_buyer_percentage",
            "10.001",
            b"Percentage expected to buy food can have at most 2 decimal places.",
        ),
        (
            "other_competing_food_vendors",
            "1.5",
            b"Other competing food vendors must be a whole number.",
        ),
        (
            "average_order_sale_amount",
            "-1",
            b"Average order sale amount cannot be negative.",
        ),
    ),
)
def test_revenue_validation_preserves_input(
    client, field_name, invalid_value, expected_error
):
    form_data = valid_event_inputs()
    form_data[field_name] = invalid_value

    response = client.post("/events/new", data=form_data)

    assert expected_error in response.data
    assert f'value="{invalid_value}"'.encode() in response.data
    assert b'value="Summer Festival"' in response.data


@pytest.mark.parametrize("percentage", ("0", "100"))
def test_food_buyer_percentage_inclusive_bounds_preview(client, percentage):
    form_data = valid_event_inputs()
    form_data["expected_food_buyer_percentage"] = percentage

    response = client.post(
        "/event-inputs/demand-preview", data=form_data
    )

    assert response.status_code == 200
    assert response.get_json()["ready"] is True


def test_demand_preview_uses_weather_and_includes_customer_vendor(client):
    response = client.post(
        "/event-inputs/demand-preview",
        data=valid_event_inputs(),
    )

    preview = response.get_json()
    assert preview["ready"] is True
    assert preview["weather_adjusted_attendance"] == "850"
    assert preview["total_expected_food_buyers"] == "85"
    assert preview["total_food_vendors"] == 6
    assert preview["equal_share_percentage"].startswith(
        "16.66666666666666666666666667"
    )
    assert preview["estimated_business_buyers"] == "14"


def test_demand_preview_allows_zero_other_vendors(client):
    form_data = valid_event_inputs()
    form_data["other_competing_food_vendors"] = "0"

    preview = client.post(
        "/event-inputs/demand-preview", data=form_data
    ).get_json()

    assert preview["ready"] is True
    assert preview["total_food_vendors"] == 1
    assert preview["estimated_business_buyers"] == "85"


def test_invalid_demand_preview_is_safe_and_does_not_save(client, app):
    form_data = valid_event_inputs()
    form_data["expected_food_buyer_percentage"] = ""

    response = client.post(
        "/event-inputs/demand-preview", data=form_data
    )

    assert response.status_code == 200
    assert response.get_json()["ready"] is False
    with app.app_context():
        from app.database import get_database

        database = get_database()
        assert database.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0] == 0
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0] == 0


def test_demand_preview_adds_break_even_comparison_when_costs_are_ready(
    client,
):
    form_data = valid_event_inputs()
    form_data.update(
        {
            "food_cost_method_choice": "sales_percentage",
            "food_cost_method": "sales_percentage",
            "average_food_cost_per_order": "",
            "food_cost_percentage": "30",
            "manual_food_cost_total": "",
            "owner_labor_pay": "",
            "travel_cost": "",
            "parking_cost": "",
            "permit_cost": "",
            "generator_utility_cost": "",
            "card_sales_percentage": "80",
            "card_processing_percentage": "3",
            "vendor_booking_fee": "",
            "organizer_commission_percentage": "",
            "fixed_card_processing_fee": "",
            "profit_target_type": "profit_amount",
            "minimum_profit_amount": "300",
            "minimum_profit_margin": "",
        }
    )

    preview = client.post(
        "/event-inputs/demand-preview", data=form_data
    ).get_json()

    assert preview["ready"] is True
    assert preview["break_even_customers"] == 5
    assert "meets or exceeds" in preview["break_even_message"]
