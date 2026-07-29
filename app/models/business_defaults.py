from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LaborDefault:
    """Typical combined worker-hours paid at one hourly rate."""

    hourly_rate: Decimal
    total_hours_paid: Decimal

    def __post_init__(self) -> None:
        if not _is_nonnegative(self.hourly_rate):
            raise ValueError("Hourly labor rate must be nonnegative.")
        if not _is_nonnegative(self.total_hours_paid):
            raise ValueError("Total paid hours must be nonnegative.")


@dataclass(frozen=True)
class BusinessDefaults:
    """Reusable assumptions applied when creating an event analysis."""

    business_name: str
    average_order_sale_amount: Decimal
    food_cost_percentage: Decimal
    card_sales_percentage: Decimal
    card_processing_percentage: Decimal
    labor_entries: tuple[LaborDefault, ...]
    profit_target_type: str
    default_owner_labor_pay: Decimal | None = None
    minimum_profit_amount: Decimal | None = None
    minimum_profit_margin: Decimal | None = None
    default_travel_cost: Decimal | None = None

    def __post_init__(self) -> None:
        money_values = (
            self.average_order_sale_amount,
            self.default_owner_labor_pay,
            self.minimum_profit_amount,
            self.default_travel_cost,
        )
        if any(
            value is not None and not _is_nonnegative(value)
            for value in money_values
        ):
            raise ValueError("Money values must be nonnegative.")

        percentages = (
            self.food_cost_percentage,
            self.card_sales_percentage,
            self.card_processing_percentage,
        )
        if any(not _is_percentage(value) for value in percentages):
            raise ValueError("Percentages must be between 0 and 1.")

        if not self.labor_entries:
            raise ValueError("At least one labor entry is required.")

        if self.profit_target_type == "profit_amount":
            if self.minimum_profit_amount is None:
                raise ValueError("The selected profit target needs a value.")
            if self.minimum_profit_margin is not None:
                raise ValueError("The unselected profit target must be empty.")
        elif self.profit_target_type == "profit_margin":
            if self.minimum_profit_margin is None:
                raise ValueError("The selected profit target needs a value.")
            if not _is_percentage(self.minimum_profit_margin):
                raise ValueError("Percentages must be between 0 and 1.")
            if self.minimum_profit_amount is not None:
                raise ValueError("The unselected profit target must be empty.")
        else:
            raise ValueError("Profit target type is invalid.")


def _is_nonnegative(value: Decimal) -> bool:
    return value.is_finite() and value >= 0


def _is_percentage(value: Decimal) -> bool:
    return value.is_finite() and Decimal("0") <= value <= Decimal("1")
