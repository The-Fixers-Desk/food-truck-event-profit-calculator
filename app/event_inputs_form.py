from datetime import date, time
from decimal import Decimal, InvalidOperation

from werkzeug.datastructures import MultiDict

from app.calculations import (
    EventCalculationResult,
    calculate_event_demand,
    calculate_event_scenario,
)
from app.models import (
    AdditionalEventCost,
    BusinessDefaults,
    DemandAssumptions,
    EmployeeLaborEntry,
    EventIdentity,
    EventScenario,
    FoodCostAssumptions,
    PaymentAndOrganizerFees,
    ProfitTarget,
    RevenueAssumptions,
    WeatherAssumptions,
)


IDENTITY_FIELDS = ("event_name", "event_date", "start_time", "location")
REVENUE_FIELDS = (
    "estimated_attendance",
    "other_competing_food_vendors",
    "expected_food_buyer_percentage",
    "average_order_sale_amount",
    "weather_outlook",
    "custom_weather_reduction",
    "event_protection",
    "revenue_method",
    "expected_sales_amount",
)
FOOD_COST_FIELDS = (
    "food_cost_method_choice",
    "food_cost_method",
    "average_food_cost_per_order",
    "food_cost_percentage",
    "manual_food_cost_total",
)
LABOR_FIELDS = ("owner_labor_pay",)
OPERATING_COST_FIELDS = (
    "travel_cost",
    "parking_cost",
    "permit_cost",
    "generator_utility_cost",
)
EVENT_FEE_FIELDS = (
    "card_sales_percentage",
    "card_processing_percentage",
    "vendor_booking_fee",
    "organizer_commission_percentage",
    "fixed_card_processing_fee",
)
PROFIT_TARGET_FIELDS = (
    "profit_target_type",
    "minimum_profit_amount",
    "minimum_profit_margin",
)
DEFAULTED_SCALAR_FIELDS = (
    "average_order_sale_amount",
    "food_cost_method",
    "average_food_cost_per_order",
    "food_cost_percentage",
    "manual_food_cost_total",
    "card_sales_percentage",
    "card_processing_percentage",
    "owner_labor_pay",
    "travel_cost",
    "profit_target_type",
    "minimum_profit_amount",
    "minimum_profit_margin",
)
WEATHER_REDUCTIONS = {
    "favorable": Decimal("0"),
    "minor_concern": Decimal("5"),
    "moderate_adverse": Decimal("15"),
    "significant_adverse": Decimal("30"),
    "severe_disruption": Decimal("50"),
}
PROTECTION_FACTORS = {
    "fully_indoors": Decimal("0.15"),
    "covered_reliable_seating": Decimal("0.50"),
    "partially_covered": Decimal("0.75"),
    "fully_outdoors": Decimal("1"),
}


def blank_event_inputs_form(
    defaults: BusinessDefaults | None = None,
) -> dict:
    values = {
        name: ""
        for name in (
            *IDENTITY_FIELDS,
            *REVENUE_FIELDS,
            *FOOD_COST_FIELDS,
            *LABOR_FIELDS,
            *OPERATING_COST_FIELDS,
            *EVENT_FEE_FIELDS,
            *PROFIT_TARGET_FIELDS,
        )
    }
    values["revenue_method"] = "attendance"
    values["food_cost_method_choice"] = "average_per_order"
    values["employee_labor"] = []
    values["additional_costs"] = []
    for name in DEFAULTED_SCALAR_FIELDS:
        values[f"baseline_{name}"] = ""

    if defaults is not None:
        _apply_business_defaults(values, defaults)
    return values


def validate_event_inputs(
    submitted: MultiDict,
) -> tuple[EventIdentity | None, dict, dict[str, str]]:
    """Validate the currently implemented portions of Event Inputs."""
    values = {
        name: submitted.get(name, "").strip()
        for name in (
            *IDENTITY_FIELDS,
            *REVENUE_FIELDS,
            *FOOD_COST_FIELDS,
            *LABOR_FIELDS,
            *OPERATING_COST_FIELDS,
            *EVENT_FEE_FIELDS,
            *PROFIT_TARGET_FIELDS,
        )
    }
    for name in DEFAULTED_SCALAR_FIELDS:
        values[f"baseline_{name}"] = submitted.get(
            f"baseline_{name}", ""
        ).strip()
    rates = submitted.getlist("employee_labor_rate")
    hours = submitted.getlist("employee_labor_hours")
    baseline_rates = submitted.getlist("baseline_employee_labor_rate")
    baseline_hours = submitted.getlist("baseline_employee_labor_hours")
    values["employee_labor"] = [
        {
            "hourly_rate": (
                rates[index].strip() if index < len(rates) else ""
            ),
            "total_hours_paid": (
                hours[index].strip() if index < len(hours) else ""
            ),
            "baseline_hourly_rate": (
                baseline_rates[index].strip()
                if index < len(baseline_rates)
                else ""
            ),
            "baseline_total_hours_paid": (
                baseline_hours[index].strip()
                if index < len(baseline_hours)
                else ""
            ),
        }
        for index in range(max(len(rates), len(hours)))
    ]
    cost_names = submitted.getlist("additional_cost_name")
    cost_amounts = submitted.getlist("additional_cost_amount")
    values["additional_costs"] = [
        {
            "name": (
                cost_names[index].strip()
                if index < len(cost_names)
                else ""
            ),
            "amount": (
                cost_amounts[index].strip()
                if index < len(cost_amounts)
                else ""
            ),
        }
        for index in range(max(len(cost_names), len(cost_amounts)))
    ]
    errors: dict[str, str] = {}

    for name, label in (
        ("event_name", "Event name"),
        ("event_date", "Event date"),
        ("start_time", "Start time"),
        ("location", "Location"),
    ):
        if not values[name]:
            errors[name] = f"{label} is required."

    event_date = _parse_date(values["event_date"], errors)
    start_time = _parse_time(values["start_time"], errors)

    _whole_number(
        values, errors, "estimated_attendance", "Estimated attendance"
    )
    _whole_number(
        values,
        errors,
        "other_competing_food_vendors",
        "Other competing food vendors",
    )
    _percentage(
        values,
        errors,
        "expected_food_buyer_percentage",
        "Percentage expected to buy food",
    )
    _money(
        values,
        errors,
        "average_order_sale_amount",
        "Average order sale amount",
    )

    weather_reduction = _validate_weather(values, errors)
    if weather_reduction is not None:
        if values["event_protection"] not in PROTECTION_FACTORS:
            errors["event_protection"] = "Choose the event protection."
    else:
        values["event_protection"] = ""

    revenue_method = values["revenue_method"]
    if revenue_method == "manual_sales":
        _money(
            values,
            errors,
            "expected_sales_amount",
            "Expected sales amount",
        )
    elif revenue_method == "attendance":
        values["expected_sales_amount"] = ""
    else:
        values["revenue_method"] = "attendance"
        values["expected_sales_amount"] = ""

    _validate_food_cost(values, errors)
    _validate_labor(values, errors)
    _validate_operating_costs(values, errors)
    _validate_event_fees(values, errors)
    _validate_additional_costs(values, errors)
    _validate_profit_target(values, errors)

    if errors:
        return None, values, errors

    identity = EventIdentity(
        event_name=values["event_name"],
        event_date=event_date,
        start_time=start_time,
        location=values["location"],
    )
    return identity, values, errors


def validate_and_calculate_event_analysis(
    submitted: MultiDict,
) -> tuple[
    EventIdentity | None,
    dict,
    dict[str, str],
    EventCalculationResult | None,
]:
    """Validate a complete event form and calculate its current analysis."""
    identity, values, errors = validate_event_inputs(submitted)
    if errors:
        return identity, values, errors, None
    result = calculate_event_scenario(_scenario_from_form_values(values))
    return identity, values, errors, result


def calculation_result_data(result: EventCalculationResult) -> dict:
    """Return structured display data without changing calculation precision."""
    target = result.profit_target_evaluation
    return {
        "weather_adjusted_attendance": _format_decimal(
            result.weather_adjusted_attendance
        ),
        "total_expected_food_buyers": _format_decimal(
            result.total_expected_food_buyers
        ),
        "total_food_vendors": str(result.total_food_vendors),
        "estimated_business_buyers": _format_decimal(
            result.estimated_business_buyers
        ),
        "expected_orders": _format_decimal(result.expected_orders),
        "expected_sales": _format_decimal(result.expected_sales),
        "food_and_packaging_cost": _format_decimal(
            result.food_and_packaging_cost
        ),
        "percentage_card_processing_fee": _format_decimal(
            result.percentage_card_processing_fee
        ),
        "fixed_card_processing_fees": _format_decimal(
            result.fixed_card_processing_fees
        ),
        "organizer_commission": _format_decimal(
            result.organizer_commission
        ),
        "variable_costs": _format_decimal(result.variable_costs),
        "employee_labor_cost": _format_decimal(
            result.employee_labor_cost
        ),
        "owner_labor_pay": _format_decimal(result.owner_labor_pay),
        "travel_cost": _format_decimal(result.travel_cost),
        "vendor_or_booking_fee": _format_decimal(
            result.vendor_or_booking_fee
        ),
        "additional_event_costs": _format_decimal(
            result.additional_event_costs
        ),
        "fixed_costs": _format_decimal(result.fixed_costs),
        "total_event_cost": _format_decimal(result.total_event_cost),
        "business_profit": _format_decimal(result.business_profit),
        "profit_margin": (
            None
            if result.profit_margin is None
            else _format_decimal(result.profit_margin * Decimal("100"))
        ),
        "break_even_sales": _format_decimal(result.break_even_sales),
        "exact_break_even_customers": (
            None
            if result.exact_break_even_customers is None
            else _format_decimal(result.exact_break_even_customers)
        ),
        "minimum_whole_break_even_customers": (
            result.minimum_whole_break_even_customers
        ),
        "profitability_status": result.profitability_status,
        "profit_target": (
            None
            if target is None
            else {
                "target_type": target.target_type,
                "target_value": _format_decimal(
                    target.target_value
                    * (
                        Decimal("100")
                        if target.target_type == "profit_margin"
                        else Decimal("1")
                    )
                ),
                "actual_value": (
                    None
                    if target.actual_value is None
                    else _format_decimal(
                        target.actual_value
                        * (
                            Decimal("100")
                            if target.target_type == "profit_margin"
                            else Decimal("1")
                        )
                    )
                ),
                "is_met": target.is_met,
            }
        ),
        "warnings": [
            {
                "code": warning.code,
                "severity": warning.severity,
                "message": warning.message,
            }
            for warning in result.warnings
        ],
    }


def calculate_demand_preview(submitted: MultiDict) -> tuple[dict | None, dict]:
    """Validate current demand inputs and calculate a read-only preview."""
    values = {
        name: submitted.get(name, "").strip()
        for name in (
            "estimated_attendance",
            "other_competing_food_vendors",
            "expected_food_buyer_percentage",
            "weather_outlook",
            "custom_weather_reduction",
            "event_protection",
        )
    }
    errors: dict[str, str] = {}
    attendance = _whole_number(
        values, errors, "estimated_attendance", "Estimated attendance"
    )
    other_vendors = _whole_number(
        values,
        errors,
        "other_competing_food_vendors",
        "Other competing food vendors",
    )
    food_buyer_percentage = _percentage(
        values,
        errors,
        "expected_food_buyer_percentage",
        "Percentage expected to buy food",
    )
    weather_reduction = _validate_weather(values, errors)
    if (
        weather_reduction is not None
        and values["event_protection"] not in PROTECTION_FACTORS
    ):
        errors["event_protection"] = "Choose the event protection."
    if errors:
        return None, errors

    result = calculate_event_demand(
        DemandAssumptions(
            estimated_attendance=attendance,
            other_competing_food_vendors=other_vendors,
            expected_food_buyer_percentage=(
                food_buyer_percentage / Decimal("100")
            ),
        ),
        WeatherAssumptions(
            event_protection=values["event_protection"],
            weather_outlook=values["weather_outlook"],
            custom_weather_reduction=(
                weather_reduction / Decimal("100")
                if values["weather_outlook"] == "custom"
                else None
            ),
        ),
    )
    preview = {
        "weather_adjusted_attendance": _format_decimal(
            result.weather_adjusted_attendance
        ),
        "total_expected_food_buyers": _format_decimal(
            result.total_expected_food_buyers
        ),
        "total_food_vendors": result.total_food_vendors,
        "equal_share_percentage": _format_decimal(
            result.equal_share_percentage * Decimal("100")
        ),
        "estimated_business_buyers": _format_decimal(
            result.estimated_business_buyers
        ),
    }

    _, full_values, full_errors = validate_event_inputs(submitted)
    for name in (*IDENTITY_FIELDS,):
        full_errors.pop(name, None)
    if not full_errors:
        calculation = calculate_event_scenario(
            _scenario_from_form_values(full_values)
        )
        if calculation.exact_break_even_customers is not None:
            difference = (
                calculation.exact_break_even_customers
                - calculation.estimated_business_buyers
            )
            preview["exact_break_even_customers"] = _format_decimal(
                calculation.exact_break_even_customers
            )
            if difference > 0:
                preview["break_even_message"] = (
                    f"The even-split estimate is "
                    f"{_format_decimal(calculation.estimated_business_buyers)} "
                    f"buyers, {_format_decimal(difference)} below the "
                    f"{_format_decimal(calculation.exact_break_even_customers)} "
                    f"break-even requirement."
                )
            else:
                preview["break_even_message"] = (
                    f"The even-split estimate meets or exceeds the "
                    f"{_format_decimal(calculation.exact_break_even_customers)} "
                    f"break-even customer requirement."
                )
    return preview, {}


def _scenario_from_form_values(values: dict) -> EventScenario:
    revenue = (
        RevenueAssumptions(
            "manual_sales",
            expected_sales_amount=Decimal(values["expected_sales_amount"]),
        )
        if values["revenue_method"] == "manual_sales"
        else RevenueAssumptions(
            "attendance",
            average_order_sale_amount=Decimal(
                values["average_order_sale_amount"]
            ),
        )
    )
    food_values = {
        "average_per_order": (
            "average_cost_per_order",
            "average_food_cost_per_order",
        ),
        "sales_percentage": (
            "sales_percentage",
            "food_cost_percentage",
        ),
        "manual_event_total": (
            "manual_event_total",
            "manual_food_cost_total",
        ),
    }
    food_attribute, food_field = food_values[values["food_cost_method"]]
    food_value = Decimal(values[food_field])
    if food_attribute == "sales_percentage":
        food_value /= Decimal("100")
    food_cost = FoodCostAssumptions(
        values["food_cost_method"],
        **{food_attribute: food_value},
    )
    target = (
        ProfitTarget(
            "profit_amount",
            minimum_profit_amount=Decimal(
                values["minimum_profit_amount"]
            ),
        )
        if values["profit_target_type"] == "profit_amount"
        else ProfitTarget(
            "profit_margin",
            minimum_profit_margin=(
                Decimal(values["minimum_profit_margin"])
                / Decimal("100")
            ),
        )
    )
    additional_costs = [
        AdditionalEventCost(cost["name"], Decimal(cost["amount"]))
        for cost in values["additional_costs"]
    ]
    additional_costs.extend(
        AdditionalEventCost(label, Decimal(values[field]))
        for field, label in (
            ("parking_cost", "Parking"),
            ("permit_cost", "Permit"),
            ("generator_utility_cost", "Generator or utility cost"),
        )
        if values[field]
    )
    return EventScenario(
        scenario_name="Demand preview",
        demand=DemandAssumptions(
            int(values["estimated_attendance"]),
            int(values["other_competing_food_vendors"]),
            Decimal(values["expected_food_buyer_percentage"])
            / Decimal("100"),
        ),
        weather=WeatherAssumptions(
            values["event_protection"],
            values["weather_outlook"],
            (
                Decimal(values["custom_weather_reduction"])
                / Decimal("100")
                if values["weather_outlook"] == "custom"
                else None
            ),
        ),
        revenue=revenue,
        food_cost=food_cost,
        fees=PaymentAndOrganizerFees(
            Decimal(values["card_sales_percentage"]) / Decimal("100"),
            Decimal(values["card_processing_percentage"]) / Decimal("100"),
            _optional_decimal(values["vendor_booking_fee"]),
            _optional_decimal(values["fixed_card_processing_fee"]),
            (
                Decimal(values["organizer_commission_percentage"])
                / Decimal("100")
                if values["organizer_commission_percentage"]
                else None
            ),
        ),
        employee_labor=tuple(
            EmployeeLaborEntry(
                Decimal(entry["hourly_rate"]),
                Decimal(entry["total_hours_paid"]),
            )
            for entry in values["employee_labor"]
        ),
        owner_labor_pay=_optional_decimal(values["owner_labor_pay"]),
        travel_cost=_optional_decimal(values["travel_cost"]),
        additional_costs=tuple(additional_costs),
        profit_target=target,
    )


def _optional_decimal(value: str) -> Decimal:
    return Decimal(value) if value else Decimal("0")


def _apply_business_defaults(
    values: dict,
    defaults: BusinessDefaults,
) -> None:
    copied = {
        "average_order_sale_amount": _format_decimal(
            defaults.average_order_sale_amount
        ),
        "food_cost_method": defaults.food_cost_method,
        "average_food_cost_per_order": _format_optional_decimal(
            defaults.average_food_cost_per_order
        ),
        "food_cost_percentage": _format_optional_percentage(
            defaults.food_cost_percentage
        ),
        "manual_food_cost_total": _format_optional_decimal(
            defaults.typical_food_cost_total
        ),
        "card_sales_percentage": _format_percentage(
            defaults.card_sales_percentage
        ),
        "card_processing_percentage": _format_percentage(
            defaults.card_processing_percentage
        ),
        "owner_labor_pay": _format_optional_decimal(
            defaults.default_owner_labor_pay
        ),
        "travel_cost": _format_optional_decimal(
            defaults.default_travel_cost
        ),
        "profit_target_type": defaults.profit_target_type,
        "minimum_profit_amount": _format_optional_decimal(
            defaults.minimum_profit_amount
        ),
        "minimum_profit_margin": _format_optional_percentage(
            defaults.minimum_profit_margin
        ),
    }
    values.update(copied)
    values["food_cost_method_choice"] = defaults.food_cost_method
    values["employee_labor"] = [
        {
            "hourly_rate": _format_decimal(entry.hourly_rate),
            "total_hours_paid": _format_decimal(entry.total_hours_paid),
            "baseline_hourly_rate": _format_decimal(entry.hourly_rate),
            "baseline_total_hours_paid": _format_decimal(
                entry.total_hours_paid
            ),
        }
        for entry in defaults.labor_entries
    ]
    for name, value in copied.items():
        values[f"baseline_{name}"] = value


def _validate_profit_target(
    values: dict,
    errors: dict,
) -> None:
    target_type = values["profit_target_type"]
    if target_type == "profit_amount":
        values["minimum_profit_margin"] = ""
        _money(
            values,
            errors,
            "minimum_profit_amount",
            "Minimum profit amount",
        )
    elif target_type == "profit_margin":
        values["minimum_profit_amount"] = ""
        _percentage(
            values,
            errors,
            "minimum_profit_margin",
            "Minimum profit margin",
        )
    else:
        values["profit_target_type"] = ""
        values["minimum_profit_amount"] = ""
        values["minimum_profit_margin"] = ""
        errors["profit_target_type"] = "Choose how you evaluate an event."


def _validate_event_fees(
    values: dict,
    errors: dict,
) -> None:
    _percentage(
        values,
        errors,
        "card_sales_percentage",
        "Sales paid by card",
    )
    _percentage(
        values,
        errors,
        "card_processing_percentage",
        "Card-processing percentage",
    )
    for name, label in (
        ("vendor_booking_fee", "Vendor or booking fee"),
        (
            "fixed_card_processing_fee",
            "Fixed card-processing fee per card transaction",
        ),
    ):
        if values[name]:
            _money(values, errors, name, label)

    if values["organizer_commission_percentage"]:
        _percentage(
            values,
            errors,
            "organizer_commission_percentage",
            "Organizer commission or revenue share",
        )


def _validate_additional_costs(
    values: dict,
    errors: dict,
) -> None:
    cost_errors = []
    for cost in values["additional_costs"]:
        row_errors = {}
        if not cost["name"]:
            row_errors["name"] = "Cost name is required."
        _positive_money(
            cost,
            row_errors,
            "amount",
            "Miscellaneous cost amount",
        )
        cost_errors.append(row_errors)
    if any(cost_errors):
        errors["additional_costs"] = cost_errors


def _validate_operating_costs(
    values: dict,
    errors: dict,
) -> None:
    for name, label in (
        ("travel_cost", "Travel cost"),
        ("parking_cost", "Parking cost"),
        ("permit_cost", "Permit cost"),
        ("generator_utility_cost", "Generator or utility cost"),
    ):
        if values[name]:
            _money(values, errors, name, label)


def _validate_labor(
    values: dict,
    errors: dict,
) -> None:
    labor_errors = []
    for entry in values["employee_labor"]:
        entry_errors = {}
        _positive_money(
            entry,
            entry_errors,
            "hourly_rate",
            "Hourly labor rate",
        )
        _positive_decimal(
            entry,
            entry_errors,
            "total_hours_paid",
            "Combined total hours paid",
        )
        labor_errors.append(entry_errors)
    if any(labor_errors):
        errors["employee_labor"] = labor_errors

    if values["owner_labor_pay"]:
        _money(
            values,
            errors,
            "owner_labor_pay",
            "Owner labor pay for this event",
        )


def _positive_money(values, errors, name, label) -> Decimal | None:
    value = _money(values, errors, name, label)
    if value is not None and value <= 0:
        errors[name] = f"{label} must be greater than zero."
    return value


def _positive_decimal(values, errors, name, label) -> Decimal | None:
    value = _decimal(values, errors, name, label)
    if value is not None and value <= 0:
        errors[name] = f"{label} must be greater than zero."
    return value


def _validate_food_cost(
    values: dict[str, str],
    errors: dict[str, str],
) -> None:
    method = values["food_cost_method"]
    if method == "average_per_order":
        values["food_cost_percentage"] = ""
        values["manual_food_cost_total"] = ""
        _money(
            values,
            errors,
            "average_food_cost_per_order",
            "Average food and packaging cost per order",
        )
    elif method == "sales_percentage":
        values["average_food_cost_per_order"] = ""
        values["manual_food_cost_total"] = ""
        _percentage(
            values,
            errors,
            "food_cost_percentage",
            "Food and packaging cost percentage",
        )
    elif method == "manual_event_total":
        values["average_food_cost_per_order"] = ""
        values["food_cost_percentage"] = ""
        _money(
            values,
            errors,
            "manual_food_cost_total",
            "Total food and packaging cost for this event",
        )
    else:
        values["food_cost_method"] = ""
        values["average_food_cost_per_order"] = ""
        values["food_cost_percentage"] = ""
        values["manual_food_cost_total"] = ""
        errors["food_cost_method"] = (
            "Choose and confirm a food and packaging cost method."
        )


def protection_reductions(values: dict[str, str]) -> dict[str, str]:
    """Return display percentages for the current weather selection."""
    reduction = _selected_weather_reduction(values)
    if reduction is None:
        return {choice: "" for choice in PROTECTION_FACTORS}
    return {
        choice: _format_decimal(reduction * factor)
        for choice, factor in PROTECTION_FACTORS.items()
    }


def weather_allows_protection(values: dict[str, str]) -> bool:
    return _selected_weather_reduction(values) is not None


def _validate_weather(
    values: dict[str, str],
    errors: dict[str, str],
) -> Decimal | None:
    outlook = values["weather_outlook"]
    if outlook in WEATHER_REDUCTIONS:
        values["custom_weather_reduction"] = ""
        return WEATHER_REDUCTIONS[outlook]
    if outlook == "custom":
        return _percentage(
            values,
            errors,
            "custom_weather_reduction",
            "Custom weather reduction",
        )
    errors["weather_outlook"] = "Choose the weather outlook."
    values["custom_weather_reduction"] = ""
    return None


def _selected_weather_reduction(
    values: dict[str, str],
) -> Decimal | None:
    outlook = values["weather_outlook"]
    if outlook in WEATHER_REDUCTIONS:
        return WEATHER_REDUCTIONS[outlook]
    if outlook != "custom":
        return None
    try:
        reduction = Decimal(values["custom_weather_reduction"])
    except InvalidOperation:
        return None
    if not reduction.is_finite() or reduction < 0 or reduction > 100:
        return None
    return reduction


def _whole_number(values, errors, name, label) -> int | None:
    raw_value = values[name]
    if not raw_value:
        errors[name] = f"{label} is required."
        return None
    try:
        value = int(raw_value)
    except ValueError:
        errors[name] = f"{label} must be a whole number."
        return None
    if value < 0:
        errors[name] = f"{label} cannot be negative."
    return value


def _money(values, errors, name, label) -> Decimal | None:
    value = _decimal(values, errors, name, label)
    if value is not None:
        if value < 0:
            errors[name] = f"{label} cannot be negative."
        elif value.as_tuple().exponent < -2:
            errors[name] = f"{label} can have at most 2 decimal places."
    return value


def _percentage(values, errors, name, label) -> Decimal | None:
    value = _decimal(values, errors, name, label)
    if value is not None:
        if value < 0 or value > 100:
            errors[name] = f"{label} must be between 0 and 100."
        elif value.as_tuple().exponent < -2:
            errors[name] = f"{label} can have at most 2 decimal places."
    return value


def _decimal(values, errors, name, label) -> Decimal | None:
    raw_value = values[name]
    if not raw_value:
        errors[name] = f"{label} is required."
        return None
    try:
        value = Decimal(raw_value)
    except InvalidOperation:
        errors[name] = f"{label} must be a number."
        return None
    if not value.is_finite():
        errors[name] = f"{label} must be a number."
        return None
    return value


def _parse_date(value: str, errors: dict[str, str]) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors["event_date"] = "Enter a valid event date."
        return None


def _parse_time(value: str, errors: dict[str, str]) -> time | None:
    if not value:
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        errors["start_time"] = "Enter a valid start time."
        return None


def _format_decimal(value: Decimal) -> str:
    formatted = format(value, "f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted or "0"


def _format_percentage(value: Decimal) -> str:
    return _format_decimal(value * Decimal("100"))


def _format_optional_decimal(value: Decimal | None) -> str:
    return "" if value is None else _format_decimal(value)


def _format_optional_percentage(value: Decimal | None) -> str:
    return "" if value is None else _format_percentage(value)
