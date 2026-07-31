from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal


EVENT_PROTECTION_CHOICES = {
    "fully_indoors",
    "covered_reliable_seating",
    "partially_covered",
    "fully_outdoors",
}
WEATHER_OUTLOOK_CHOICES = {
    "favorable",
    "minor_concern",
    "moderate_adverse",
    "significant_adverse",
    "severe_disruption",
    "custom",
}
REVENUE_METHODS = {"attendance", "manual_sales"}
FOOD_COST_METHODS = {
    "average_per_order",
    "sales_percentage",
    "manual_event_total",
}
PROFIT_TARGET_TYPES = {"profit_amount", "profit_margin"}


@dataclass(frozen=True)
class EventIdentity:
    event_name: str
    event_date: date
    start_time: time
    location: str

    def __post_init__(self) -> None:
        if (
            not self.event_name.strip()
            or not self.location.strip()
            or not isinstance(self.event_date, date)
            or not isinstance(self.start_time, time)
        ):
            raise ValueError("Required event identity values cannot be blank.")


@dataclass(frozen=True)
class DemandAssumptions:
    estimated_attendance: int
    other_competing_food_vendors: int
    expected_food_buyer_percentage: Decimal

    def __post_init__(self) -> None:
        if self.estimated_attendance < 0 or self.other_competing_food_vendors < 0:
            raise ValueError("Demand counts cannot be negative.")
        _require_percentage(self.expected_food_buyer_percentage)


@dataclass(frozen=True)
class WeatherAssumptions:
    event_protection: str
    weather_outlook: str
    custom_weather_reduction: Decimal | None = None

    def __post_init__(self) -> None:
        if self.event_protection not in EVENT_PROTECTION_CHOICES:
            raise ValueError("Event protection choice is invalid.")
        if self.weather_outlook not in WEATHER_OUTLOOK_CHOICES:
            raise ValueError("Weather outlook choice is invalid.")
        if self.weather_outlook == "custom":
            if self.custom_weather_reduction is None:
                raise ValueError("Custom weather requires a reduction.")
            _require_percentage(self.custom_weather_reduction)
        elif self.custom_weather_reduction is not None:
            raise ValueError("Only custom weather may have a custom reduction.")


@dataclass(frozen=True)
class RevenueAssumptions:
    method: str
    average_order_sale_amount: Decimal | None = None
    expected_sales_amount: Decimal | None = None

    def __post_init__(self) -> None:
        if self.method not in REVENUE_METHODS:
            raise ValueError("Revenue method is invalid.")
        _require_selected_value(
            selected=self.method,
            expected="attendance",
            selected_value=self.average_order_sale_amount,
            unselected_value=self.expected_sales_amount,
        )
        if self.average_order_sale_amount is not None:
            _require_nonnegative_money(self.average_order_sale_amount)
        if self.expected_sales_amount is not None:
            _require_nonnegative_money(self.expected_sales_amount)


@dataclass(frozen=True)
class FoodCostAssumptions:
    method: str
    average_cost_per_order: Decimal | None = None
    sales_percentage: Decimal | None = None
    manual_event_total: Decimal | None = None

    def __post_init__(self) -> None:
        if self.method not in FOOD_COST_METHODS:
            raise ValueError("Food-cost method is invalid.")
        values = {
            "average_per_order": self.average_cost_per_order,
            "sales_percentage": self.sales_percentage,
            "manual_event_total": self.manual_event_total,
        }
        _require_exactly_selected(self.method, values)
        if self.average_cost_per_order is not None:
            _require_nonnegative_money(self.average_cost_per_order)
        if self.sales_percentage is not None:
            _require_percentage(self.sales_percentage)
        if self.manual_event_total is not None:
            _require_nonnegative_money(self.manual_event_total)


@dataclass(frozen=True)
class PaymentAndOrganizerFees:
    card_sales_percentage: Decimal
    card_processing_percentage: Decimal
    vendor_or_booking_fee: Decimal
    fixed_card_processing_fee: Decimal | None = None
    organizer_commission_percentage: Decimal | None = None

    def __post_init__(self) -> None:
        _require_percentage(self.card_sales_percentage)
        _require_percentage(self.card_processing_percentage)
        _require_nonnegative_money(self.vendor_or_booking_fee)
        if self.fixed_card_processing_fee is not None:
            _require_nonnegative_money(self.fixed_card_processing_fee)
        if self.organizer_commission_percentage is not None:
            _require_percentage(self.organizer_commission_percentage)


@dataclass(frozen=True)
class EmployeeLaborEntry:
    hourly_rate: Decimal
    total_hours_paid: Decimal

    def __post_init__(self) -> None:
        _require_nonnegative(self.hourly_rate, "Labor rate")
        _require_nonnegative(self.total_hours_paid, "Paid hours")


@dataclass(frozen=True)
class AdditionalEventCost:
    name: str
    amount: Decimal

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Additional event costs require a name.")
        _require_nonnegative_money(self.amount)


@dataclass(frozen=True)
class ProfitTarget:
    target_type: str
    minimum_profit_amount: Decimal | None = None
    minimum_profit_margin: Decimal | None = None

    def __post_init__(self) -> None:
        if self.target_type not in PROFIT_TARGET_TYPES:
            raise ValueError("Profit target type is invalid.")
        _require_selected_value(
            selected=self.target_type,
            expected="profit_amount",
            selected_value=self.minimum_profit_amount,
            unselected_value=self.minimum_profit_margin,
        )
        if self.minimum_profit_amount is not None:
            _require_nonnegative_money(self.minimum_profit_amount)
        if self.minimum_profit_margin is not None:
            _require_percentage(self.minimum_profit_margin)


@dataclass(frozen=True)
class EventScenario:
    scenario_name: str
    demand: DemandAssumptions
    weather: WeatherAssumptions
    revenue: RevenueAssumptions
    food_cost: FoodCostAssumptions
    fees: PaymentAndOrganizerFees
    profit_target: ProfitTarget
    notes: str | None = None
    employee_labor: tuple[EmployeeLaborEntry, ...] = ()
    owner_labor_pay: Decimal | None = None
    travel_cost: Decimal | None = None
    additional_costs: tuple[AdditionalEventCost, ...] = ()

    def __post_init__(self) -> None:
        if not self.scenario_name.strip():
            raise ValueError("Scenario name cannot be blank.")
        if self.owner_labor_pay is not None:
            _require_nonnegative_money(self.owner_labor_pay)
        if self.travel_cost is not None:
            _require_nonnegative_money(self.travel_cost)


@dataclass(frozen=True)
class Event:
    identity: EventIdentity
    scenarios: tuple[EventScenario, ...] = ()

    def __post_init__(self) -> None:
        if not self.scenarios:
            raise ValueError("An event requires at least one scenario.")


def _require_selected_value(
    *,
    selected: str,
    expected: str,
    selected_value: Decimal | None,
    unselected_value: Decimal | None,
) -> None:
    if selected == expected:
        if selected_value is None:
            raise ValueError("The selected method requires a value.")
        if unselected_value is not None:
            raise ValueError("An unselected method cannot have a value.")
    else:
        if unselected_value is None:
            raise ValueError("The selected method requires a value.")
        if selected_value is not None:
            raise ValueError("An unselected method cannot have a value.")


def _require_exactly_selected(
    selected: str,
    values: dict[str, Decimal | None],
) -> None:
    if values[selected] is None:
        raise ValueError("The selected method requires a value.")
    if any(value is not None for key, value in values.items() if key != selected):
        raise ValueError("An unselected method cannot have a value.")


def _require_nonnegative_money(value: Decimal) -> None:
    _require_nonnegative(value, "Money")


def _require_nonnegative(value: Decimal, label: str) -> None:
    if not value.is_finite() or value < 0:
        raise ValueError(f"{label} cannot be negative or non-finite.")


def _require_percentage(value: Decimal) -> None:
    if (
        not value.is_finite()
        or value < Decimal("0")
        or value > Decimal("1")
    ):
        raise ValueError("Percentage must be between 0 and 1.")
