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
    )

    assert defaults.default_travel_cost is None
    assert defaults.default_owner_labor_pay is None
    assert defaults.profit_target_type is None
    assert defaults.minimum_profit_amount is None
    assert defaults.minimum_profit_margin is None


def test_business_defaults_are_immutable(business_defaults):
    with pytest.raises(FrozenInstanceError):
        business_defaults.average_order_sale_amount = Decimal("20.00")


def test_labor_defaults_are_immutable(business_defaults):
    with pytest.raises(FrozenInstanceError):
        business_defaults.labor_entries[0].hourly_rate = Decimal("20.00")
