from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

from app.calculations import (
    CalculationWarning,
    calculate_event_scenario,
)
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
    assert result.break_even_sales == Decimal("894")
    assert result.exact_break_even_customers == Decimal("89.4")
    assert result.minimum_whole_break_even_customers == 90


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
    assert result.break_even_sales == Decimal("625")
    assert result.exact_break_even_customers is None
    assert result.minimum_whole_break_even_customers is None


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


def test_break_even_sales_equals_current_total_event_cost():
    result = calculate_event_scenario(scenario())

    assert result.break_even_sales == result.total_event_cost


def test_owner_labor_pay_is_included_in_break_even_sales():
    with_owner_pay = calculate_event_scenario(scenario())
    without_owner_pay = calculate_event_scenario(
        replace(scenario(), owner_labor_pay=None)
    )

    assert (
        with_owner_pay.break_even_sales
        - without_owner_pay.break_even_sales
        == Decimal("100")
    )


def test_break_even_customers_are_exact_and_rounded_up():
    result = calculate_event_scenario(scenario())

    assert result.exact_break_even_customers == Decimal("89.4")
    assert result.minimum_whole_break_even_customers == 90


def test_exact_whole_break_even_customers_are_not_rounded_further():
    example = replace(
        scenario(),
        fees=replace(
            scenario().fees,
            vendor_or_booking_fee=Decimal("106"),
        ),
    )

    result = calculate_event_scenario(example)

    assert result.break_even_sales == Decimal("900")
    assert result.exact_break_even_customers == Decimal("90")
    assert result.minimum_whole_break_even_customers == 90


def test_zero_total_cost_has_zero_break_even():
    example = replace(
        scenario(),
        demand=DemandAssumptions(0, 0, Decimal("0")),
        food_cost=FoodCostAssumptions(
            "sales_percentage", sales_percentage=Decimal("0")
        ),
        fees=PaymentAndOrganizerFees(
            card_sales_percentage=Decimal("0"),
            card_processing_percentage=Decimal("0"),
            fixed_card_processing_fee=None,
            vendor_or_booking_fee=Decimal("0"),
            organizer_commission_percentage=None,
        ),
        employee_labor=(),
        owner_labor_pay=None,
        travel_cost=None,
        additional_costs=(),
    )

    result = calculate_event_scenario(example)

    assert result.total_event_cost == Decimal("0")
    assert result.break_even_sales == Decimal("0")
    assert result.exact_break_even_customers == Decimal("0")
    assert result.minimum_whole_break_even_customers == 0


def test_zero_average_order_amount_has_no_break_even_customer_count():
    example = replace(
        scenario(),
        revenue=RevenueAssumptions(
            "attendance", average_order_sale_amount=Decimal("0")
        ),
    )

    result = calculate_event_scenario(example)

    assert result.break_even_sales > Decimal("0")
    assert result.exact_break_even_customers is None
    assert result.minimum_whole_break_even_customers is None


def test_positive_profit_status():
    result = calculate_event_scenario(scenario())

    assert result.profitability_status == "profitable"
    assert "estimated_loss" not in warning_codes(result)
    assert "exactly_at_break_even" not in warning_codes(result)


def test_estimated_loss_status_and_warning():
    example = replace(
        scenario(),
        fees=replace(
            scenario().fees,
            vendor_or_booking_fee=Decimal("207"),
        ),
    )

    result = calculate_event_scenario(example)

    assert result.business_profit == Decimal("-1")
    assert result.profitability_status == "estimated_loss"
    assert result.warnings[0] == CalculationWarning(
        code="estimated_loss",
        severity="critical",
        message="This scenario has an estimated business loss.",
    )


def test_exact_break_even_status_and_warning():
    example = replace(
        scenario(),
        fees=replace(
            scenario().fees,
            vendor_or_booking_fee=Decimal("206"),
        ),
    )

    result = calculate_event_scenario(example)

    assert result.business_profit == Decimal("0")
    assert result.profitability_status == "break_even"
    assert result.warnings[0] == CalculationWarning(
        code="exactly_at_break_even",
        severity="info",
        message="This scenario is exactly at break-even.",
    )


@pytest.mark.parametrize(
    ("target", "expected_met"),
    [
        (Decimal("100"), True),
        (Decimal("106"), True),
        (Decimal("107"), False),
    ],
)
def test_profit_amount_target_evaluation(target, expected_met):
    example = replace(
        scenario(),
        profit_target=ProfitTarget(
            "profit_amount", minimum_profit_amount=target
        ),
    )

    result = calculate_event_scenario(example)

    assert result.profit_target_evaluation.target_value == target
    assert result.profit_target_evaluation.actual_value == Decimal("106")
    assert result.profit_target_evaluation.is_met is expected_met
    assert (
        "below_profit_target" in warning_codes(result)
    ) is (not expected_met)


@pytest.mark.parametrize(
    ("target", "expected_met"),
    [
        (Decimal("0.10"), True),
        (Decimal("0.106"), True),
        (Decimal("0.11"), False),
    ],
)
def test_profit_margin_target_evaluation(target, expected_met):
    example = replace(
        scenario(),
        profit_target=ProfitTarget(
            "profit_margin", minimum_profit_margin=target
        ),
    )

    result = calculate_event_scenario(example)

    assert result.profit_target_evaluation.target_value == target
    assert result.profit_target_evaluation.actual_value == Decimal("0.106")
    assert result.profit_target_evaluation.is_met is expected_met
    assert (
        "below_profit_target" in warning_codes(result)
    ) is (not expected_met)


def test_margin_target_is_unavailable_when_sales_are_zero():
    example = replace(
        scenario(),
        demand=DemandAssumptions(0, 0, Decimal("0")),
        revenue=RevenueAssumptions(
            "attendance", average_order_sale_amount=Decimal("10")
        ),
        profit_target=ProfitTarget(
            "profit_margin", minimum_profit_margin=Decimal("0.10")
        ),
    )

    result = calculate_event_scenario(example)

    assert result.profit_target_evaluation.actual_value is None
    assert result.profit_target_evaluation.is_met is None
    assert "below_profit_target" not in warning_codes(result)
    assert "profit_margin_unavailable" in warning_codes(result)


def test_no_profit_target_has_no_evaluation_or_target_warning():
    example = replace(scenario(), profit_target=None)

    result = calculate_event_scenario(example)

    assert result.profit_target_evaluation is None
    assert "below_profit_target" not in warning_codes(result)


def test_expected_orders_below_break_even_customers_warning():
    example = replace(
        scenario(),
        fees=replace(
            scenario().fees,
            vendor_or_booking_fee=Decimal("300"),
        ),
    )

    result = calculate_event_scenario(example)

    assert result.expected_orders == Decimal("100")
    assert result.exact_break_even_customers == Decimal("109.4")
    assert "expected_customers_below_break_even" in warning_codes(result)


def test_break_even_customers_exceed_weather_adjusted_attendance_warning():
    example = replace(
        scenario(),
        additional_costs=(
            AdditionalEventCost("Large fixed cost", Decimal("10000")),
        ),
    )

    result = calculate_event_scenario(example)

    assert result.minimum_whole_break_even_customers == 1085
    assert result.weather_adjusted_attendance == Decimal("1000")
    assert (
        "break_even_exceeds_available_attendance"
        in warning_codes(result)
    )


def test_custom_expected_sales_warning_documents_order_assumption():
    example = replace(
        scenario(),
        revenue=RevenueAssumptions(
            "manual_sales", expected_sales_amount=Decimal("2000")
        ),
    )

    result = calculate_event_scenario(example)

    warning = next(
        warning
        for warning in result.warnings
        if warning.code == "custom_sales_assumption"
    )
    assert warning.severity == "info"
    assert "attendance-based expected order estimate" in warning.message


def test_warning_codes_messages_severity_and_order_are_stable():
    example = replace(
        scenario(),
        additional_costs=(
            AdditionalEventCost("Large fixed cost", Decimal("10000")),
        ),
    )

    result = calculate_event_scenario(example)

    assert result.warnings == (
        CalculationWarning(
            "estimated_loss",
            "critical",
            "This scenario has an estimated business loss.",
        ),
        CalculationWarning(
            "below_profit_target",
            "warning",
            "This scenario is below the selected profit target.",
        ),
        CalculationWarning(
            "expected_customers_below_break_even",
            "warning",
            "Expected customers are below the break-even customer count.",
        ),
        CalculationWarning(
            "break_even_exceeds_available_attendance",
            "critical",
            "Break-even customers exceed weather-adjusted attendance.",
        ),
    )


def test_break_even_keeps_exact_decimal_precision():
    example = replace(
        scenario(),
        revenue=RevenueAssumptions(
            "attendance",
            average_order_sale_amount=Decimal("12.345"),
        ),
    )

    result = calculate_event_scenario(example)

    assert (
        result.exact_break_even_customers
        == result.total_event_cost / Decimal("12.345")
    )


def warning_codes(result):
    return tuple(warning.code for warning in result.warnings)
