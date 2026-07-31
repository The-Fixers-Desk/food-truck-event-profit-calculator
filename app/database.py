import sqlite3
from datetime import date, time
from decimal import Decimal
from pathlib import Path

from flask import current_app, g

from app.models import (
    AdditionalEventCost,
    BusinessDefaults,
    DemandAssumptions,
    EmployeeLaborEntry,
    EventIdentity,
    EventScenario,
    FoodCostAssumptions,
    LaborDefault,
    PaymentAndOrganizerFees,
    ProfitTarget,
    RevenueAssumptions,
    WeatherAssumptions,
)


SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "business_defaults.sql"
EVENT_ANALYSIS_SCHEMA_PATH = (
    Path(__file__).resolve().parent / "schema" / "event_analysis.sql"
)


def apply_business_defaults_schema(connection: sqlite3.Connection) -> None:
    """Create the business-defaults tables on a database connection."""
    connection.execute("PRAGMA foreign_keys = ON")
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    connection.executescript(schema)


def apply_event_analysis_schema(connection: sqlite3.Connection) -> None:
    """Create saved-event tables without changing existing defaults tables."""
    connection.execute("PRAGMA foreign_keys = ON")
    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(event_scenarios)"
        ).fetchall()
    }
    if columns and "expected_food_buyer_basis_points" not in columns:
        _upgrade_event_demand_columns(connection)
        columns.update(
            {
                "other_competing_food_vendors",
                "expected_food_buyer_basis_points",
            }
        )
    if columns and "manual_average_order_sale_amount_cents" not in columns:
        connection.execute(
            """
            ALTER TABLE event_scenarios
            ADD COLUMN manual_average_order_sale_amount_cents INTEGER
                CHECK (
                    manual_average_order_sale_amount_cents IS NULL
                    OR manual_average_order_sale_amount_cents >= 0
                )
            """
        )
        connection.commit()
    schema = EVENT_ANALYSIS_SCHEMA_PATH.read_text(encoding="utf-8")
    connection.executescript(schema)


def _upgrade_event_demand_columns(
    database: sqlite3.Connection,
) -> None:
    """Add new demand fields without reinterpreting legacy saved demand."""
    database.execute(
        """
        ALTER TABLE event_scenarios
        ADD COLUMN other_competing_food_vendors INTEGER
            CHECK (
                other_competing_food_vendors IS NULL
                OR other_competing_food_vendors >= 0
            )
        """
    )
    database.execute(
        """
        ALTER TABLE event_scenarios
        ADD COLUMN expected_food_buyer_basis_points INTEGER
            CHECK (
                expected_food_buyer_basis_points IS NULL
                OR expected_food_buyer_basis_points BETWEEN 0 AND 10000
            )
        """
    )
    database.commit()


def get_database() -> sqlite3.Connection:
    """Return the database connection for the current request."""
    if "database" not in g:
        database_path = Path(current_app.config["DATABASE"])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        g.database = sqlite3.connect(database_path)
        g.database.row_factory = sqlite3.Row
        g.database.execute("PRAGMA foreign_keys = ON")
    return g.database


def close_database(exception: BaseException | None = None) -> None:
    """Close the current request's database connection."""
    database = g.pop("database", None)
    if database is not None:
        database.close()


def initialize_database() -> None:
    """Create, adopt, or upgrade the database through formal migrations."""
    from app.migrations import migrate_database

    migrate_database(get_database(), logger=current_app.logger)


def load_business_defaults() -> BusinessDefaults | None:
    """Load the single saved defaults record and its ordered labor entries."""
    database = get_database()
    row = database.execute(
        "SELECT * FROM business_defaults WHERE id = 1"
    ).fetchone()
    if row is None:
        return None
    labor_rows = database.execute(
        """
        SELECT hourly_rate_cents, total_paid_minutes
        FROM business_default_labor_entries
        WHERE business_defaults_id = 1
        ORDER BY position
        """
    ).fetchall()
    return BusinessDefaults(
        business_name=row["business_name"],
        average_order_sale_amount=_cents_to_decimal(
            row["average_order_sale_amount_cents"]
        ),
        food_cost_method=row["food_cost_method"],
        average_food_cost_per_order=_optional_cents_to_decimal(
            row["average_food_cost_per_order_cents"]
        ),
        food_cost_percentage=_optional_basis_points_to_decimal(
            row["food_cost_percentage_basis_points"]
        ),
        typical_food_cost_total=_optional_cents_to_decimal(
            row["typical_food_cost_total_cents"]
        ),
        card_sales_percentage=_basis_points_to_decimal(
            row["card_sales_basis_points"]
        ),
        card_processing_percentage=_basis_points_to_decimal(
            row["card_processing_basis_points"]
        ),
        labor_entries=tuple(
            LaborDefault(
                hourly_rate=_cents_to_decimal(item["hourly_rate_cents"]),
                total_hours_paid=_minutes_to_hours(
                    item["total_paid_minutes"]
                ),
            )
            for item in labor_rows
        ),
        default_owner_labor_pay=_optional_cents_to_decimal(
            row["default_owner_labor_pay_cents"]
        ),
        default_travel_cost=_optional_cents_to_decimal(
            row["default_travel_cost_cents"]
        ),
        profit_target_type=row["profit_target_type"],
        minimum_profit_amount=_optional_cents_to_decimal(
            row["minimum_profit_amount_cents"]
        ),
        minimum_profit_margin=_optional_basis_points_to_decimal(
            row["minimum_profit_margin_basis_points"]
        ),
    )


def business_defaults_setup_is_complete() -> bool:
    """Return whether a valid business-defaults record has been saved."""
    try:
        return load_business_defaults() is not None
    except (sqlite3.Error, ValueError):
        return False


def save_business_defaults(defaults: BusinessDefaults) -> None:
    """Atomically save the defaults record and replace its labor entries."""
    database = get_database()
    with database:
        database.execute(
            """
            INSERT INTO business_defaults (
                id, business_name, average_order_sale_amount_cents,
                food_cost_method, average_food_cost_per_order_cents,
                food_cost_percentage_basis_points,
                typical_food_cost_total_cents, card_sales_basis_points,
                card_processing_basis_points, default_travel_cost_cents,
                default_owner_labor_pay_cents,
                profit_target_type, minimum_profit_amount_cents,
                minimum_profit_margin_basis_points
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                business_name = excluded.business_name,
                average_order_sale_amount_cents =
                    excluded.average_order_sale_amount_cents,
                food_cost_method = excluded.food_cost_method,
                average_food_cost_per_order_cents =
                    excluded.average_food_cost_per_order_cents,
                food_cost_percentage_basis_points =
                    excluded.food_cost_percentage_basis_points,
                typical_food_cost_total_cents =
                    excluded.typical_food_cost_total_cents,
                card_sales_basis_points = excluded.card_sales_basis_points,
                card_processing_basis_points =
                    excluded.card_processing_basis_points,
                default_travel_cost_cents =
                    excluded.default_travel_cost_cents,
                default_owner_labor_pay_cents =
                    excluded.default_owner_labor_pay_cents,
                profit_target_type = excluded.profit_target_type,
                minimum_profit_amount_cents =
                    excluded.minimum_profit_amount_cents,
                minimum_profit_margin_basis_points =
                    excluded.minimum_profit_margin_basis_points,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                defaults.business_name,
                _decimal_to_cents(defaults.average_order_sale_amount),
                defaults.food_cost_method,
                _optional_decimal_to_cents(
                    defaults.average_food_cost_per_order
                ),
                _optional_decimal_to_basis_points(
                    defaults.food_cost_percentage
                ),
                _optional_decimal_to_cents(defaults.typical_food_cost_total),
                _decimal_to_basis_points(defaults.card_sales_percentage),
                _decimal_to_basis_points(
                    defaults.card_processing_percentage
                ),
                _optional_decimal_to_cents(defaults.default_travel_cost),
                _optional_decimal_to_cents(
                    defaults.default_owner_labor_pay
                ),
                defaults.profit_target_type,
                _optional_decimal_to_cents(
                    defaults.minimum_profit_amount
                ),
                _optional_decimal_to_basis_points(
                    defaults.minimum_profit_margin
                ),
            ),
        )
        database.execute(
            """
            DELETE FROM business_default_labor_entries
            WHERE business_defaults_id = 1
            """
        )
        database.executemany(
            """
            INSERT INTO business_default_labor_entries (
                business_defaults_id, position, hourly_rate_cents,
                total_paid_minutes
            )
            VALUES (1, ?, ?, ?)
            """,
            [
                (
                    position,
                    _decimal_to_cents(entry.hourly_rate),
                    _hours_to_minutes(entry.total_hours_paid),
                )
                for position, entry in enumerate(defaults.labor_entries)
            ],
        )


class ScenarioNameConflict(ValueError):
    """Raised when an Event already has the requested Scenario name."""


class FinalScenarioDeletionError(ValueError):
    """Raised when individual deletion would leave an Event empty."""


def list_saved_events() -> list[dict]:
    """Return Events and Scenarios in deterministic modified-first order."""
    database = get_database()
    event_rows = database.execute(
        """
        SELECT e.*, COUNT(s.id) AS scenario_count,
               CASE
                   WHEN MAX(s.updated_at) > e.updated_at
                   THEN MAX(s.updated_at)
                   ELSE e.updated_at
               END AS last_modified
        FROM events AS e
        JOIN event_scenarios AS s ON s.event_id = e.id
        GROUP BY e.id
        ORDER BY last_modified DESC, e.id DESC
        """
    ).fetchall()
    events = []
    for event in event_rows:
        scenarios = database.execute(
            """
            SELECT id, scenario_name, updated_at
            FROM event_scenarios
            WHERE event_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (event["id"],),
        ).fetchall()
        events.append(
            {
                "id": event["id"],
                "event_name": event["event_name"],
                "event_date": event["event_date"],
                "start_time": _minutes_to_clock(
                    event["start_time_minutes"]
                ),
                "location": event["location"],
                "scenario_count": event["scenario_count"],
                "last_modified": event["last_modified"],
                "scenarios": [dict(row) for row in scenarios],
            }
        )
    return events


def saved_event_counts() -> tuple[int, int]:
    """Return the persisted Event and Scenario counts."""
    row = get_database().execute(
        """
        SELECT
            (SELECT COUNT(*) FROM events) AS event_count,
            (SELECT COUNT(*) FROM event_scenarios) AS scenario_count
        """
    ).fetchone()
    return row["event_count"], row["scenario_count"]


def rename_event(event_id: int, name: str) -> bool:
    """Rename only an Event and update its modified timestamp."""
    database = get_database()
    with database:
        cursor = database.execute(
            """
            UPDATE events
            SET event_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (name.strip(), event_id),
        )
    return cursor.rowcount == 1


def rename_event_scenario(scenario_id: int, name: str) -> bool:
    """Rename one Scenario while enforcing per-Event uniqueness."""
    database = get_database()
    row = database.execute(
        "SELECT event_id FROM event_scenarios WHERE id = ?",
        (scenario_id,),
    ).fetchone()
    if row is None:
        return False
    event_id = row["event_id"]
    if database.execute(
        """
        SELECT 1 FROM event_scenarios
        WHERE event_id = ? AND id <> ?
          AND lower(trim(scenario_name)) = lower(?)
        """,
        (event_id, scenario_id, name.strip()),
    ).fetchone():
        raise ScenarioNameConflict(
            "A scenario with this name already exists for this event."
        )
    try:
        with database:
            database.execute(
                """
                UPDATE event_scenarios
                SET scenario_name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name.strip(), scenario_id),
            )
            _touch_event(database, event_id)
    except sqlite3.IntegrityError as error:
        raise ScenarioNameConflict(
            "A scenario with this name already exists for this event."
        ) from error
    return True


def delete_event_scenario(scenario_id: int) -> bool:
    """Delete a non-final Scenario and its children transactionally."""
    database = get_database()
    row = database.execute(
        "SELECT event_id FROM event_scenarios WHERE id = ?",
        (scenario_id,),
    ).fetchone()
    if row is None:
        return False
    event_id = row["event_id"]
    count = database.execute(
        "SELECT COUNT(*) FROM event_scenarios WHERE event_id = ?",
        (event_id,),
    ).fetchone()[0]
    if count <= 1:
        raise FinalScenarioDeletionError(
            "The final scenario cannot be deleted individually. "
            "Delete the complete event instead."
        )
    with database:
        database.execute(
            "DELETE FROM event_scenarios WHERE id = ?",
            (scenario_id,),
        )
        _touch_event(database, event_id)
    return True


def delete_event(event_id: int) -> bool:
    """Transactionally delete an Event and all cascading child records."""
    database = get_database()
    with database:
        return _delete_event_row(database, event_id) == 1


def _delete_event_row(
    database: sqlite3.Connection,
    event_id: int,
) -> int:
    return database.execute(
        "DELETE FROM events WHERE id = ?", (event_id,)
    ).rowcount


def _touch_event(database: sqlite3.Connection, event_id: int) -> None:
    database.execute(
        """
        UPDATE events SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """,
        (event_id,),
    )


def create_event_with_initial_scenario(
    identity: EventIdentity,
    scenario: EventScenario,
) -> tuple[int, int]:
    """Atomically create an Event and its first complete Scenario."""
    database = get_database()
    with database:
        cursor = database.execute(
            """
            INSERT INTO events (
                event_name, event_date, start_time_minutes, location
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                identity.event_name,
                identity.event_date.isoformat(),
                identity.start_time.hour * 60 + identity.start_time.minute,
                identity.location,
            ),
        )
        event_id = cursor.lastrowid
        scenario_id = _insert_event_scenario(
            database, event_id, scenario
        )
    return event_id, scenario_id


def create_event_scenario(
    event_id: int,
    scenario: EventScenario,
) -> int:
    """Atomically add a uniquely named Scenario to an Event."""
    database = get_database()
    name = scenario.scenario_name.strip()
    if _scenario_name_exists(database, event_id, name):
        raise ScenarioNameConflict(
            "A scenario with this name already exists for this event."
        )
    try:
        with database:
            scenario_id = _insert_event_scenario(
                database, event_id, scenario
            )
            _touch_event(database, event_id)
            return scenario_id
    except sqlite3.IntegrityError as error:
        if _scenario_name_exists(database, event_id, name):
            raise ScenarioNameConflict(
                "A scenario with this name already exists for this event."
            ) from error
        raise


def overwrite_event_scenario(
    scenario_id: int,
    scenario: EventScenario,
) -> None:
    """Atomically replace assumptions and ordered children for a Scenario."""
    database = get_database()
    existing = database.execute(
        """
        SELECT event_id, scenario_name
        FROM event_scenarios WHERE id = ?
        """,
        (scenario_id,),
    ).fetchone()
    if existing is None:
        raise ValueError("The active scenario no longer exists.")
    stored_scenario = EventScenario(
        scenario_name=existing["scenario_name"],
        demand=scenario.demand,
        weather=scenario.weather,
        revenue=scenario.revenue,
        food_cost=scenario.food_cost,
        fees=scenario.fees,
        profit_target=scenario.profit_target,
        notes=scenario.notes,
        employee_labor=scenario.employee_labor,
        owner_labor_pay=scenario.owner_labor_pay,
        travel_cost=scenario.travel_cost,
        additional_costs=scenario.additional_costs,
    )
    with database:
        database.execute(
            "DELETE FROM event_scenario_employee_labor_entries "
            "WHERE event_scenario_id = ?",
            (scenario_id,),
        )
        database.execute(
            "DELETE FROM event_scenario_additional_costs "
            "WHERE event_scenario_id = ?",
            (scenario_id,),
        )
        assignments, values = _scenario_assignments(stored_scenario)
        database.execute(
            f"""
            UPDATE event_scenarios
            SET {assignments}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (*values, scenario_id),
        )
        _insert_scenario_children(database, scenario_id, stored_scenario)
        _touch_event(database, existing["event_id"])


def load_event_scenario(
    scenario_id: int,
) -> tuple[int, EventIdentity, EventScenario]:
    """Load Event identity and a complete Scenario from scaled storage."""
    database = get_database()
    row = database.execute(
        """
        SELECT s.*, e.event_name, e.event_date, e.start_time_minutes,
               e.location
        FROM event_scenarios AS s
        JOIN events AS e ON e.id = s.event_id
        WHERE s.id = ?
        """,
        (scenario_id,),
    ).fetchone()
    if row is None:
        raise ValueError("The active scenario no longer exists.")
    labor_rows = database.execute(
        """
        SELECT hourly_rate_cents, total_paid_minutes
        FROM event_scenario_employee_labor_entries
        WHERE event_scenario_id = ? ORDER BY position
        """,
        (scenario_id,),
    ).fetchall()
    cost_rows = database.execute(
        """
        SELECT cost_name, amount_cents
        FROM event_scenario_additional_costs
        WHERE event_scenario_id = ? ORDER BY position
        """,
        (scenario_id,),
    ).fetchall()
    minutes = row["start_time_minutes"]
    identity = EventIdentity(
        row["event_name"],
        date.fromisoformat(row["event_date"]),
        time(minutes // 60, minutes % 60),
        row["location"],
    )
    scenario = EventScenario(
        scenario_name=row["scenario_name"],
        notes=row["notes"],
        demand=DemandAssumptions(
            row["estimated_attendance"],
            row["other_competing_food_vendors"],
            _basis_points_to_decimal(
                row["expected_food_buyer_basis_points"]
            ),
        ),
        weather=WeatherAssumptions(
            row["event_protection"],
            row["weather_outlook"],
            _optional_basis_points_to_decimal(
                row["custom_weather_reduction_basis_points"]
            ),
        ),
        revenue=RevenueAssumptions(
            row["revenue_method"],
            average_order_sale_amount=_cents_to_decimal(
                row["average_order_sale_amount_cents"]
                if row["revenue_method"] == "attendance"
                else row["manual_average_order_sale_amount_cents"]
            ),
            expected_sales_amount=_optional_cents_to_decimal(
                row["expected_sales_amount_cents"]
            ),
        ),
        food_cost=FoodCostAssumptions(
            row["food_cost_method"],
            _optional_cents_to_decimal(
                row["average_food_cost_per_order_cents"]
            ),
            _optional_basis_points_to_decimal(
                row["food_cost_percentage_basis_points"]
            ),
            _optional_cents_to_decimal(
                row["manual_food_cost_total_cents"]
            ),
        ),
        fees=PaymentAndOrganizerFees(
            _basis_points_to_decimal(row["card_sales_basis_points"]),
            _basis_points_to_decimal(
                row["card_processing_basis_points"]
            ),
            _cents_to_decimal(row["vendor_or_booking_fee_cents"]),
            _optional_cents_to_decimal(
                row["fixed_card_processing_fee_cents"]
            ),
            _optional_basis_points_to_decimal(
                row["organizer_commission_basis_points"]
            ),
        ),
        employee_labor=tuple(
            EmployeeLaborEntry(
                _cents_to_decimal(item["hourly_rate_cents"]),
                _minutes_to_hours(item["total_paid_minutes"]),
            )
            for item in labor_rows
        ),
        owner_labor_pay=_optional_cents_to_decimal(
            row["owner_labor_pay_cents"]
        ),
        travel_cost=_optional_cents_to_decimal(row["travel_cost_cents"]),
        additional_costs=tuple(
            AdditionalEventCost(
                item["cost_name"],
                _cents_to_decimal(item["amount_cents"]),
            )
            for item in cost_rows
        ),
        profit_target=ProfitTarget(
            row["profit_target_type"],
            _optional_cents_to_decimal(
                row["minimum_profit_amount_cents"]
            ),
            _optional_basis_points_to_decimal(
                row["minimum_profit_margin_basis_points"]
            ),
        ),
    )
    return row["event_id"], identity, scenario


def _insert_event_scenario(
    database: sqlite3.Connection,
    event_id: int,
    scenario: EventScenario,
) -> int:
    columns, placeholders, values = _scenario_insert_values(scenario)
    cursor = database.execute(
        f"""
        INSERT INTO event_scenarios (event_id, {columns})
        VALUES (?, {placeholders})
        """,
        (event_id, *values),
    )
    scenario_id = cursor.lastrowid
    _insert_scenario_children(database, scenario_id, scenario)
    return scenario_id


def _scenario_insert_values(
    scenario: EventScenario,
) -> tuple[str, str, tuple]:
    names, values = _scenario_column_values(scenario)
    return ", ".join(names), ", ".join("?" for _ in names), values


def _scenario_assignments(
    scenario: EventScenario,
) -> tuple[str, tuple]:
    names, values = _scenario_column_values(scenario)
    return ", ".join(f"{name} = ?" for name in names), values


def _scenario_column_values(
    scenario: EventScenario,
) -> tuple[tuple[str, ...], tuple]:
    revenue_is_manual = scenario.revenue.method == "manual_sales"
    names = (
        "scenario_name", "notes", "estimated_attendance",
        "other_competing_food_vendors",
        "expected_food_buyer_basis_points", "event_protection",
        "weather_outlook", "custom_weather_reduction_basis_points",
        "revenue_method", "average_order_sale_amount_cents",
        "expected_sales_amount_cents",
        "manual_average_order_sale_amount_cents", "food_cost_method",
        "average_food_cost_per_order_cents",
        "food_cost_percentage_basis_points",
        "manual_food_cost_total_cents", "card_sales_basis_points",
        "card_processing_basis_points",
        "fixed_card_processing_fee_cents",
        "vendor_or_booking_fee_cents",
        "organizer_commission_basis_points", "owner_labor_pay_cents",
        "travel_cost_cents", "profit_target_type",
        "minimum_profit_amount_cents",
        "minimum_profit_margin_basis_points",
    )
    values = (
        scenario.scenario_name.strip(),
        scenario.notes,
        scenario.demand.estimated_attendance,
        scenario.demand.other_competing_food_vendors,
        _decimal_to_basis_points(
            scenario.demand.expected_food_buyer_percentage
        ),
        scenario.weather.event_protection,
        scenario.weather.weather_outlook,
        _optional_decimal_to_basis_points(
            scenario.weather.custom_weather_reduction
        ),
        scenario.revenue.method,
        (
            None
            if revenue_is_manual
            else _decimal_to_cents(
                scenario.revenue.average_order_sale_amount
            )
        ),
        _optional_decimal_to_cents(
            scenario.revenue.expected_sales_amount
        ),
        (
            _decimal_to_cents(
                scenario.revenue.average_order_sale_amount
            )
            if revenue_is_manual
            else None
        ),
        scenario.food_cost.method,
        _optional_decimal_to_cents(
            scenario.food_cost.average_cost_per_order
        ),
        _optional_decimal_to_basis_points(
            scenario.food_cost.sales_percentage
        ),
        _optional_decimal_to_cents(
            scenario.food_cost.manual_event_total
        ),
        _decimal_to_basis_points(scenario.fees.card_sales_percentage),
        _decimal_to_basis_points(
            scenario.fees.card_processing_percentage
        ),
        _optional_decimal_to_cents(
            scenario.fees.fixed_card_processing_fee
        ),
        _decimal_to_cents(scenario.fees.vendor_or_booking_fee),
        _optional_decimal_to_basis_points(
            scenario.fees.organizer_commission_percentage
        ),
        _optional_decimal_to_cents(scenario.owner_labor_pay),
        _optional_decimal_to_cents(scenario.travel_cost),
        scenario.profit_target.target_type,
        _optional_decimal_to_cents(
            scenario.profit_target.minimum_profit_amount
        ),
        _optional_decimal_to_basis_points(
            scenario.profit_target.minimum_profit_margin
        ),
    )
    return names, values


def _insert_scenario_children(
    database: sqlite3.Connection,
    scenario_id: int,
    scenario: EventScenario,
) -> None:
    database.executemany(
        """
        INSERT INTO event_scenario_employee_labor_entries (
            event_scenario_id, position, hourly_rate_cents,
            total_paid_minutes
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                scenario_id,
                position,
                _decimal_to_cents(entry.hourly_rate),
                _hours_to_minutes(entry.total_hours_paid),
            )
            for position, entry in enumerate(scenario.employee_labor)
        ],
    )
    database.executemany(
        """
        INSERT INTO event_scenario_additional_costs (
            event_scenario_id, position, cost_name, amount_cents
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                scenario_id,
                position,
                cost.name,
                _decimal_to_cents(cost.amount),
            )
            for position, cost in enumerate(scenario.additional_costs)
        ],
    )


def _scenario_name_exists(
    database: sqlite3.Connection,
    event_id: int,
    name: str,
) -> bool:
    return database.execute(
        """
        SELECT 1 FROM event_scenarios
        WHERE event_id = ? AND lower(trim(scenario_name)) = lower(?)
        """,
        (event_id, name.strip()),
    ).fetchone() is not None


def _minutes_to_clock(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def _upgrade_food_cost_schema(
    database: sqlite3.Connection,
    columns: set[str],
) -> None:
    """Preserve legacy percentage defaults in the new method-based shape."""
    defaults_row = database.execute(
        "SELECT * FROM business_defaults WHERE id = 1"
    ).fetchone()
    labor_table_exists = database.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type = 'table'
          AND name = 'business_default_labor_entries'
        """
    ).fetchone()
    labor_rows = []
    if labor_table_exists:
        labor_rows = database.execute(
            """
            SELECT position, hourly_rate_cents, total_paid_minutes
            FROM business_default_labor_entries ORDER BY position
            """
        ).fetchall()
        database.execute("DROP TABLE business_default_labor_entries")

    database.execute(
    """
    ALTER TABLE business_defaults
    RENAME TO prior_defaults_food_cost
    """
    )
    apply_business_defaults_schema(database)
    if defaults_row is not None:
        target_type = (
            defaults_row["profit_target_type"]
            if "profit_target_type" in columns
            else _legacy_target_type(defaults_row)
        )
        database.execute(
            """
            INSERT INTO business_defaults (
                id, business_name, average_order_sale_amount_cents,
                food_cost_method, food_cost_percentage_basis_points,
                card_sales_basis_points, card_processing_basis_points,
                default_travel_cost_cents,
                default_owner_labor_pay_cents,
                profit_target_type, minimum_profit_amount_cents,
                minimum_profit_margin_basis_points, created_at, updated_at
            )
            VALUES (
                1, ?, ?, 'sales_percentage', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                defaults_row["business_name"],
                _legacy_column(
                    defaults_row,
                    "average_order_sale_amount_cents",
                    "average_order_value_cents",
                ),
                defaults_row["food_cost_basis_points"],
                defaults_row["card_sales_basis_points"],
                defaults_row["card_processing_basis_points"],
                _legacy_column(
                    defaults_row, "default_travel_cost_cents"
                ),
                _legacy_column(
                    defaults_row, "default_owner_labor_pay_cents"
                ),
                target_type,
                (
                    _legacy_column(
                        defaults_row,
                        "minimum_profit_amount_cents",
                        "minimum_acceptable_profit_cents",
                    )
                    if target_type == "profit_amount"
                    else None
                ),
                (
                    _legacy_column(
                        defaults_row,
                        "minimum_profit_margin_basis_points",
                        "minimum_acceptable_margin_basis_points",
                    )
                    if target_type == "profit_margin"
                    else None
                ),
                _legacy_column(defaults_row, "created_at"),
                _legacy_column(defaults_row, "updated_at"),
            ),
        )
        if labor_rows:
            database.executemany(
                """
                INSERT INTO business_default_labor_entries (
                    business_defaults_id, position, hourly_rate_cents,
                    total_paid_minutes
                )
                VALUES (1, ?, ?, ?)
                """,
                [tuple(row) for row in labor_rows],
            )
    database.execute("DROP TABLE prior_defaults_food_cost")
    database.commit()


def _legacy_column(
    row: sqlite3.Row,
    *names: str,
) -> object | None:
    for name in names:
        if name in row.keys():
            return row[name]
    return None


def _upgrade_legacy_business_defaults(
    database: sqlite3.Connection,
) -> None:
    """Upgrade the earlier uncommitted single-labor schema."""
    legacy_row = database.execute(
        "SELECT * FROM business_defaults WHERE id = 1"
    ).fetchone()
    database.execute("ALTER TABLE business_defaults RENAME TO legacy_defaults")
    apply_business_defaults_schema(database)
    if legacy_row is not None:
        database.execute(
            """
            INSERT INTO business_defaults (
                id, business_name, average_order_sale_amount_cents,
                food_cost_basis_points, card_sales_basis_points,
                card_processing_basis_points,
                profit_target_type, minimum_profit_amount_cents,
                minimum_profit_margin_basis_points
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                legacy_row["business_name"],
                legacy_row["average_order_value_cents"],
                legacy_row["food_cost_basis_points"],
                legacy_row["card_sales_basis_points"],
                legacy_row["card_processing_basis_points"],
                _legacy_target_type(legacy_row),
                legacy_row["minimum_acceptable_profit_cents"]
                if _legacy_target_type(legacy_row) == "profit_amount"
                else None,
                legacy_row["minimum_acceptable_margin_basis_points"]
                if _legacy_target_type(legacy_row) == "profit_margin"
                else None,
            ),
        )
    database.execute("DROP TABLE legacy_defaults")
    database.commit()


def _upgrade_profit_target_schema(database: sqlite3.Connection) -> None:
    """Add the required-choice shape while retaining prior saved defaults."""
    defaults_row = database.execute(
        "SELECT * FROM business_defaults WHERE id = 1"
    ).fetchone()
    labor_rows = database.execute(
        """
        SELECT position, hourly_rate_cents, total_paid_minutes
        FROM business_default_labor_entries ORDER BY position
        """
    ).fetchall()
    database.execute("DROP TABLE business_default_labor_entries")
    database.execute("ALTER TABLE business_defaults RENAME TO prior_defaults")
    apply_business_defaults_schema(database)
    if defaults_row is not None:
        target_type = _legacy_target_type(defaults_row)
        database.execute(
            """
            INSERT INTO business_defaults (
                id, business_name, average_order_sale_amount_cents,
                food_cost_basis_points, card_sales_basis_points,
                card_processing_basis_points, default_travel_cost_cents,
                profit_target_type, minimum_profit_amount_cents,
                minimum_profit_margin_basis_points, created_at, updated_at
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                defaults_row["business_name"],
                defaults_row["average_order_sale_amount_cents"],
                defaults_row["food_cost_basis_points"],
                defaults_row["card_sales_basis_points"],
                defaults_row["card_processing_basis_points"],
                defaults_row["default_travel_cost_cents"],
                target_type,
                defaults_row["minimum_acceptable_profit_cents"]
                if target_type == "profit_amount" else None,
                defaults_row["minimum_acceptable_margin_basis_points"]
                if target_type == "profit_margin" else None,
                defaults_row["created_at"],
                defaults_row["updated_at"],
            ),
        )
        database.executemany(
            """
            INSERT INTO business_default_labor_entries (
                business_defaults_id, position, hourly_rate_cents,
                total_paid_minutes
            )
            VALUES (1, ?, ?, ?)
            """,
            [tuple(row) for row in labor_rows],
        )
    database.execute("DROP TABLE prior_defaults")
    database.commit()


def _legacy_target_type(row: sqlite3.Row) -> str | None:
    if row["minimum_acceptable_profit_cents"] is not None:
        return "profit_amount"
    if row["minimum_acceptable_margin_basis_points"] is not None:
        return "profit_margin"
    return None


def _cents_to_decimal(value: int) -> Decimal:
    return Decimal(value) / Decimal("100")


def _basis_points_to_decimal(value: int) -> Decimal:
    return Decimal(value) / Decimal("10000")


def _minutes_to_hours(value: int) -> Decimal:
    return Decimal(value) / Decimal("60")


def _decimal_to_cents(value: Decimal) -> int:
    return int(value * 100)


def _decimal_to_basis_points(value: Decimal) -> int:
    return int(value * 10000)


def _hours_to_minutes(value: Decimal) -> int:
    return int(value * 60)


def _optional_cents_to_decimal(value: int | None) -> Decimal | None:
    return None if value is None else _cents_to_decimal(value)


def _optional_basis_points_to_decimal(value: int | None) -> Decimal | None:
    return None if value is None else _basis_points_to_decimal(value)


def _optional_decimal_to_cents(value: Decimal | None) -> int | None:
    return None if value is None else _decimal_to_cents(value)


def _optional_decimal_to_basis_points(value: Decimal | None) -> int | None:
    return None if value is None else _decimal_to_basis_points(value)
