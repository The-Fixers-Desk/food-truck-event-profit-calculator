from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP

from app.calculations import CalculationWarning, calculate_event_scenario
from app.database import load_event_scenario
from app.event_inputs_form import customer_warning_data


RESULT_ROWS = (
    ("estimated_business_buyers", "Expected buyers", "buyer_count"),
    ("expected_orders", "Expected orders", "count"),
    ("expected_sales", "Expected sales", "money"),
    ("variable_costs", "Variable costs", "money"),
    ("fixed_costs", "Fixed costs", "money"),
    ("employee_labor_cost", "Employee labor", "money"),
    ("owner_labor_pay", "Owner labor pay", "money"),
    ("total_event_cost", "Total event cost", "money"),
    ("business_profit", "Business profit", "money"),
    ("profit_margin", "Profit margin", "percentage"),
    ("break_even_sales", "Break-even sales", "money"),
    (
        "minimum_whole_break_even_customers",
        "Break-even customers",
        "break_even_count",
    ),
)


def build_comparison(
    scenario_ids: list[int],
    baseline_id: int | None = None,
) -> dict:
    """Recalculate saved Scenarios and prepare every baseline difference."""
    columns = []
    for scenario_id in scenario_ids:
        event_id, identity, scenario = load_event_scenario(scenario_id)
        result = calculate_event_scenario(scenario)
        columns.append(
            {
                "event_id": event_id,
                "scenario_id": scenario_id,
                "identity": identity,
                "scenario": scenario,
                "result": result,
                "warnings": tuple(
                    CalculationWarning(
                        warning["code"],
                        warning["severity"],
                        warning["message"],
                    )
                    for warning in customer_warning_data(result)
                ),
            }
        )
    if len({column["event_id"] for column in columns}) != 1:
        raise ValueError("Scenarios must belong to the same event.")
    if baseline_id not in scenario_ids:
        baseline_id = scenario_ids[0]

    result_rows = _result_rows(columns)
    assumption_rows = _assumption_rows(columns)
    _add_differences(result_rows, columns)
    _add_differences(assumption_rows, columns)
    highlights = _highlights(columns)
    return {
        "columns": columns,
        "result_rows": result_rows,
        "assumption_rows": assumption_rows,
        "baseline_id": baseline_id,
        "highlights": highlights,
    }


def _result_rows(columns: list[dict]) -> list[dict]:
    rows = []
    for key, label, kind in RESULT_ROWS:
        values = {
            column["scenario_id"]: getattr(column["result"], key)
            for column in columns
        }
        rows.append(_row(key, label, kind, values))
    target_values = {}
    for column in columns:
        evaluation = column["result"].profit_target_evaluation
        if evaluation is None or evaluation.is_met is None:
            value = "Not available."
        elif evaluation.is_met:
            value = "Target met"
        else:
            value = "Target not met"
        target_values[column["scenario_id"]] = value
    rows.append(
        _row("profit_target_status", "Profit-target status", "category",
             target_values)
    )
    return rows


def _assumption_rows(columns: list[dict]) -> list[dict]:
    definitions = (
        ("estimated_attendance", "Estimated attendance", "count"),
        ("weather_outlook", "Weather outlook", "category"),
        ("custom_weather_reduction", "Custom weather reduction", "percentage"),
        ("event_protection", "Event protection", "category"),
        (
            "expected_food_buyer_percentage",
            "Percentage expected to buy food",
            "percentage",
        ),
        (
            "other_competing_food_vendors",
            "Other competing food vendors",
            "buyer_count",
        ),
        ("total_food_vendors", "Total food vendors", "count"),
        (
            "estimated_business_buyers",
            "Even-split expected buyers",
            "count",
        ),
        ("average_order_sale_amount", "Average order amount", "money"),
        ("revenue_method", "Expected-sales method", "category"),
        (
            "custom_expected_sales",
            "Custom expected-sales amount",
            "money",
        ),
        ("food_cost_method", "Food-cost method", "category"),
        ("food_cost_value", "Food-cost method value", "category"),
        ("card_sales_percentage", "Sales paid by card", "percentage"),
        (
            "card_processing_percentage",
            "Card-processing percentage",
            "percentage",
        ),
        (
            "fixed_card_processing_fee",
            "Fixed processing fee per transaction",
            "money",
        ),
        ("employee_labor_entries", "Employee labor entries", "category"),
        ("employee_labor_cost", "Total employee labor cost", "money"),
        ("owner_labor_pay", "Owner labor pay", "money"),
        ("travel_cost", "Travel", "money"),
        ("parking_cost", "Parking", "money"),
        ("permit_cost", "Permit", "money"),
        ("generator_utility_cost", "Generator or utility", "money"),
        ("vendor_or_booking_fee", "Vendor or booking fee", "money"),
        (
            "organizer_commission",
            "Organizer commission",
            "percentage",
        ),
        ("additional_costs", "Named miscellaneous costs", "category"),
        ("profit_target_type", "Profit-target type", "category"),
        ("profit_target_value", "Profit-target value", "category"),
    )
    scenario_values = {
        column["scenario_id"]: _scenario_values(column)
        for column in columns
    }
    return [
        _row(
            key,
            label,
            kind,
            {
                scenario_id: values[key]
                for scenario_id, values in scenario_values.items()
            },
        )
        for key, label, kind in definitions
    ]


def _scenario_values(column: dict) -> dict:
    scenario = column["scenario"]
    result = column["result"]
    operating = {
        "__parking_cost__": None,
        "__permit_cost__": None,
        "__generator_utility_cost__": None,
    }
    miscellaneous = []
    for cost in scenario.additional_costs:
        if cost.name in operating:
            operating[cost.name] = cost.amount
        else:
            miscellaneous.append(f"{cost.name}: ${_number(cost.amount)}")
    labor = [
        (
            f"${_number(entry.hourly_rate)}/hour × "
            f"{_number(entry.total_hours_paid)} hours"
        )
        for entry in scenario.employee_labor
    ]
    food = scenario.food_cost
    if food.method == "average_per_order":
        food_value = f"${_number(food.average_cost_per_order)} per order"
    elif food.method == "sales_percentage":
        food_value = f"{_number(food.sales_percentage * 100)}%"
    else:
        food_value = f"${_number(food.manual_event_total)} total"
    target = scenario.profit_target
    target_value = (
        f"${_number(target.minimum_profit_amount)}"
        if target.target_type == "profit_amount"
        else f"{_number(target.minimum_profit_margin * 100)}%"
    )
    return {
        "estimated_attendance": Decimal(
            scenario.demand.estimated_attendance
        ),
        "weather_outlook": _words(scenario.weather.weather_outlook),
        "custom_weather_reduction": scenario.weather.custom_weather_reduction,
        "event_protection": _words(scenario.weather.event_protection),
        "expected_food_buyer_percentage": (
            scenario.demand.expected_food_buyer_percentage
        ),
        "other_competing_food_vendors": Decimal(
            scenario.demand.other_competing_food_vendors
        ),
        "total_food_vendors": Decimal(result.total_food_vendors),
        "estimated_business_buyers": result.estimated_business_buyers,
        "average_order_sale_amount": (
            scenario.revenue.average_order_sale_amount
        ),
        "revenue_method": (
            "Custom expected sales"
            if scenario.revenue.method == "manual_sales"
            else "Calculated from attendance"
        ),
        "custom_expected_sales": scenario.revenue.expected_sales_amount,
        "food_cost_method": _words(food.method),
        "food_cost_value": food_value,
        "card_sales_percentage": scenario.fees.card_sales_percentage,
        "card_processing_percentage": (
            scenario.fees.card_processing_percentage
        ),
        "fixed_card_processing_fee": (
            scenario.fees.fixed_card_processing_fee
        ),
        "employee_labor_entries": (
            "None" if not labor else " | ".join(labor)
        ),
        "employee_labor_cost": result.employee_labor_cost,
        "owner_labor_pay": scenario.owner_labor_pay,
        "travel_cost": scenario.travel_cost,
        "parking_cost": operating["__parking_cost__"],
        "permit_cost": operating["__permit_cost__"],
        "generator_utility_cost": operating[
            "__generator_utility_cost__"
        ],
        "vendor_or_booking_fee": scenario.fees.vendor_or_booking_fee,
        "organizer_commission": (
            scenario.fees.organizer_commission_percentage
        ),
        "additional_costs": (
            "None" if not miscellaneous else " | ".join(miscellaneous)
        ),
        "profit_target_type": _words(target.target_type),
        "profit_target_value": target_value,
    }


def _row(key: str, label: str, kind: str, values: dict) -> dict:
    return {
        "key": key,
        "label": label,
        "kind": kind,
        "values": values,
        "display": {
            scenario_id: _display(value, kind)
            for scenario_id, value in values.items()
        },
        "identical": len(set(values.values())) == 1,
    }


def _add_differences(rows: list[dict], columns: list[dict]) -> None:
    for row in rows:
        row["differences"] = {}
        for baseline in columns:
            baseline_id = baseline["scenario_id"]
            baseline_value = row["values"][baseline_id]
            row["differences"][baseline_id] = {}
            for column in columns:
                scenario_id = column["scenario_id"]
                value = row["values"][scenario_id]
                row["differences"][baseline_id][scenario_id] = (
                    _difference(value, baseline_value, row["kind"])
                )


def _difference(value, baseline, kind: str) -> str:
    if value is None or baseline is None:
        return "Not available."
    if kind == "category":
        return "" if value == baseline else "Different from baseline"
    value = Decimal(value)
    baseline = Decimal(baseline)
    if kind == "buyer_count":
        value = value.to_integral_value(rounding=ROUND_FLOOR)
        baseline = baseline.to_integral_value(rounding=ROUND_FLOOR)
    elif kind == "break_even_count":
        value = value.to_integral_value(rounding=ROUND_CEILING)
        baseline = baseline.to_integral_value(rounding=ROUND_CEILING)
    difference = value - baseline
    sign = "+" if difference > 0 else ""
    if kind == "money":
        return f"{sign}${_number(difference)}"
    if kind == "percentage":
        return f"{sign}{_number(difference * 100)} percentage points"
    return f"{sign}{_number(difference)}"


def _highlights(columns: list[dict]) -> dict:
    def tied(key: str, select):
        available = [
            (column["scenario_id"], getattr(column["result"], key))
            for column in columns
            if getattr(column["result"], key) is not None
        ]
        if not available:
            return []
        selected = select(value for _, value in available)
        return [
            scenario_id
            for scenario_id, value in available
            if value == selected
        ]

    target_met = []
    target_not_met = []
    for column in columns:
        evaluation = column["result"].profit_target_evaluation
        if evaluation is not None and evaluation.is_met is True:
            target_met.append(column["scenario_id"])
        elif evaluation is not None and evaluation.is_met is False:
            target_not_met.append(column["scenario_id"])
    warning_counts = {}
    for column in columns:
        for warning in column["warnings"]:
            warning_counts[warning.code] = (
                warning_counts.get(warning.code, 0) + 1
            )
    warning_differences = {
        column["scenario_id"]: [
            warning
            for warning in column["warnings"]
            if warning_counts[warning.code] < len(columns)
        ]
        for column in columns
    }
    return {
        "highest_profit": tied("business_profit", max),
        "highest_margin": tied("profit_margin", max),
        "lowest_cost": tied("total_event_cost", min),
        "lowest_break_even": tied(
            "minimum_whole_break_even_customers", min
        ),
        "target_met": target_met,
        "target_not_met": target_not_met,
        "warning_differences": warning_differences,
    }


def _display(value, kind: str) -> str:
    if value is None:
        return "Not available."
    if kind == "money":
        return f"${_number(Decimal(value))}"
    if kind == "percentage":
        return f"{_number(Decimal(value) * 100)}%"
    if kind == "buyer_count":
        return str(int(Decimal(value).to_integral_value(rounding=ROUND_FLOOR)))
    if kind == "break_even_count":
        return str(int(Decimal(value).to_integral_value(rounding=ROUND_CEILING)))
    if kind == "count":
        return _number(Decimal(value))
    return str(value)


def _number(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{rounded:,.2f}"


def _words(value: str) -> str:
    return value.replace("_", " ").capitalize()
