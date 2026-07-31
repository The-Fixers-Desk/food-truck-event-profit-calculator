from dataclasses import FrozenInstanceError
from datetime import date, time
from decimal import Decimal

import pytest

from app.models import (
    AdditionalEventCost,
    DemandAssumptions,
    EmployeeLaborEntry,
    Event,
    EventIdentity,
    EventScenario,
    FoodCostAssumptions,
    PaymentAndOrganizerFees,
    ProfitTarget,
    RevenueAssumptions,
    WeatherAssumptions,
)


def valid_scenario(**changes) -> EventScenario:
    values = {
        "scenario_name": "Original estimate",
        "notes": "Customer estimate",
        "demand": DemandAssumptions(1000, 5, Decimal("0.10")),
        "weather": WeatherAssumptions(
            "covered_reliable_seating", "minor_concern"
        ),
        "revenue": RevenueAssumptions(
            "attendance", average_order_sale_amount=Decimal("15")
        ),
        "food_cost": FoodCostAssumptions(
            "sales_percentage", sales_percentage=Decimal("0.30")
        ),
        "fees": PaymentAndOrganizerFees(
            card_sales_percentage=Decimal("0.80"),
            card_processing_percentage=Decimal("0.03"),
            fixed_card_processing_fee=Decimal("5"),
            vendor_or_booking_fee=Decimal("100"),
            organizer_commission_percentage=Decimal("0.05"),
        ),
        "employee_labor": (
            EmployeeLaborEntry(Decimal("18"), Decimal("12")),
        ),
        "owner_labor_pay": Decimal("125"),
        "travel_cost": Decimal("75"),
        "additional_costs": (
            AdditionalEventCost("Parking", Decimal("20")),
        ),
        "profit_target": ProfitTarget(
            "profit_amount", minimum_profit_amount=Decimal("300")
        ),
    }
    values.update(changes)
    return EventScenario(**values)


def test_valid_event_and_scenario_can_be_created():
    identity = EventIdentity(
        "Summer Festival",
        date(2026, 8, 15),
        time(11, 0),
        "Town Square",
    )
    event = Event(identity, (valid_scenario(),))

    assert event.identity.event_name == "Summer Festival"
    assert event.scenarios[0].employee_labor[0].total_hours_paid == 12


def test_owner_only_scenario_can_have_no_employee_labor():
    scenario = valid_scenario(employee_labor=())

    assert scenario.employee_labor == ()


def test_event_requires_at_least_one_scenario():
    identity = EventIdentity(
        "Summer Festival",
        date(2026, 8, 15),
        time(11, 0),
        "Town Square",
    )

    with pytest.raises(ValueError):
        Event(identity)


@pytest.mark.parametrize(
    "revenue",
    [
        RevenueAssumptions(
            "attendance", average_order_sale_amount=Decimal("15")
        ),
        RevenueAssumptions(
            "manual_sales",
            average_order_sale_amount=Decimal("15"),
            expected_sales_amount=Decimal("5000"),
        ),
    ],
)
def test_approved_revenue_methods_are_valid(revenue):
    assert valid_scenario(revenue=revenue).revenue == revenue


@pytest.mark.parametrize(
    "food_cost",
    [
        FoodCostAssumptions(
            "average_per_order", average_cost_per_order=Decimal("5")
        ),
        FoodCostAssumptions(
            "sales_percentage", sales_percentage=Decimal("0.30")
        ),
        FoodCostAssumptions(
            "manual_event_total", manual_event_total=Decimal("750")
        ),
    ],
)
def test_approved_food_cost_methods_are_valid(food_cost):
    assert valid_scenario(food_cost=food_cost).food_cost == food_cost


def test_custom_weather_with_reduction_is_valid():
    weather = WeatherAssumptions(
        "fully_outdoors", "custom", Decimal("0.25")
    )

    assert valid_scenario(weather=weather).weather == weather


@pytest.mark.parametrize(
    "identity",
    [
        ("", date(2026, 8, 15), time(11), "Town Square"),
        ("Festival", date(2026, 8, 15), time(11), " "),
        ("Festival", None, time(11), "Town Square"),
        ("Festival", date(2026, 8, 15), None, "Town Square"),
    ],
)
def test_event_identity_rejects_missing_required_values(identity):
    with pytest.raises(ValueError):
        EventIdentity(*identity)


@pytest.mark.parametrize(
    "demand",
    [
        (-1, 2, Decimal("0.10")),
        (100, -1, Decimal("0.10")),
        (100, 2, Decimal("-0.01")),
        (100, 2, Decimal("1.01")),
    ],
)
def test_demand_rejects_invalid_counts_and_percentages(demand):
    with pytest.raises(ValueError):
        DemandAssumptions(*demand)


@pytest.mark.parametrize(
    "weather",
    [
        ("unknown", "favorable", None),
        ("fully_outdoors", "unknown", None),
        ("fully_outdoors", "custom", None),
        ("fully_outdoors", "custom", Decimal("1.01")),
        ("fully_outdoors", "minor_concern", Decimal("0.10")),
    ],
)
def test_weather_rejects_invalid_or_contradictory_states(weather):
    with pytest.raises(ValueError):
        WeatherAssumptions(*weather)


@pytest.mark.parametrize(
    "values",
    [
        {"method": "unknown"},
        {"method": "attendance"},
        {
            "method": "attendance",
            "average_order_sale_amount": Decimal("15"),
            "expected_sales_amount": Decimal("5000"),
        },
        {"method": "manual_sales"},
        {
            "method": "manual_sales",
            "average_order_sale_amount": Decimal("15"),
            "expected_sales_amount": Decimal("-1"),
        },
    ],
)
def test_revenue_rejects_invalid_or_contradictory_states(values):
    with pytest.raises(ValueError):
        RevenueAssumptions(**values)


@pytest.mark.parametrize(
    "values",
    [
        {"method": "unknown"},
        {"method": "average_per_order"},
        {
            "method": "average_per_order",
            "average_cost_per_order": Decimal("5"),
            "sales_percentage": Decimal("0.30"),
        },
        {
            "method": "sales_percentage",
            "sales_percentage": Decimal("1.01"),
        },
        {
            "method": "manual_event_total",
            "manual_event_total": Decimal("-1"),
        },
    ],
)
def test_food_cost_rejects_invalid_or_contradictory_states(values):
    with pytest.raises(ValueError):
        FoodCostAssumptions(**values)


@pytest.mark.parametrize(
    "fees",
    [
        (Decimal("-0.01"), Decimal("0.03"), Decimal("100")),
        (Decimal("0.80"), Decimal("1.01"), Decimal("100")),
        (Decimal("0.80"), Decimal("0.03"), Decimal("-1")),
    ],
)
def test_payment_fees_reject_invalid_values(fees):
    with pytest.raises(ValueError):
        PaymentAndOrganizerFees(*fees)


@pytest.mark.parametrize(
    "labor",
    [
        (Decimal("-1"), Decimal("1")),
        (Decimal("1"), Decimal("-1")),
    ],
)
def test_employee_labor_rejects_negative_values(labor):
    with pytest.raises(ValueError):
        EmployeeLaborEntry(*labor)


@pytest.mark.parametrize(
    "cost",
    [("", Decimal("10")), ("Parking", Decimal("-1"))],
)
def test_additional_cost_rejects_invalid_values(cost):
    with pytest.raises(ValueError):
        AdditionalEventCost(*cost)


@pytest.mark.parametrize(
    "values",
    [
        {"target_type": "unknown"},
        {"target_type": "profit_amount"},
        {
            "target_type": "profit_amount",
            "minimum_profit_amount": Decimal("300"),
            "minimum_profit_margin": Decimal("0.20"),
        },
        {"target_type": "profit_margin"},
        {
            "target_type": "profit_margin",
            "minimum_profit_amount": Decimal("300"),
            "minimum_profit_margin": Decimal("0.20"),
        },
        {
            "target_type": "profit_margin",
            "minimum_profit_margin": Decimal("1.01"),
        },
    ],
)
def test_profit_target_rejects_invalid_or_contradictory_states(values):
    with pytest.raises(ValueError):
        ProfitTarget(**values)


@pytest.mark.parametrize(
    "changes",
    [
        {"scenario_name": " "},
        {"owner_labor_pay": Decimal("-1")},
        {"travel_cost": Decimal("-1")},
    ],
)
def test_event_scenario_rejects_invalid_values(changes):
    with pytest.raises(ValueError):
        valid_scenario(**changes)


def test_event_models_are_immutable():
    scenario = valid_scenario()

    with pytest.raises(FrozenInstanceError):
        scenario.scenario_name = "Changed"
