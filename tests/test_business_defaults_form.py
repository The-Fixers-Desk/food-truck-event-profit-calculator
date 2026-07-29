import sqlite3
from pathlib import Path

from app import create_app


def test_hidden_profit_target_fields_override_form_field_display():
    stylesheet = (
        Path(__file__).parents[1] / "app" / "static" / "css" / "forms.css"
    ).read_text(encoding="utf-8")

    assert ".target-field[hidden]" in stylesheet
    hidden_rule = stylesheet.split(".target-field[hidden]", 1)[1].split(
        "}", 1
    )[0]
    assert "display: none;" in hidden_rule


def valid_form_data() -> dict[str, str | list[str]]:
    return {
        "business_name": "Example Food Truck",
        "average_order_sale_amount": "15.00",
        "food_cost_percentage": "30",
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


def test_defaults_page_shows_correct_fields(client):
    response = client.get("/defaults")

    assert response.status_code == 200
    assert b"Average order sale amount" in response.data
    assert b"Default travel cost" in response.data
    assert b"Hourly labor rate" in response.data
    assert b"Total hours paid at that rate" in response.data
    assert b"Default owner labor pay ($)" in response.data
    assert (
        b"Optional flat amount you normally pay yourself for working an event."
        in response.data
    )
    assert b"How do you decide whether an event is worth accepting?" in (
        response.data
    )
    assert b"Minimum profit amount" in response.data
    assert b"Minimum profit margin" in response.data
    assert b"Paid staff" not in response.data
    assert b"Vehicle cost per mile" not in response.data


def test_initial_profit_target_inputs_are_hidden(client):
    response = client.get("/defaults")

    assert b'id="profit-amount-field" class="form-field target-field"\n        hidden' in response.data
    assert b'id="profit-margin-field" class="form-field target-field"\n        hidden' in response.data


def test_saved_profit_amount_shows_only_amount_field(client):
    client.post("/defaults", data=valid_form_data())

    response = client.get("/defaults")

    assert b'id="profit-amount-field" class="form-field target-field"\n        >' in response.data
    assert b'id="profit-margin-field" class="form-field target-field"\n        hidden' in response.data


def test_saved_profit_margin_shows_only_margin_field(client):
    form_data = valid_form_data()
    form_data["profit_target_type"] = "profit_margin"
    form_data["minimum_profit_amount"] = ""
    form_data["minimum_profit_margin"] = "20"
    client.post("/defaults", data=form_data)

    response = client.get("/defaults")

    assert b'id="profit-amount-field" class="form-field target-field"\n        hidden' in response.data
    assert b'id="profit-margin-field" class="form-field target-field"\n        >' in response.data


def test_valid_defaults_and_labor_entries_are_saved(client, database_path):
    response = client.post("/defaults", data=valid_form_data())

    assert response.status_code == 302
    with sqlite3.connect(database_path) as database:
        defaults_row = database.execute(
            """
            SELECT average_order_sale_amount_cents,
                   default_travel_cost_cents,
                   default_owner_labor_pay_cents
            FROM business_defaults WHERE id = 1
            """
        ).fetchone()
        labor_rows = database.execute(
            """
            SELECT hourly_rate_cents, total_paid_minutes
            FROM business_default_labor_entries ORDER BY position
            """
        ).fetchall()

    assert defaults_row == (1500, 7500, 12500)
    assert labor_rows == [(1800, 720), (2500, 240)]


def test_saved_labor_entries_load_after_app_restart(client, database_path):
    client.post("/defaults", data=valid_form_data())
    restarted_app = create_app(
        {"DATABASE": database_path, "SECRET_KEY": "test", "TESTING": True}
    )

    response = restarted_app.test_client().get("/defaults")

    assert response.data.count(b'name="labor_rate"') == 3
    assert b'value="18"' in response.data
    assert b'value="12"' in response.data
    assert b'value="25"' in response.data
    assert b'value="4"' in response.data
    assert b'value="profit_amount"' in response.data
    assert b'value="300"' in response.data
    assert b'name="default_owner_labor_pay"' in response.data
    assert b'value="125"' in response.data


def test_removing_labor_entry_persists(client, database_path):
    client.post("/defaults", data=valid_form_data())
    changed = valid_form_data()
    changed["labor_rate"] = ["25.00"]
    changed["labor_hours"] = ["4"]

    client.post("/defaults", data=changed)

    with sqlite3.connect(database_path) as database:
        rows = database.execute(
            """
            SELECT hourly_rate_cents FROM business_default_labor_entries
            """
        ).fetchall()
    assert rows == [(2500,)]


def test_blank_optional_travel_cost_is_saved_as_null(client, database_path):
    form_data = valid_form_data()
    form_data["default_travel_cost"] = ""

    client.post("/defaults", data=form_data)

    with sqlite3.connect(database_path) as database:
        value = database.execute(
            "SELECT default_travel_cost_cents FROM business_defaults"
        ).fetchone()[0]
    assert value is None


def test_blank_owner_labor_pay_is_saved_as_null(client, database_path):
    form_data = valid_form_data()
    form_data["default_owner_labor_pay"] = ""

    client.post("/defaults", data=form_data)

    with sqlite3.connect(database_path) as database:
        value = database.execute(
            "SELECT default_owner_labor_pay_cents FROM business_defaults"
        ).fetchone()[0]
    assert value is None


def test_invalid_owner_labor_pay_is_preserved_without_changing_saved_data(
    client, database_path
):
    client.post("/defaults", data=valid_form_data())
    invalid = valid_form_data()
    invalid["default_owner_labor_pay"] = "12.345"

    response = client.post("/defaults", data=invalid)

    assert b"Default owner labor pay can have at most 2 decimal places." in (
        response.data
    )
    assert b'value="12.345"' in response.data
    with sqlite3.connect(database_path) as database:
        value = database.execute(
            "SELECT default_owner_labor_pay_cents FROM business_defaults"
        ).fetchone()[0]
    assert value == 12500


def test_negative_owner_labor_pay_is_rejected(client):
    form_data = valid_form_data()
    form_data["default_owner_labor_pay"] = "-1"

    response = client.post("/defaults", data=form_data)

    assert b"Default owner labor pay must be 0 or more." in response.data


def test_profit_margin_choice_saves_only_margin(client, database_path):
    form_data = valid_form_data()
    form_data["profit_target_type"] = "profit_margin"
    form_data["minimum_profit_amount"] = "999"
    form_data["minimum_profit_margin"] = "20"

    client.post("/defaults", data=form_data)

    with sqlite3.connect(database_path) as database:
        row = database.execute(
            """
            SELECT profit_target_type, minimum_profit_amount_cents,
                   minimum_profit_margin_basis_points
            FROM business_defaults
            """
        ).fetchone()
    assert row == ("profit_margin", None, 2000)


def test_profit_target_choice_and_value_are_required(client):
    no_choice = valid_form_data()
    no_choice["profit_target_type"] = ""
    response = client.post("/defaults", data=no_choice)
    assert b"Choose how you evaluate an event." in response.data

    missing_value = valid_form_data()
    missing_value["minimum_profit_amount"] = ""
    response = client.post("/defaults", data=missing_value)
    assert b"Minimum profit amount is required." in response.data


def test_invalid_profit_target_preserves_choice_and_does_not_save(
    client, database_path
):
    client.post("/defaults", data=valid_form_data())
    invalid = valid_form_data()
    invalid["profit_target_type"] = "profit_margin"
    invalid["minimum_profit_amount"] = "999"
    invalid["minimum_profit_margin"] = "101"

    response = client.post("/defaults", data=invalid)

    assert b"Minimum profit margin must be between 0 and 100." in response.data
    assert b'value="profit_margin"' in response.data
    assert b'value="101"' in response.data
    assert b'value="999"' not in response.data
    with sqlite3.connect(database_path) as database:
        row = database.execute(
            """
            SELECT profit_target_type, minimum_profit_amount_cents,
                   minimum_profit_margin_basis_points
            FROM business_defaults
            """
        ).fetchone()
    assert row == ("profit_amount", 30000, None)


def test_invalid_labor_preserves_entries_and_does_not_change_database(
    client, database_path
):
    client.post("/defaults", data=valid_form_data())
    invalid = valid_form_data()
    invalid["business_name"] = "Should Not Save"
    invalid["labor_rate"] = ["-1", "not-a-number"]
    invalid["labor_hours"] = ["12", "-2"]

    response = client.post("/defaults", data=invalid)

    assert b"Hourly labor rate cannot be negative." in response.data
    assert b"Hourly labor rate must be a number." in response.data
    assert b"Total hours paid at that rate cannot be negative." in response.data
    assert b'value="-1"' in response.data
    assert b'value="not-a-number"' in response.data
    with sqlite3.connect(database_path) as database:
        name = database.execute(
            "SELECT business_name FROM business_defaults"
        ).fetchone()[0]
        count = database.execute(
            "SELECT COUNT(*) FROM business_default_labor_entries"
        ).fetchone()[0]
    assert name == "Example Food Truck"
    assert count == 2


def test_at_least_one_labor_entry_is_required(client):
    form_data = valid_form_data()
    form_data["labor_rate"] = []
    form_data["labor_hours"] = []

    response = client.post("/defaults", data=form_data)

    assert b"Add at least one labor entry." in response.data


def test_successful_save_shows_confirmation(client):
    response = client.post(
        "/defaults", data=valid_form_data(), follow_redirects=True
    )
    assert b"Business defaults saved successfully." in response.data
