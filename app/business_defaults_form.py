from decimal import Decimal, InvalidOperation

from werkzeug.datastructures import MultiDict

from app.models import BusinessDefaults, LaborDefault


SCALAR_FIELDS = (
    "business_name",
    "average_order_sale_amount",
    "food_cost_percentage",
    "card_sales_percentage",
    "card_processing_percentage",
    "default_travel_cost",
    "default_owner_labor_pay",
)


def defaults_to_form(defaults: BusinessDefaults | None) -> dict:
    """Create customer-facing display values for the defaults form."""
    if defaults is None:
        return {
            **{name: "" for name in SCALAR_FIELDS},
            "profit_target_type": "",
            "minimum_profit_amount": "",
            "minimum_profit_margin": "",
            "labor_entries": [{"hourly_rate": "", "total_hours_paid": ""}],
        }
    return {
        "business_name": defaults.business_name,
        "average_order_sale_amount": _format_decimal(
            defaults.average_order_sale_amount
        ),
        "food_cost_percentage": _format_percentage(
            defaults.food_cost_percentage
        ),
        "card_sales_percentage": _format_percentage(
            defaults.card_sales_percentage
        ),
        "card_processing_percentage": _format_percentage(
            defaults.card_processing_percentage
        ),
        "default_travel_cost": _format_optional_decimal(
            defaults.default_travel_cost
        ),
        "default_owner_labor_pay": _format_optional_decimal(
            defaults.default_owner_labor_pay
        ),
        "profit_target_type": defaults.profit_target_type or "",
        "minimum_profit_amount": _format_optional_decimal(
            defaults.minimum_profit_amount
        ),
        "minimum_profit_margin": _format_optional_percentage(
            defaults.minimum_profit_margin
        ),
        "labor_entries": [
            {
                "hourly_rate": _format_decimal(entry.hourly_rate),
                "total_hours_paid": _format_decimal(
                    entry.total_hours_paid
                ),
            }
            for entry in defaults.labor_entries
        ],
    }


def validate_defaults_form(
    submitted: MultiDict,
) -> tuple[BusinessDefaults | None, dict, dict]:
    """Validate submitted display values and build a domain model."""
    values = {
        name: submitted.get(name, "").strip()
        for name in SCALAR_FIELDS
    }
    values["profit_target_type"] = submitted.get(
        "profit_target_type", ""
    ).strip()
    values["minimum_profit_amount"] = submitted.get(
        "minimum_profit_amount", ""
    ).strip()
    values["minimum_profit_margin"] = submitted.get(
        "minimum_profit_margin", ""
    ).strip()
    rates = submitted.getlist("labor_rate")
    hours = submitted.getlist("labor_hours")
    values["labor_entries"] = [
        {
            "hourly_rate": rates[index].strip() if index < len(rates) else "",
            "total_hours_paid": (
                hours[index].strip() if index < len(hours) else ""
            ),
        }
        for index in range(max(len(rates), len(hours)))
    ]
    errors: dict = {"labor_entries": []}

    average_sale = _decimal_field(
        values, errors, "average_order_sale_amount",
        "Average order sale amount", minimum=Decimal("0"),
        exclusive_minimum=True, scale=2
    )
    food_cost = _percentage_field(
        values, errors, "food_cost_percentage", "Food and packaging cost"
    )
    card_sales = _percentage_field(
        values, errors, "card_sales_percentage", "Sales paid by card"
    )
    card_processing = _percentage_field(
        values, errors, "card_processing_percentage", "Card processing fee"
    )
    travel_cost = _decimal_field(
        values, errors, "default_travel_cost", "Default travel cost",
        minimum=Decimal("0"), scale=2, required=False
    )
    owner_labor_pay = _decimal_field(
        values, errors, "default_owner_labor_pay",
        "Default owner labor pay", minimum=Decimal("0"), scale=2,
        required=False
    )
    target_type = values["profit_target_type"]
    minimum_profit = None
    minimum_margin = None
    if target_type == "profit_amount":
        values["minimum_profit_margin"] = ""
        minimum_profit = _decimal_field(
            values, errors, "minimum_profit_amount",
            "Minimum profit amount", minimum=Decimal("0"), scale=2
        )
    elif target_type == "profit_margin":
        values["minimum_profit_amount"] = ""
        minimum_margin = _percentage_field(
            values, errors, "minimum_profit_margin",
            "Minimum profit margin"
        )
    else:
        errors["profit_target_type"] = "Choose how you evaluate an event."

    labor_defaults = []
    if not values["labor_entries"]:
        errors["labor"] = "Add at least one labor entry."
    for entry in values["labor_entries"]:
        entry_errors = {}
        rate = _entry_decimal(
            entry, entry_errors, "hourly_rate", "Hourly labor rate",
            scale=2
        )
        total_hours = _entry_decimal(
            entry, entry_errors, "total_hours_paid",
            "Total hours paid at that rate"
        )
        if (
            total_hours is not None
            and total_hours * 60
            != (total_hours * 60).to_integral_value()
        ):
            entry_errors["total_hours_paid"] = (
                "Total hours must use whole-minute increments."
            )
        errors["labor_entries"].append(entry_errors)
        if not entry_errors:
            labor_defaults.append(
                LaborDefault(
                    hourly_rate=rate,
                    total_hours_paid=total_hours,
                )
            )

    has_errors = any(
        value for key, value in errors.items() if key != "labor_entries"
    ) or any(errors["labor_entries"])
    if has_errors:
        return None, values, errors

    return (
        BusinessDefaults(
            business_name=values["business_name"],
            average_order_sale_amount=average_sale,
            food_cost_percentage=food_cost,
            card_sales_percentage=card_sales,
            card_processing_percentage=card_processing,
            labor_entries=tuple(labor_defaults),
            default_owner_labor_pay=owner_labor_pay,
            profit_target_type=target_type,
            minimum_profit_amount=minimum_profit,
            minimum_profit_margin=minimum_margin,
            default_travel_cost=travel_cost,
        ),
        values,
        errors,
    )


def _decimal_field(
    values, errors, name, label, *, minimum, exclusive_minimum=False,
    scale=None, required=True
):
    raw_value = values[name]
    if not raw_value:
        if required:
            errors[name] = f"{label} is required."
        return None
    value = _parse_decimal(raw_value, errors, name, label)
    if value is None:
        return None
    if value < minimum or (exclusive_minimum and value == minimum):
        comparison = "greater than 0" if exclusive_minimum else "0 or more"
        errors[name] = f"{label} must be {comparison}."
    elif scale is not None and value.as_tuple().exponent < -scale:
        errors[name] = f"{label} can have at most {scale} decimal places."
    return value


def _entry_decimal(entry, errors, name, label, scale=None):
    raw_value = entry[name]
    if not raw_value:
        errors[name] = f"{label} is required."
        return None
    value = _parse_decimal(raw_value, errors, name, label)
    if value is None:
        return None
    if value < 0:
        errors[name] = f"{label} cannot be negative."
    elif scale is not None and value.as_tuple().exponent < -scale:
        errors[name] = f"{label} can have at most {scale} decimal places."
    return value


def _parse_decimal(raw_value, errors, name, label):
    try:
        value = Decimal(raw_value)
    except InvalidOperation:
        errors[name] = f"{label} must be a number."
        return None
    if not value.is_finite():
        errors[name] = f"{label} must be a number."
        return None
    return value


def _percentage_field(values, errors, name, label, *, required=True):
    value = _decimal_field(
        values, errors, name, label, minimum=Decimal("0"),
        scale=2, required=required
    )
    if value is not None and value > 100:
        errors[name] = f"{label} must be between 0 and 100."
    return None if value is None else value / Decimal("100")


def _format_decimal(value: Decimal) -> str:
    formatted = format(value, "f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted or "0"


def _format_percentage(value: Decimal) -> str:
    return _format_decimal(value * 100)


def _format_optional_decimal(value: Decimal | None) -> str:
    return "" if value is None else _format_decimal(value)


def _format_optional_percentage(value: Decimal | None) -> str:
    return "" if value is None else _format_percentage(value)
