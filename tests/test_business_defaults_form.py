import sqlite3
from pathlib import Path

import pytest

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


def test_defaults_page_shows_correct_fields(client):
    response = client.get("/defaults")

    assert response.status_code == 200
    assert b"Average order sale amount" in response.data
    assert b"How do you usually estimate food and packaging costs?" in (
        response.data
    )
    assert b"Average cost per order" in response.data
    assert b"Percentage of sales" in response.data
    assert b"Typical total per event" in response.data
    assert b"Use this method" in response.data
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


def test_fresh_food_cost_defaults_to_average_without_showing_value(client):
    response = client.get("/defaults")

    assert (
        b'<option value="average_per_order"\n            \n'
        in response.data
        or b'value="average_per_order"' in response.data
    )
    assert b'id="food_cost_method" name="food_cost_method" type="hidden"\n        value=""' in response.data
    assert b'id="average-food-cost-field"\n        class="form-field target-field food-cost-field"\n        hidden' in response.data


def test_saved_percentage_method_shows_only_percentage_field(client):
    client.post("/defaults", data=valid_form_data())

    response = client.get("/defaults")

    assert b'value="sales_percentage"' in response.data
    assert b'id="food-cost-percentage-field"\n        class="form-field target-field food-cost-field"\n        >' in response.data
    assert b'value="30"' in response.data


def test_all_food_cost_methods_save_only_matching_value(
    client, database_path
):
    cases = (
        ("average_per_order", "5.25", "", "", (525, None, None)),
        ("sales_percentage", "", "30", "", (None, 3000, None)),
        ("typical_event_total", "", "", "750", (None, None, 75000)),
    )
    for method, average, percentage, total, expected in cases:
        form_data = valid_form_data()
        form_data.update(
            {
                "food_cost_method_choice": method,
                "food_cost_method": method,
                "average_food_cost_per_order": average,
                "food_cost_percentage": percentage,
                "typical_food_cost_total": total,
            }
        )
        response = client.post("/defaults", data=form_data)
        assert response.status_code == 302
        with sqlite3.connect(database_path) as database:
            row = database.execute(
                """
                SELECT average_food_cost_per_order_cents,
                       food_cost_percentage_basis_points,
                       typical_food_cost_total_cents
                FROM business_defaults
                """
            ).fetchone()
        assert row == expected


def test_unconfirmed_food_cost_method_is_rejected_without_saving(
    client, database_path
):
    form_data = valid_form_data()
    form_data["food_cost_method"] = ""

    response = client.post("/defaults", data=form_data)

    assert b"Choose and confirm a food and packaging cost method." in (
        response.data
    )
    with sqlite3.connect(database_path) as database:
        count = database.execute(
            "SELECT COUNT(*) FROM business_defaults"
        ).fetchone()[0]
    assert count == 0


def test_invalid_food_cost_value_is_preserved_without_changing_saved_data(
    client, database_path
):
    client.post("/defaults", data=valid_form_data())
    invalid = valid_form_data()
    invalid["food_cost_percentage"] = "101"

    response = client.post("/defaults", data=invalid)

    assert b"Food and packaging cost percentage must be between 0 and 100." in (
        response.data
    )
    assert b'value="101"' in response.data
    with sqlite3.connect(database_path) as database:
        value = database.execute(
            "SELECT food_cost_percentage_basis_points FROM business_defaults"
        ).fetchone()[0]
    assert value == 3000


@pytest.mark.parametrize(
    ("method", "field_name", "invalid_value", "message"),
    [
        (
            "average_per_order",
            "average_food_cost_per_order",
            "-1",
            "must be 0 or more",
        ),
        (
            "average_per_order",
            "average_food_cost_per_order",
            "1.234",
            "at most 2 decimal places",
        ),
        (
            "typical_event_total",
            "typical_food_cost_total",
            "-1",
            "must be 0 or more",
        ),
    ],
)
def test_food_cost_money_validation(
    client, method, field_name, invalid_value, message
):
    form_data = valid_form_data()
    form_data.update(
        {
            "food_cost_method_choice": method,
            "food_cost_method": method,
            "average_food_cost_per_order": "",
            "food_cost_percentage": "",
            "typical_food_cost_total": "",
            field_name: invalid_value,
        }
    )

    response = client.post("/defaults", data=form_data)

    assert message.encode() in response.data


def test_existing_percentage_default_is_migrated_and_loaded(tmp_path):
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as database:
        database.executescript(
            """
            CREATE TABLE business_defaults (
                id INTEGER PRIMARY KEY,
                business_name TEXT NOT NULL,
                average_order_sale_amount_cents INTEGER NOT NULL,
                food_cost_basis_points INTEGER NOT NULL,
                card_sales_basis_points INTEGER NOT NULL,
                card_processing_basis_points INTEGER NOT NULL,
                default_travel_cost_cents INTEGER,
                default_owner_labor_pay_cents INTEGER,
                profit_target_type TEXT,
                minimum_profit_amount_cents INTEGER,
                minimum_profit_margin_basis_points INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE business_default_labor_entries (
                id INTEGER PRIMARY KEY,
                business_defaults_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                hourly_rate_cents INTEGER NOT NULL,
                total_paid_minutes INTEGER NOT NULL
            );
            INSERT INTO business_defaults (
                id, business_name, average_order_sale_amount_cents,
                food_cost_basis_points, card_sales_basis_points,
                card_processing_basis_points, profit_target_type,
                minimum_profit_amount_cents
            )
            VALUES (
                1, 'Legacy Truck', 1500, 3000, 8000, 300,
                'profit_amount', 30000
            );
            INSERT INTO business_default_labor_entries (
                id, business_defaults_id, position, hourly_rate_cents,
                total_paid_minutes
            )
            VALUES (1, 1, 0, 1800, 720);
            """
        )
    migrated_app = create_app(
        {"DATABASE": database_path, "SECRET_KEY": "test", "TESTING": True}
    )

    response = migrated_app.test_client().get("/defaults")

    assert b'value="sales_percentage"' in response.data
    assert b'value="30"' in response.data
    with sqlite3.connect(database_path) as database:
        row = database.execute(
            """
            SELECT food_cost_method, food_cost_percentage_basis_points
            FROM business_defaults
            """
        ).fetchone()
    assert row == ("sales_percentage", 3000)


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
