from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LaborDefault:
    """Typical combined worker-hours paid at one hourly rate."""

    hourly_rate: Decimal
    total_hours_paid: Decimal


@dataclass(frozen=True)
class BusinessDefaults:
    """Reusable assumptions applied when creating an event analysis."""

    business_name: str
    average_order_sale_amount: Decimal
    food_cost_percentage: Decimal
    card_sales_percentage: Decimal
    card_processing_percentage: Decimal
    labor_entries: tuple[LaborDefault, ...]
    default_owner_labor_pay: Decimal | None = None
    profit_target_type: str | None = None
    minimum_profit_amount: Decimal | None = None
    minimum_profit_margin: Decimal | None = None
    default_travel_cost: Decimal | None = None
