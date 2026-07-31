from datetime import date, time
from decimal import Decimal, InvalidOperation

from werkzeug.datastructures import MultiDict

from app.models import EventIdentity


IDENTITY_FIELDS = ("event_name", "event_date", "start_time", "location")
REVENUE_FIELDS = (
    "estimated_attendance",
    "competing_food_vendors",
    "expected_buyer_percentage",
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


def blank_event_inputs_form() -> dict[str, str]:
    values = {
        name: ""
        for name in (*IDENTITY_FIELDS, *REVENUE_FIELDS, *FOOD_COST_FIELDS)
    }
    values["revenue_method"] = "attendance"
    values["food_cost_method_choice"] = "average_per_order"
    return values


def validate_event_inputs(
    submitted: MultiDict,
) -> tuple[EventIdentity | None, dict[str, str], dict[str, str]]:
    """Validate the currently implemented portions of Event Inputs."""
    values = {
        name: submitted.get(name, "").strip()
        for name in (*IDENTITY_FIELDS, *REVENUE_FIELDS, *FOOD_COST_FIELDS)
    }
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
        "competing_food_vendors",
        "Number of competing food vendors",
    )
    _percentage(
        values,
        errors,
        "expected_buyer_percentage",
        "Expected buyer percentage",
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

    if errors:
        return None, values, errors

    identity = EventIdentity(
        event_name=values["event_name"],
        event_date=event_date,
        start_time=start_time,
        location=values["location"],
    )
    return identity, values, errors


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
