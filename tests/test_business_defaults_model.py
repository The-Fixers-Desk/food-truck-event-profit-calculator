from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.models import BusinessDefaults


@pytest.fixture()
def business_defaults() -> BusinessDefaults:
    """Create a representative set of reusable business defaults."""
    return BusinessDefaults(
        business_name="Example Food Truck",
        average_order_value=Decimal("15.00"),
        food_cost_percentage=Decimal("0.30"),
        card_sales_percentage=Decimal("0.80"),
        card_processing_percentage=Decimal("0.03"),
        default_staff_count=2,
        hourly_labor_cost=Decimal("18.00"),
        setup_hours=Decimal("1.50"),
        cleanup_hours=Decimal("1.00"),
        vehicle_cost_per_mile=Decimal("0.75"),
        minimum_acceptable_profit=Decimal("300.00"),
        minimum_acceptable_margin=Decimal("0.20"),
    )


def test_business_defaults_store_expected_values(
    business_defaults: BusinessDefaults,
):
    """The model should preserve the supplied business assumptions."""
    assert business_defaults.business_name == "Example Food Truck"
    assert business_defaults.average_order_value == Decimal("15.00")
    assert business_defaults.default_staff_count == 2
    assert business_defaults.minimum_acceptable_margin == Decimal("0.20")


def test_optional_decision_thresholds_can_be_omitted():
    """Profit targets should be optional."""
    defaults = BusinessDefaults(
        business_name="Example Food Truck",
        average_order_value=Decimal("15.00"),
        food_cost_percentage=Decimal("0.30"),
        card_sales_percentage=Decimal("0.80"),
        card_processing_percentage=Decimal("0.03"),
        default_staff_count=2,
        hourly_labor_cost=Decimal("18.00"),
        setup_hours=Decimal("1.50"),
        cleanup_hours=Decimal("1.00"),
        vehicle_cost_per_mile=Decimal("0.75"),
    )

    assert defaults.minimum_acceptable_profit is None
    assert defaults.minimum_acceptable_margin is None


def test_business_defaults_are_immutable(
    business_defaults: BusinessDefaults,
):
    """Saved model instances should not be changed silently."""
    with pytest.raises(FrozenInstanceError):
        business_defaults.average_order_value = Decimal("20.00")