from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.models import BusinessDefaults, LaborDefault


@pytest.fixture()
def business_defaults() -> BusinessDefaults:
    return BusinessDefaults(
        business_name="Example Food Truck",
        average_order_sale_amount=Decimal("15.00"),
        food_cost_percentage=Decimal("0.30"),
        card_sales_percentage=Decimal("0.80"),
        card_processing_percentage=Decimal("0.03"),
        labor_entries=(
            LaborDefault(Decimal("18.00"), Decimal("12.00")),
            LaborDefault(Decimal("25.00"), Decimal("4.00")),
        ),
        default_owner_labor_pay=Decimal("125.00"),
        profit_target_type="profit_amount",
        minimum_profit_amount=Decimal("300.00"),
        default_travel_cost=Decimal("75.00"),
    )


def test_business_defaults_store_expected_values(business_defaults):
    assert business_defaults.average_order_sale_amount == Decimal("15.00")
    assert len(business_defaults.labor_entries) == 2
    assert business_defaults.labor_entries[0].total_hours_paid == Decimal("12")
    assert business_defaults.default_travel_cost == Decimal("75.00")
    assert business_defaults.default_owner_labor_pay == Decimal("125.00")


def test_optional_values_can_be_omitted():
    defaults = BusinessDefaults(
        business_name="Example Food Truck",
        average_order_sale_amount=Decimal("15.00"),
        food_cost_percentage=Decimal("0.30"),
        card_sales_percentage=Decimal("0.80"),
        card_processing_percentage=Decimal("0.03"),
        labor_entries=(LaborDefault(Decimal("18"), Decimal("12")),),
        profit_target_type="profit_margin",
        minimum_profit_margin=Decimal("0.20"),
    )

    assert defaults.default_travel_cost is None
    assert defaults.default_owner_labor_pay is None
    assert defaults.profit_target_type == "profit_margin"
    assert defaults.minimum_profit_amount is None
    assert defaults.minimum_profit_margin == Decimal("0.20")


def test_business_defaults_are_immutable(business_defaults):
    with pytest.raises(FrozenInstanceError):
        business_defaults.average_order_sale_amount = Decimal("20.00")


def test_labor_defaults_are_immutable(business_defaults):
    with pytest.raises(FrozenInstanceError):
        business_defaults.labor_entries[0].hourly_rate = Decimal("20.00")


@pytest.mark.parametrize(
    ("hourly_rate", "total_hours"),
    [
        (Decimal("-1"), Decimal("1")),
        (Decimal("1"), Decimal("-1")),
    ],
)
def test_labor_defaults_reject_negative_values(hourly_rate, total_hours):
    with pytest.raises(ValueError):
        LaborDefault(hourly_rate, total_hours)


def valid_defaults_values() -> dict:
    return {
        "business_name": "Example Food Truck",
        "average_order_sale_amount": Decimal("15"),
        "food_cost_percentage": Decimal("0.30"),
        "card_sales_percentage": Decimal("0.80"),
        "card_processing_percentage": Decimal("0.03"),
        "labor_entries": (LaborDefault(Decimal("18"), Decimal("12")),),
        "profit_target_type": "profit_amount",
        "minimum_profit_amount": Decimal("300"),
    }


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("average_order_sale_amount", Decimal("-1")),
        ("default_travel_cost", Decimal("-1")),
        ("default_owner_labor_pay", Decimal("-1")),
        ("minimum_profit_amount", Decimal("-1")),
        ("food_cost_percentage", Decimal("-0.01")),
        ("food_cost_percentage", Decimal("1.01")),
        ("card_sales_percentage", Decimal("-0.01")),
        ("card_processing_percentage", Decimal("1.01")),
    ],
)
def test_business_defaults_reject_invalid_ranges(field_name, invalid_value):
    values = valid_defaults_values()
    values[field_name] = invalid_value

    with pytest.raises(ValueError):
        BusinessDefaults(**values)


def test_business_defaults_require_labor_entries():
    values = valid_defaults_values()
    values["labor_entries"] = ()

    with pytest.raises(ValueError):
        BusinessDefaults(**values)


@pytest.mark.parametrize("target_type", ["", "unknown", None])
def test_business_defaults_reject_invalid_profit_target_type(target_type):
    values = valid_defaults_values()
    values["profit_target_type"] = target_type

    with pytest.raises(ValueError):
        BusinessDefaults(**values)


@pytest.mark.parametrize(
    "values",
    [
        {
            "profit_target_type": "profit_amount",
            "minimum_profit_amount": None,
        },
        {
            "profit_target_type": "profit_margin",
            "minimum_profit_amount": None,
            "minimum_profit_margin": None,
        },
    ],
)
def test_business_defaults_require_selected_profit_target_value(values):
    defaults_values = valid_defaults_values()
    defaults_values.update(values)

    with pytest.raises(ValueError):
        BusinessDefaults(**defaults_values)


@pytest.mark.parametrize(
    "values",
    [
        {
            "profit_target_type": "profit_amount",
            "minimum_profit_margin": Decimal("0.20"),
        },
        {
            "profit_target_type": "profit_margin",
            "minimum_profit_margin": Decimal("0.20"),
        },
    ],
)
def test_business_defaults_reject_unselected_profit_target_value(values):
    defaults_values = valid_defaults_values()
    defaults_values.update(values)

    with pytest.raises(ValueError):
        BusinessDefaults(**defaults_values)


@pytest.mark.parametrize("margin", [Decimal("-0.01"), Decimal("1.01")])
def test_business_defaults_reject_invalid_profit_margin(margin):
    values = valid_defaults_values()
    values.update(
        {
            "profit_target_type": "profit_margin",
            "minimum_profit_amount": None,
            "minimum_profit_margin": margin,
        }
    )

    with pytest.raises(ValueError):
        BusinessDefaults(**values)
