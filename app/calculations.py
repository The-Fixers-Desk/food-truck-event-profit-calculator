from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING

from app.models import DemandAssumptions, EventScenario, WeatherAssumptions


ZERO = Decimal("0")
ONE = Decimal("1")

WEATHER_REDUCTIONS = {
    "favorable": Decimal("0"),
    "minor_concern": Decimal("0.05"),
    "moderate_adverse": Decimal("0.15"),
    "significant_adverse": Decimal("0.30"),
    "severe_disruption": Decimal("0.50"),
}

PROTECTION_FACTORS = {
    "fully_indoors": Decimal("0.15"),
    "covered_reliable_seating": Decimal("0.50"),
    "partially_covered": Decimal("0.75"),
    "fully_outdoors": Decimal("1"),
}


@dataclass(frozen=True)
class ProfitTargetEvaluation:
    target_type: str
    target_value: Decimal
    actual_value: Decimal | None
    is_met: bool | None


@dataclass(frozen=True)
class CalculationWarning:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class DemandCalculationResult:
    selected_weather_reduction: Decimal
    final_weather_reduction: Decimal
    weather_adjusted_attendance: Decimal
    total_expected_food_buyers: Decimal
    total_food_vendors: int
    equal_share_percentage: Decimal
    estimated_business_buyers: Decimal
    expected_orders: Decimal


@dataclass(frozen=True)
class EventCalculationResult:
    """Calculated scenario values before any display rounding."""

    selected_weather_reduction: Decimal
    final_weather_reduction: Decimal
    weather_adjusted_attendance: Decimal
    total_expected_food_buyers: Decimal
    total_food_vendors: int
    equal_share_percentage: Decimal
    estimated_business_buyers: Decimal
    expected_orders: Decimal
    expected_sales: Decimal

    food_and_packaging_cost: Decimal
    card_sales: Decimal
    percentage_card_processing_fee: Decimal
    estimated_card_transactions: Decimal
    fixed_card_processing_fees: Decimal
    organizer_commission: Decimal
    variable_costs: Decimal

    employee_labor_cost: Decimal
    owner_labor_pay: Decimal
    travel_cost: Decimal
    vendor_or_booking_fee: Decimal
    additional_event_costs: Decimal
    fixed_costs: Decimal

    total_event_cost: Decimal
    business_profit: Decimal
    profit_margin: Decimal | None

    break_even_sales: Decimal
    exact_break_even_customers: Decimal | None
    minimum_whole_break_even_customers: int | None
    profitability_status: str
    profit_target_evaluation: ProfitTargetEvaluation | None
    warnings: tuple[CalculationWarning, ...]


def calculate_event_scenario(
    scenario: EventScenario,
) -> EventCalculationResult:
    """Calculate financial outcomes for one complete event scenario."""
    demand = calculate_event_demand(
        scenario.demand,
        scenario.weather,
    )
    expected_orders = demand.expected_orders

    if scenario.revenue.method == "manual_sales":
        expected_sales = scenario.revenue.expected_sales_amount
    else:
        expected_sales = (
            expected_orders
            * scenario.revenue.average_order_sale_amount
        )

    food_and_packaging_cost = _food_cost(
        scenario, expected_orders, expected_sales
    )
    card_sales = expected_sales * scenario.fees.card_sales_percentage
    percentage_card_processing_fee = (
        card_sales * scenario.fees.card_processing_percentage
    )

    # This estimate assumes card and cash orders have approximately the same
    # average value.
    estimated_card_transactions = (
        expected_orders * scenario.fees.card_sales_percentage
    )
    fixed_card_processing_fees = (
        estimated_card_transactions
        * _or_zero(scenario.fees.fixed_card_processing_fee)
    )
    organizer_commission = (
        expected_sales
        * _or_zero(scenario.fees.organizer_commission_percentage)
    )
    variable_costs = sum(
        (
            food_and_packaging_cost,
            percentage_card_processing_fee,
            fixed_card_processing_fees,
            organizer_commission,
        ),
        ZERO,
    )

    employee_labor_cost = sum(
        (
            entry.hourly_rate * entry.total_hours_paid
            for entry in scenario.employee_labor
        ),
        ZERO,
    )
    owner_labor_pay = _or_zero(scenario.owner_labor_pay)
    travel_cost = _or_zero(scenario.travel_cost)
    vendor_or_booking_fee = scenario.fees.vendor_or_booking_fee
    additional_event_costs = sum(
        (cost.amount for cost in scenario.additional_costs),
        ZERO,
    )
    fixed_costs = sum(
        (
            employee_labor_cost,
            owner_labor_pay,
            travel_cost,
            vendor_or_booking_fee,
            additional_event_costs,
        ),
        ZERO,
    )

    total_event_cost = variable_costs + fixed_costs
    business_profit = expected_sales - total_event_cost
    profit_margin = (
        None
        if expected_sales == ZERO
        else business_profit / expected_sales
    )
    break_even_sales = total_event_cost
    average_order_sale_amount = (
        scenario.revenue.average_order_sale_amount
    )
    if (
        average_order_sale_amount is None
        or average_order_sale_amount == ZERO
    ):
        exact_break_even_customers = None
        minimum_whole_break_even_customers = None
    else:
        exact_break_even_customers = (
            break_even_sales / average_order_sale_amount
        )
        minimum_whole_break_even_customers = int(
            exact_break_even_customers.to_integral_value(
                rounding=ROUND_CEILING
            )
        )

    profitability_status = (
        "estimated_loss"
        if business_profit < ZERO
        else "break_even"
        if business_profit == ZERO
        else "profitable"
    )
    profit_target_evaluation = _evaluate_profit_target(
        scenario, business_profit, profit_margin
    )
    warnings = _build_warnings(
        scenario=scenario,
        business_profit=business_profit,
        profit_margin=profit_margin,
        expected_orders=expected_orders,
        exact_break_even_customers=exact_break_even_customers,
        minimum_whole_break_even_customers=(
            minimum_whole_break_even_customers
        ),
        total_expected_food_buyers=demand.total_expected_food_buyers,
        profit_target_evaluation=profit_target_evaluation,
    )

    return EventCalculationResult(
        selected_weather_reduction=demand.selected_weather_reduction,
        final_weather_reduction=demand.final_weather_reduction,
        weather_adjusted_attendance=demand.weather_adjusted_attendance,
        total_expected_food_buyers=demand.total_expected_food_buyers,
        total_food_vendors=demand.total_food_vendors,
        equal_share_percentage=demand.equal_share_percentage,
        estimated_business_buyers=demand.estimated_business_buyers,
        expected_orders=expected_orders,
        expected_sales=expected_sales,
        food_and_packaging_cost=food_and_packaging_cost,
        card_sales=card_sales,
        percentage_card_processing_fee=percentage_card_processing_fee,
        estimated_card_transactions=estimated_card_transactions,
        fixed_card_processing_fees=fixed_card_processing_fees,
        organizer_commission=organizer_commission,
        variable_costs=variable_costs,
        employee_labor_cost=employee_labor_cost,
        owner_labor_pay=owner_labor_pay,
        travel_cost=travel_cost,
        vendor_or_booking_fee=vendor_or_booking_fee,
        additional_event_costs=additional_event_costs,
        fixed_costs=fixed_costs,
        total_event_cost=total_event_cost,
        business_profit=business_profit,
        profit_margin=profit_margin,
        break_even_sales=break_even_sales,
        exact_break_even_customers=exact_break_even_customers,
        minimum_whole_break_even_customers=(
            minimum_whole_break_even_customers
        ),
        profitability_status=profitability_status,
        profit_target_evaluation=profit_target_evaluation,
        warnings=warnings,
    )


def calculate_event_demand(
    demand: DemandAssumptions,
    weather: WeatherAssumptions,
) -> DemandCalculationResult:
    """Calculate weather-adjusted shared food demand without rounding."""
    selected_weather_reduction = _selected_weather_reduction(weather)
    final_weather_reduction = (
        selected_weather_reduction
        * PROTECTION_FACTORS[weather.event_protection]
    )
    weather_adjusted_attendance = (
        Decimal(demand.estimated_attendance)
        * (ONE - final_weather_reduction)
    )
    total_expected_food_buyers = (
        weather_adjusted_attendance
        * demand.expected_food_buyer_percentage
    )
    total_food_vendors = demand.other_competing_food_vendors + 1
    equal_share_percentage = ONE / Decimal(total_food_vendors)
    estimated_business_buyers = (
        total_expected_food_buyers / Decimal(total_food_vendors)
    )
    return DemandCalculationResult(
        selected_weather_reduction=selected_weather_reduction,
        final_weather_reduction=final_weather_reduction,
        weather_adjusted_attendance=weather_adjusted_attendance,
        total_expected_food_buyers=total_expected_food_buyers,
        total_food_vendors=total_food_vendors,
        equal_share_percentage=equal_share_percentage,
        estimated_business_buyers=estimated_business_buyers,
        expected_orders=estimated_business_buyers,
    )


def _selected_weather_reduction(
    weather: WeatherAssumptions,
) -> Decimal:
    if weather.weather_outlook == "custom":
        return weather.custom_weather_reduction
    return WEATHER_REDUCTIONS[weather.weather_outlook]


def _food_cost(
    scenario: EventScenario,
    expected_orders: Decimal,
    expected_sales: Decimal,
) -> Decimal:
    if scenario.food_cost.method == "average_per_order":
        return (
            expected_orders
            * scenario.food_cost.average_cost_per_order
        )
    if scenario.food_cost.method == "sales_percentage":
        return expected_sales * scenario.food_cost.sales_percentage
    return scenario.food_cost.manual_event_total


def _or_zero(value: Decimal | None) -> Decimal:
    return ZERO if value is None else value


def _evaluate_profit_target(
    scenario: EventScenario,
    business_profit: Decimal,
    profit_margin: Decimal | None,
) -> ProfitTargetEvaluation | None:
    target = scenario.profit_target
    if target is None:
        return None
    if target.target_type == "profit_amount":
        return ProfitTargetEvaluation(
            target_type=target.target_type,
            target_value=target.minimum_profit_amount,
            actual_value=business_profit,
            is_met=business_profit >= target.minimum_profit_amount,
        )
    if profit_margin is None:
        return ProfitTargetEvaluation(
            target_type=target.target_type,
            target_value=target.minimum_profit_margin,
            actual_value=None,
            is_met=None,
        )
    return ProfitTargetEvaluation(
        target_type=target.target_type,
        target_value=target.minimum_profit_margin,
        actual_value=profit_margin,
        is_met=profit_margin >= target.minimum_profit_margin,
    )


def _build_warnings(
    *,
    scenario: EventScenario,
    business_profit: Decimal,
    profit_margin: Decimal | None,
    expected_orders: Decimal,
    exact_break_even_customers: Decimal | None,
    minimum_whole_break_even_customers: int | None,
    total_expected_food_buyers: Decimal,
    profit_target_evaluation: ProfitTargetEvaluation | None,
) -> tuple[CalculationWarning, ...]:
    warnings = []
    if business_profit < ZERO:
        warnings.append(
            CalculationWarning(
                "estimated_loss",
                "critical",
                "This scenario has an estimated business loss.",
            )
        )
    elif business_profit == ZERO:
        warnings.append(
            CalculationWarning(
                "exactly_at_break_even",
                "info",
                "This scenario is exactly at break-even.",
            )
        )
    if (
        profit_target_evaluation is not None
        and profit_target_evaluation.is_met is False
    ):
        warnings.append(
            CalculationWarning(
                "below_profit_target",
                "warning",
                "This scenario is below the selected profit target.",
            )
        )
    if (
        exact_break_even_customers is not None
        and expected_orders < exact_break_even_customers
    ):
        difference = exact_break_even_customers - expected_orders
        warnings.append(
            CalculationWarning(
                "even_split_buyers_below_break_even",
                "warning",
                (
                    f"The even-split estimate is {expected_orders} buyers, "
                    f"below the break-even requirement of "
                    f"{exact_break_even_customers} by {difference}."
                ),
            )
        )
    if (
        minimum_whole_break_even_customers is not None
        and Decimal(minimum_whole_break_even_customers)
        > total_expected_food_buyers
    ):
        warnings.append(
            CalculationWarning(
                "break_even_exceeds_all_expected_food_demand",
                "critical",
                (
                    f"Break-even requires "
                    f"{minimum_whole_break_even_customers} customers, more "
                    f"than all {total_expected_food_buyers} expected food "
                    f"buyers."
                ),
            )
        )
    if profit_margin is None:
        warnings.append(
            CalculationWarning(
                "profit_margin_unavailable",
                "info",
                "Profit margin is unavailable because expected sales are zero.",
            )
        )
    if scenario.revenue.method == "manual_sales":
        warnings.append(
            CalculationWarning(
                "custom_sales_assumption",
                "info",
                (
                    "Custom expected sales are active; order-based costs and "
                    "card transactions still use the shared-demand "
                    "expected order estimate."
                ),
            )
        )
    return tuple(warnings)
