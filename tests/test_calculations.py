from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

from app.calculations import calculate_event_scenario
from app.models import (
    AdditionalEventCost,
    DemandAssumptions,
    EmployeeLaborEntry,
    EventScenario,
    FoodCostAssumptions,
    PaymentAndOrganizerFees,
    ProfitTarget,
    RevenueAssumptions,
    WeatherAssumptions,
)


def scenario() -> EventScenario:
    return EventScenario(
        scenario_name="Original estimate",
        demand=DemandAssumptions(1000, 5, Decimal("0.10")),
        weather=WeatherAssumptions("fully_outdoors", "favorable"),
        revenue=RevenueAssumptions(
            "attendance", average_order_sale_amount=Decimal("10")
        ),
        food_cost=FoodCostAssumptions(
            "sales_percentage", sales_percentage=Decimal("0.30")
        ),
        fees=PaymentAndOrganizerFees(
            card_sales_percentage=Decimal("0.80"),
            card_processing_percentage=Decimal("0.03"),
            fixed_card_processing_fee=Decimal("0.25"),
            vendor_or_booking_fee=Decimal("100"),
            organizer_commission_percentage=Decimal("0.05"),
        ),
        employee_labor=(
            EmployeeLaborEntry(Decimal("20"), Decimal("10")),
        ),
        owner_labor_pay=Decimal("100"),
        travel_cost=Decimal("50"),
        additional_costs=(
            AdditionalEventCost("Parking", Decimal("20")),
            AdditionalEventCost("Permit", Decimal("10")),
            AdditionalEventCost(
                "Generator or utility cost", Decimal("20")
            ),
        ),
        profit_target=ProfitTarget(
            "profit_amount", minimum_profit_amount=Decimal("300")
        ),
    )


@pytest.mark.parametrize(
    ("outlook", "selected_reduction"),
    (
        ("favorable", Decimal("0")),
        ("minor_concern", Decimal("0.05")),
        ("moderate_adverse", Decimal("0.15")),
        ("significant_adverse", Decimal("0.30")),
        ("severe_disruption", Decimal("0.50")),
        ("custom", Decimal("0.22")),
    ),
)
@pytest.mark.parametrize(
    ("protection", "factor"),
    (
        ("fully_indoors", Decimal("0.15")),
        ("covered_reliable_seating", Decimal("0.50")),
        ("partially_covered", Decimal("0.75")),
        ("fully_outdoors", Decimal("1")),
    ),
)
def test_every_weather_and_protection_combination(
    outlook, selected_reduction, protection, factor
):
    weather = WeatherAssumptions(
        protection,
        outlook,
        selected_reduction if outlook == "custom" else None,
    )

    result = calculate_event_scenario(replace(scenario(), weather=weather))

    assert result.selected_weather_reduction == selected_reduction
    assert result.final_weather_reduction == selected_reduction * factor
    assert result.weather_adjusted_expected_customers == (
        Decimal("100") * (Decimal("1") - selected_reduction * factor)
    )


def test_attendance_based_revenue_flow():
    result = calculate_event_scenario(scenario())

    assert result.expected_customers_before_weather == Decimal("100")
    assert result.weather_adjusted_expected_customers == Decimal("100")
    assert result.expected_orders == Decimal("100")
    assert result.expected_sales == Decimal("1000")


def test_custom_sales_overrides_sales_but_not_expected_orders():
    custom_revenue = RevenueAssumptions(
        "manual_sales", expected_sales_amount=Decimal("2500")
    )

    result = calculate_event_scenario(
        replace(scenario(), revenue=custom_revenue)
    )

    assert result.expected_orders == Decimal("100")
    assert result.expected_sales == Decimal("2500")
    assert result.estimated_card_transactions == Decimal("80")


@pytest.mark.parametrize(
    ("food_cost", "expected"),
    (
        (
            FoodCostAssumptions(
                "average_per_order",
                average_cost_per_order=Decimal("4"),
            ),
            Decimal("400"),
        ),
        (
            FoodCostAssumptions(
                "sales_percentage",
                sales_percentage=Decimal("0.30"),
            ),
            Decimal("300"),
        ),
        (
            FoodCostAssumptions(
                "manual_event_total",
                manual_event_total=Decimal("475"),
            ),
            Decimal("475"),
        ),
    ),
)
def test_all_food_cost_methods(food_cost, expected):
    result = calculate_event_scenario(
        replace(scenario(), food_cost=food_cost)
    )

    assert result.food_and_packaging_cost == expected


def test_card_processing_and_organizer_costs():
    result = calculate_event_scenario(scenario())

    assert result.card_sales == Decimal("800")
    assert result.percentage_card_processing_fee == Decimal("24")
    assert result.estimated_card_transactions == Decimal("80")
    assert result.fixed_card_processing_fees == Decimal("20")
    assert result.organizer_commission == Decimal("50")


def test_multiple_employee_labor_entries_are_summed():
    labor = (
        EmployeeLaborEntry(Decimal("18"), Decimal("12")),
        EmployeeLaborEntry(Decimal("25"), Decimal("4")),
    )

    result = calculate_event_scenario(
        replace(scenario(), employee_labor=labor)
    )

    assert result.employee_labor_cost == Decimal("316")


def test_owner_only_event_has_zero_employee_labor():
    result = calculate_event_scenario(
        replace(
            scenario(),
            employee_labor=(),
            owner_labor_pay=Decimal("125"),
        )
    )

    assert result.employee_labor_cost == Decimal("0")
    assert result.owner_labor_pay == Decimal("125")


def test_every_fixed_event_cost_is_included():
    result = calculate_event_scenario(scenario())

    assert result.employee_labor_cost == Decimal("200")
    assert result.owner_labor_pay == Decimal("100")
    assert result.travel_cost == Decimal("50")
    assert result.vendor_or_booking_fee == Decimal("100")
    assert result.additional_event_costs == Decimal("50")
    assert result.fixed_costs == Decimal("500")


def test_optional_costs_are_zero_when_omitted():
    fees = PaymentAndOrganizerFees(
        card_sales_percentage=Decimal("0"),
        card_processing_percentage=Decimal("0"),
        fixed_card_processing_fee=None,
        vendor_or_booking_fee=Decimal("0"),
        organizer_commission_percentage=None,
    )
    minimal = replace(
        scenario(),
        fees=fees,
        employee_labor=(),
        owner_labor_pay=None,
        travel_cost=None,
        additional_costs=(),
    )

    result = calculate_event_scenario(minimal)

    assert result.fixed_card_processing_fees == Decimal("0")
    assert result.organizer_commission == Decimal("0")
    assert result.fixed_costs == Decimal("0")


def test_positive_profit_total_costs_and_margin():
    result = calculate_event_scenario(scenario())

    assert result.variable_costs == Decimal("394")
    assert result.fixed_costs == Decimal("500")
    assert result.total_event_cost == Decimal("894")
    assert result.business_profit == Decimal("106")
    assert result.profit_margin == Decimal("0.106")


def test_negative_profit_and_margin():
    costly = replace(
        scenario(),
        food_cost=FoodCostAssumptions(
            "manual_event_total",
            manual_event_total=Decimal("1000"),
        ),
        additional_costs=(
            AdditionalEventCost("Large permit", Decimal("1000")),
        ),
    )

    result = calculate_event_scenario(costly)

    assert result.business_profit < 0
    assert result.profit_margin < 0
    assert result.profit_margin == (
        result.business_profit / result.expected_sales
    )


def test_zero_expected_sales_has_no_calculable_margin():
    no_sales = replace(
        scenario(),
        demand=DemandAssumptions(0, 0, Decimal("0")),
        revenue=RevenueAssumptions(
            "attendance", average_order_sale_amount=Decimal("10")
        ),
    )

    result = calculate_event_scenario(no_sales)

    assert result.expected_sales == Decimal("0")
    assert result.business_profit < 0
    assert result.profit_margin is None


def test_decimal_calculations_are_not_intermediately_rounded():
    precise = replace(
        scenario(),
        demand=DemandAssumptions(3, 0, Decimal("0.3333")),
        weather=WeatherAssumptions("fully_indoors", "minor_concern"),
        revenue=RevenueAssumptions(
            "attendance", average_order_sale_amount=Decimal("12.345")
        ),
    )

    result = calculate_event_scenario(precise)

    assert result.expected_customers_before_weather == Decimal("0.9999")
    assert result.final_weather_reduction == Decimal("0.0075")
    assert (
        result.weather_adjusted_expected_customers
        == Decimal("0.99240075")
    )
    assert result.expected_sales == (
        Decimal("0.99240075") * Decimal("12.345")
    )


def test_calculation_results_are_immutable():
    result = calculate_event_scenario(scenario())

    with pytest.raises(FrozenInstanceError):
        result.expected_sales = Decimal("1")


def test_manual_example_one_attendance_based():
    """100 orders at $10 with percentage food cost and full fixed costs."""
    result = calculate_event_scenario(scenario())

    assert result.expected_sales == Decimal("1000")
    assert result.variable_costs == Decimal("394")
    assert result.fixed_costs == Decimal("500")
    assert result.total_event_cost == Decimal("894")
    assert result.business_profit == Decimal("106")
    assert result.profit_margin == Decimal("0.106")


def test_manual_example_two_custom_sales_owner_only():
    example = replace(
        scenario(),
        revenue=RevenueAssumptions(
            "manual_sales", expected_sales_amount=Decimal("2000")
        ),
        food_cost=FoodCostAssumptions(
            "average_per_order",
            average_cost_per_order=Decimal("4"),
        ),
        fees=PaymentAndOrganizerFees(
            card_sales_percentage=Decimal("0.50"),
            card_processing_percentage=Decimal("0.02"),
            fixed_card_processing_fee=Decimal("0.10"),
            vendor_or_booking_fee=Decimal("75"),
            organizer_commission_percentage=Decimal("0"),
        ),
        employee_labor=(),
        owner_labor_pay=Decimal("100"),
        travel_cost=Decimal("0"),
        additional_costs=(
            AdditionalEventCost("Parking", Decimal("25")),
        ),
    )

    result = calculate_event_scenario(example)

    assert result.expected_orders == Decimal("100")
    assert result.expected_sales == Decimal("2000")
    assert result.food_and_packaging_cost == Decimal("400")
    assert result.variable_costs == Decimal("425")
    assert result.fixed_costs == Decimal("200")
    assert result.total_event_cost == Decimal("625")
    assert result.business_profit == Decimal("1375")
    assert result.profit_margin == Decimal("0.6875")


def test_manual_example_three_negative_profit():
    example = replace(
        scenario(),
        revenue=RevenueAssumptions(
            "manual_sales", expected_sales_amount=Decimal("500")
        ),
        food_cost=FoodCostAssumptions(
            "manual_event_total",
            manual_event_total=Decimal("400"),
        ),
        fees=PaymentAndOrganizerFees(
            card_sales_percentage=Decimal("1"),
            card_processing_percentage=Decimal("0.04"),
            fixed_card_processing_fee=Decimal("0.50"),
            vendor_or_booking_fee=Decimal("100"),
            organizer_commission_percentage=Decimal("0.10"),
        ),
        employee_labor=(
            EmployeeLaborEntry(Decimal("30"), Decimal("10")),
        ),
        owner_labor_pay=Decimal("100"),
        travel_cost=Decimal("100"),
        additional_costs=(
            AdditionalEventCost("Event operating costs", Decimal("100")),
        ),
    )

    result = calculate_event_scenario(example)

    assert result.variable_costs == Decimal("520")
    assert result.fixed_costs == Decimal("700")
    assert result.total_event_cost == Decimal("1220")
    assert result.business_profit == Decimal("-720")
    assert result.profit_margin == Decimal("-1.44")
