from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BusinessDefaults:
    """Reusable assumptions applied when creating an event analysis."""

    business_name: str
    average_order_value: Decimal
    food_cost_percentage: Decimal
    card_sales_percentage: Decimal
    card_processing_percentage: Decimal
    default_staff_count: int
    hourly_labor_cost: Decimal
    setup_hours: Decimal
    cleanup_hours: Decimal
    vehicle_cost_per_mile: Decimal
    minimum_acceptable_profit: Decimal | None = None
    minimum_acceptable_margin: Decimal | None = None