import sqlite3

from werkzeug.datastructures import MultiDict

from app.event_inputs_form import validate_event_inputs


def saved_defaults_data() -> dict[str, str | list[str]]:
    return {
        "business_name": "Defaults Truck",
        "average_order_sale_amount": "15.00",
        "food_cost_method_choice": "sales_percentage",
        "food_cost_method": "sales_percentage",
        "average_food_cost_per_order": "",
        "food_cost_percentage": "30",
        "typical_food_cost_total": "",
        "card_sales_percentage": "80",
        "card_processing_percentage": "3",
        "default_travel_cost": "75",
        "default_owner_labor_pay": "125",
        "profit_target_type": "profit_amount",
        "minimum_profit_amount": "300",
        "minimum_profit_margin": "",
        "labor_rate": ["18.00", "25.00"],
        "labor_hours": ["12", "4"],
    }


def complete_event_inputs() -> dict[str, str | list[str]]:
    return {
        "event_name": "Summer Festival",
        "event_date": "2026-08-15",
        "start_time": "11:00",
        "location": "Town Square",
        "estimated_attendance": "1000",
        "other_competing_food_vendors": "5",
        "expected_food_buyer_percentage": "10",
        "average_order_sale_amount": "16.50",
        "weather_outlook": "custom",
        "custom_weather_reduction": "20",
        "event_protection": "partially_covered",
        "revenue_method": "manual_sales",
        "expected_sales_amount": "5000",
        "food_cost_method_choice": "manual_event_total",
        "food_cost_method": "manual_event_total",
        "average_food_cost_per_order": "",
        "food_cost_percentage": "",
        "manual_food_cost_total": "900",
        "owner_labor_pay": "150",
        "employee_labor_rate": ["20", "25"],
        "employee_labor_hours": ["10", "4"],
        "travel_cost": "80",
        "parking_cost": "20",
        "permit_cost": "100",
        "generator_utility_cost": "35",
        "card_sales_percentage": "75",
        "card_processing_percentage": "3.25",
        "vendor_booking_fee": "200",
        "organizer_commission_percentage": "5",
        "fixed_card_processing_fee": "0.30",
        "profit_target_type": "profit_margin",
        "minimum_profit_amount": "",
        "minimum_profit_margin": "20",
        "additional_cost_name": ["Ice", "Extra propane"],
        "additional_cost_amount": ["40", "60"],
    }


def add_default_baselines(form_data: dict) -> None:
    baseline_values = {
        "average_order_sale_amount": "15",
        "food_cost_method": "sales_percentage",
        "average_food_cost_per_order": "",
        "food_cost_percentage": "30",
        "manual_food_cost_total": "",
        "card_sales_percentage": "80",
        "card_processing_percentage": "3",
        "owner_labor_pay": "125",
        "travel_cost": "75",
        "profit_target_type": "profit_amount",
        "minimum_profit_amount": "300",
        "minimum_profit_margin": "",
    }
    for name, value in baseline_values.items():
        form_data[f"baseline_{name}"] = value
    form_data["baseline_employee_labor_rate"] = ["18", "25"]
    form_data["baseline_employee_labor_hours"] = ["12", "4"]


def test_saved_business_defaults_prefill_new_event_without_business_name(
    client,
):
    client.post("/defaults", data=saved_defaults_data())

    response = client.get("/")
    page = response.data.decode()

    assert 'name="event_name"' in page
    assert 'value="Defaults Truck"' not in page
    for value in ("15", "30", "80", "3", "18", "12", "25", "4", "125", "75", "300"):
        assert f'value="{value}"' in page
    assert 'value="sales_percentage"' in page
    assert 'value="profit_amount"' in page
    assert page.count("From defaults") >= 8


def test_event_specific_fields_remain_blank_when_defaults_are_applied(client):
    client.post("/defaults", data=saved_defaults_data())

    page = client.get("/").data.decode()

    for field_name in (
        "event_name",
        "event_date",
        "start_time",
        "location",
        "estimated_attendance",
        "other_competing_food_vendors",
        "weather_outlook",
        "parking_cost",
        "permit_cost",
        "generator_utility_cost",
        "vendor_booking_fee",
        "organizer_commission_percentage",
        "fixed_card_processing_fee",
    ):
        section = page.split(f'name="{field_name}"', 1)[1].split(">", 1)[0]
        assert 'value=""' in section or field_name == "weather_outlook"


def test_event_inputs_page_does_not_crash_without_defaults(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"From defaults" not in response.data
    assert b'name="average_order_sale_amount"' in response.data
    assert b'name="card_sales_percentage"' in response.data
    assert b'name="profit_target_type"' in response.data


def test_complete_valid_form_covers_every_section_without_saving(
    client, database_path
):
    form_data = complete_event_inputs()

    identity, values, errors = validate_event_inputs(
        MultiDict(form_data)
    )

    assert errors == {}
    assert identity.event_name == "Summer Festival"
    assert len(values["employee_labor"]) == 2
    assert len(values["additional_costs"]) == 2

    response = client.post("/", data=form_data)
    assert response.status_code == 200
    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0] == 0
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0] == 0


def test_event_overrides_survive_errors_and_do_not_modify_defaults(
    client, database_path
):
    client.post("/defaults", data=saved_defaults_data())
    before = _read_defaults(database_path)
    form_data = complete_event_inputs()
    add_default_baselines(form_data)
    form_data["event_name"] = ""

    response = client.post("/", data=form_data)

    assert b"Event name is required." in response.data
    for value in ("16.50", "900", "75", "3.25", "20", "150", "80"):
        assert f'value="{value}"'.encode() in response.data
    assert b"Changed for this event" in response.data
    assert _read_defaults(database_path) == before


def test_required_card_and_profit_target_validation(client):
    form_data = complete_event_inputs()
    form_data["card_sales_percentage"] = ""
    form_data["card_processing_percentage"] = "101"
    form_data["profit_target_type"] = "profit_amount"
    form_data["minimum_profit_amount"] = ""
    form_data["minimum_profit_margin"] = "99"

    response = client.post("/", data=form_data)

    assert b"Sales paid by card is required." in response.data
    assert b"Card-processing percentage must be between 0 and 100." in (
        response.data
    )
    assert b"Minimum profit amount is required." in response.data
    assert b'value="99"' not in response.data


def test_estimate_and_event_only_indicators_are_visible(client):
    page = client.get("/").data.decode()

    assert "Changes on this screen apply only to this event." in page
    assert page.count("Estimate") >= 5
    assert "About estimates" in page


def _read_defaults(database_path) -> tuple:
    with sqlite3.connect(database_path) as database:
        defaults_row = database.execute(
            """
            SELECT average_order_sale_amount_cents, food_cost_method,
                   food_cost_percentage_basis_points,
                   card_sales_basis_points, card_processing_basis_points,
                   default_owner_labor_pay_cents,
                   default_travel_cost_cents, profit_target_type,
                   minimum_profit_amount_cents
            FROM business_defaults WHERE id = 1
            """
        ).fetchone()
        labor_rows = database.execute(
            """
            SELECT position, hourly_rate_cents, total_paid_minutes
            FROM business_default_labor_entries ORDER BY position
            """
        ).fetchall()
    return defaults_row, tuple(labor_rows)
