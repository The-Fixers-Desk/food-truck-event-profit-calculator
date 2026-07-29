import sqlite3
import re
from pathlib import Path

import pytest

from app import create_app
from app.database import business_defaults_setup_is_complete


def first_setup_data() -> dict[str, str | list[str]]:
    return {
        "business_name": "",
        "average_order_sale_amount": "15.00",
        "food_cost_percentage": "30",
        "card_sales_percentage": "80",
        "card_processing_percentage": "3",
        "default_travel_cost": "",
        "default_owner_labor_pay": "",
        "profit_target_type": "profit_amount",
        "minimum_profit_amount": "300",
        "minimum_profit_margin": "",
        "labor_rate": ["18.00"],
        "labor_hours": ["12"],
    }


def table_counts(database_path: Path) -> tuple[int, int]:
    with sqlite3.connect(database_path) as database:
        defaults_count = database.execute(
            "SELECT COUNT(*) FROM business_defaults"
        ).fetchone()[0]
        labor_count = database.execute(
            "SELECT COUNT(*) FROM business_default_labor_entries"
        ).fetchone()[0]
    return defaults_count, labor_count


def test_fresh_database_contains_no_business_defaults(database_path, app):
    assert table_counts(database_path) == (0, 0)


def test_fresh_defaults_page_has_blank_customer_values(client):
    response = client.get("/defaults")

    blank_fields = (
        "business_name",
        "average_order_sale_amount",
        "food_cost_percentage",
        "card_sales_percentage",
        "card_processing_percentage",
        "default_travel_cost",
        "default_owner_labor_pay",
        "minimum_profit_amount",
        "minimum_profit_margin",
        "labor_rate",
        "labor_hours",
    )
    for field_name in blank_fields:
        input_tag = re.search(
            rb"<input[^>]*name=\""
            + field_name.encode()
            + rb"\"[^>]*>",
            response.data,
            re.DOTALL,
        )
        assert input_tag is not None
        assert b'value=""' in input_tag.group()
    assert b'value="Example Food Truck"' not in response.data
    assert b'value="profit_amount"' in response.data
    assert b'value="profit_margin"' in response.data
    assert b"checked" not in response.data


def test_first_setup_saves_with_every_optional_field_blank(
    client, database_path
):
    response = client.post("/defaults", data=first_setup_data())

    assert response.status_code == 302
    with sqlite3.connect(database_path) as database:
        row = database.execute(
            """
            SELECT business_name, default_travel_cost_cents,
                   default_owner_labor_pay_cents,
                   minimum_profit_margin_basis_points
            FROM business_defaults
            """
        ).fetchone()
    assert row == ("", None, None, None)


@pytest.mark.parametrize(
    "required_field",
    (
        "average_order_sale_amount",
        "food_cost_percentage",
        "card_sales_percentage",
        "card_processing_percentage",
    ),
)
def test_missing_required_main_fields_are_rejected(
    client, database_path, required_field
):
    form_data = first_setup_data()
    form_data[required_field] = ""

    response = client.post("/defaults", data=form_data)

    assert response.status_code == 200
    assert b"is required." in response.data
    assert table_counts(database_path) == (0, 0)


def test_first_invalid_submission_leaves_both_tables_empty(
    client, database_path
):
    form_data = first_setup_data()
    form_data["labor_rate"] = ["-1"]

    response = client.post("/defaults", data=form_data)

    assert response.status_code == 200
    assert table_counts(database_path) == (0, 0)


def test_setup_complete_is_false_before_saving(app):
    with app.app_context():
        assert business_defaults_setup_is_complete() is False


def test_setup_complete_is_true_after_saving(client, app):
    client.post("/defaults", data=first_setup_data())

    with app.app_context():
        assert business_defaults_setup_is_complete() is True


def test_setup_complete_remains_true_after_restart(client, database_path):
    client.post("/defaults", data=first_setup_data())
    restarted_app = create_app(
        {"DATABASE": database_path, "SECRET_KEY": "test", "TESTING": True}
    )

    with restarted_app.app_context():
        assert business_defaults_setup_is_complete() is True


def test_defaults_page_includes_labor_add_and_remove_controls(client):
    response = client.get("/defaults")

    assert b'id="add-labor"' in response.data
    assert b"Add labor entry" in response.data
    assert b'class="remove-labor button-secondary"' in response.data
    assert b"Remove" in response.data
