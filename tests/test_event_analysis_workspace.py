import sqlite3

import pytest

from tests.test_complete_event_inputs_workflow import (
    complete_event_inputs,
    saved_defaults_data,
)


def test_valid_event_inputs_open_workspace_with_read_only_identity(client):
    response = client.post("/events/new", data=complete_event_inputs())
    page = response.data.decode()

    assert response.status_code == 200
    assert "<h1>Summer Festival</h1>" in page
    assert '<p class="page-eyebrow">Event Analysis</p>' in page
    assert "Summer Festival" in page
    assert "2026-08-15" in page
    assert "11:00" in page
    assert "Town Square" in page
    assert 'data-workspace="true"' in page
    assert "Adjustable assumptions" in page
    assert "Business results" in page


def test_invalid_event_inputs_remain_on_input_form(client):
    form_data = complete_event_inputs()
    form_data["estimated_attendance"] = ""

    response = client.post("/events/new", data=form_data)

    assert b"<h1>Enter the details for this event</h1>" in response.data
    assert b"Estimated attendance is required." in response.data
    assert b'data-workspace="true"' not in response.data


def test_workspace_contains_all_adjustable_groups_and_actions(client):
    page = client.post("/events/new", data=complete_event_inputs()).data.decode()

    for text in (
        "Demand and sales potential",
        "Food and transaction costs",
        "Labor",
        "Fixed event costs and fees",
        "Event and payment fees",
        "Profit target",
        "Additional costs",
        "Add employee labor",
        "Add another cost",
        "Reset changes",
        "Start new analysis",
        "Save as new scenario",
        "Overwrite current scenario",
    ):
        assert text in page
    assert ">Continue<" not in page
    assert 'id="open-save-analysis"' in page
    save_tag = page.split('id="open-save-analysis"', 1)[1].split(
        ">", 1
    )[0]
    assert "disabled" in save_tag
    new_mode = page.split('name="save_mode" value="new"', 1)[1].split(
        ">", 1
    )[0]
    assert "checked" in new_mode


def test_initial_workspace_displays_complete_calculation(client):
    page = client.post("/events/new", data=complete_event_inputs()).data.decode()

    assert "$5000" in page
    assert "custom_sales_assumption" in page
    assert "Exact break-even customers" not in page
    assert "Break-even buyers" in page
    assert 'name="revenue_method" value="attendance"' in page
    assert 'name="revenue_method" value="manual_sales"' in page


def test_live_endpoint_recalculates_demand_revenue_and_costs(client):
    form_data = complete_event_inputs()
    form_data["revenue_method"] = "attendance"
    form_data["expected_sales_amount"] = ""

    baseline = client.post(
        "/event-analysis/calculate", data=form_data
    ).get_json()
    form_data["estimated_attendance"] = "2000"
    form_data["other_competing_food_vendors"] = "0"
    form_data["expected_food_buyer_percentage"] = "50"
    form_data["weather_outlook"] = "favorable"
    form_data["custom_weather_reduction"] = "99"
    form_data["event_protection"] = "fully_outdoors"
    changed = client.post(
        "/event-analysis/calculate", data=form_data
    ).get_json()

    assert baseline["valid"] is True
    assert changed["valid"] is True
    assert changed["result"]["weather_adjusted_attendance"] == "2000"
    assert changed["result"]["total_expected_food_buyers"] == "1000"
    assert changed["result"]["total_food_vendors"] == "1"
    assert changed["result"]["expected_orders"] == "1000"
    assert changed["result"]["expected_sales"] == "16500"
    assert changed["result"]["fixed_card_processing_fees"] == "225"


def test_live_endpoint_supports_food_methods_labor_costs_and_target(client):
    form_data = complete_event_inputs()
    form_data.update(
        {
            "food_cost_method_choice": "average_per_order",
            "food_cost_method": "average_per_order",
            "average_food_cost_per_order": "4",
            "food_cost_percentage": "99",
            "manual_food_cost_total": "9999",
            "owner_labor_pay": "200",
            "organizer_commission_percentage": "10",
            "profit_target_type": "profit_amount",
            "minimum_profit_amount": "100",
            "minimum_profit_margin": "99",
        }
    )
    form_data["employee_labor_rate"] = ["30"]
    form_data["employee_labor_hours"] = ["5"]

    payload = client.post(
        "/event-analysis/calculate", data=form_data
    ).get_json()
    result = payload["result"]

    assert payload["valid"] is True
    assert result["food_and_packaging_cost"].startswith(
        "56.666666666666666666666666"
    )
    assert result["employee_labor_cost"] == "150"
    assert result["owner_labor_pay"] == "200"
    assert result["organizer_commission"] == "500"
    assert result["profit_target"]["target_type"] == "profit_amount"
    assert result["profit_target"]["is_met"] is True


@pytest.mark.parametrize(
    ("method", "field", "value", "expected"),
    (
        (
            "average_per_order",
            "average_food_cost_per_order",
            "4",
            "56.66666666666666666666666668",
        ),
        ("sales_percentage", "food_cost_percentage", "30", "1500"),
        ("manual_event_total", "manual_food_cost_total", "900", "900"),
    ),
)
def test_live_endpoint_supports_every_food_cost_method(
    client, method, field, value, expected
):
    form_data = complete_event_inputs()
    form_data.update(
        {
            "food_cost_method_choice": method,
            "food_cost_method": method,
            "average_food_cost_per_order": "",
            "food_cost_percentage": "",
            "manual_food_cost_total": "",
        }
    )
    form_data[field] = value

    payload = client.post(
        "/event-analysis/calculate", data=form_data
    ).get_json()

    assert payload["valid"] is True
    assert payload["result"]["food_and_packaging_cost"] == expected


def test_live_endpoint_handles_removed_repeatable_rows(client):
    form_data = complete_event_inputs()
    form_data["employee_labor_rate"] = []
    form_data["employee_labor_hours"] = []
    form_data["additional_cost_name"] = []
    form_data["additional_cost_amount"] = []

    payload = client.post(
        "/event-analysis/calculate", data=form_data
    ).get_json()

    assert payload["valid"] is True
    assert payload["result"]["employee_labor_cost"] == "0"
    assert payload["result"]["additional_event_costs"] == "155"


def test_live_endpoint_preserves_latest_results_contract_when_invalid(client):
    valid = complete_event_inputs()
    valid_payload = client.post(
        "/event-analysis/calculate", data=valid
    ).get_json()
    invalid = complete_event_inputs()
    invalid["employee_labor_rate"] = ["-1", "25"]

    invalid_payload = client.post(
        "/event-analysis/calculate", data=invalid
    ).get_json()

    assert valid_payload["valid"] is True
    assert invalid_payload["valid"] is False
    assert "result" not in invalid_payload
    assert invalid_payload["errors"]["employee_labor"][0][
        "hourly_rate"
    ]
    assert invalid_payload["status"] == (
        "Results have not updated. Correct the highlighted fields."
    )

    corrected_payload = client.post(
        "/event-analysis/calculate", data=valid
    ).get_json()
    assert corrected_payload["valid"] is True
    assert "errors" not in corrected_payload


def test_live_calculations_create_no_additional_records_or_default_changes(
    client, database_path
):
    client.post("/defaults", data=saved_defaults_data())
    with sqlite3.connect(database_path) as database:
        defaults_before = database.execute(
            "SELECT * FROM business_defaults"
        ).fetchone()

    client.post("/events/new", data=complete_event_inputs())
    client.post(
        "/event-analysis/calculate", data=complete_event_inputs()
    )

    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0] == 1
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0] == 1
        assert database.execute(
            "SELECT * FROM business_defaults"
        ).fetchone() == defaults_before


def test_start_new_analysis_returns_clean_event_inputs(client):
    client.post("/events/new", data=complete_event_inputs())

    response = client.get("/events/new")

    assert b"<h1>Enter the details for this event</h1>" in response.data
    assert b'value="Summer Festival"' not in response.data


def test_workspace_client_behavior_is_debounced_accessible_and_responsive(
    client,
):
    page = client.post("/events/new", data=complete_event_inputs()).data.decode()
    script = client.get("/static/js/event_inputs.js").data.decode()
    styles = client.get("/static/css/forms.css").data.decode()

    assert 'aria-live="polite"' in page
    assert "setTimeout(recalculateWorkspace, 300)" in script
    assert "AbortController" in script
    assert "requestNumber !== workspaceRequestNumber" in script
    assert "restoreWorkspaceBaseline" in script
    assert "workspaceSignature" in script
    assert "updateWorkspaceDirtyState" in script
    assert "workspaceBaseline = new FormData(workspaceForm)" in script
    assert "position: sticky" in styles
    assert "@media (max-width: 800px)" in styles
    assert "grid-row: auto" in styles
