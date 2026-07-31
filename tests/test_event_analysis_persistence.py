import sqlite3

import pytest

import app.database as database_module
from app.calculations import calculate_event_scenario
from app.database import load_event_scenario
from app.event_inputs_form import calculation_result_data
from tests.test_complete_event_inputs_workflow import complete_event_inputs


def saved_ids(database_path):
    with sqlite3.connect(database_path) as database:
        event_id = database.execute(
            "SELECT id FROM events ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        scenario_id = database.execute(
            "SELECT id FROM event_scenarios ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
    return event_id, scenario_id


def test_valid_submission_persists_complete_original_estimate(
    client, database_path
):
    response = client.post("/events/new", data=complete_event_inputs())

    assert b"Event Analysis" in response.data
    with sqlite3.connect(database_path) as database:
        event = database.execute("SELECT * FROM events").fetchone()
        scenario = database.execute(
            "SELECT * FROM event_scenarios"
        ).fetchone()
        labor = database.execute(
            """
            SELECT position, hourly_rate_cents, total_paid_minutes
            FROM event_scenario_employee_labor_entries ORDER BY position
            """
        ).fetchall()
        costs = database.execute(
            """
            SELECT position, cost_name, amount_cents
            FROM event_scenario_additional_costs ORDER BY position
            """
        ).fetchall()

    assert event[1:5] == (
        "Summer Festival",
        "2026-08-15",
        660,
        "Town Square",
    )
    assert scenario[2] == "Original estimate"
    assert scenario[4:7] == (1000, 5, 1000)
    assert scenario[10] == "attendance"
    assert scenario[11] == 1650
    assert scenario[12] is None
    assert labor == [(0, 2000, 600), (1, 2500, 240)]
    assert costs[:2] == [(0, "Ice", 4000), (1, "Extra propane", 6000)]
    assert [row[1] for row in costs[2:]] == [
        "__parking_cost__",
        "__permit_cost__",
        "__generator_utility_cost__",
    ]


def test_initial_save_rolls_back_if_a_child_write_fails(
    client, database_path, monkeypatch, caplog
):
    def fail_children(*args):
        raise sqlite3.IntegrityError("child failure")

    monkeypatch.setattr(
        database_module, "_insert_scenario_children", fail_children
    )

    response = client.post("/events/new", data=complete_event_inputs())

    assert b"Event Inputs" in response.data
    assert b"The event could not be saved." in response.data
    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0] == 0
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0] == 0
    records = [
        record
        for record in caplog.records
        if "Event and initial Scenario persistence failed."
        in record.getMessage()
    ]
    assert len(records) == 1
    assert records[0].exc_info[0] is sqlite3.IntegrityError
    logged = caplog.text
    assert "Summer Festival" not in logged
    assert "Town Square" not in logged


def test_separate_valid_submissions_create_separate_events(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    client.post("/events/new", data=complete_event_inputs())

    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0] == 2
        assert database.execute(
            """
            SELECT COUNT(*) FROM event_scenarios
            WHERE scenario_name = 'Original estimate'
            """
        ).fetchone()[0] == 2


def test_calculated_results_are_not_persisted(client, database_path):
    client.post("/events/new", data=complete_event_inputs())

    with sqlite3.connect(database_path) as database:
        columns = {
            row[1]
            for row in database.execute(
                "PRAGMA table_info(event_scenarios)"
            )
        }

    assert "business_profit_cents" not in columns
    assert "total_event_cost_cents" not in columns
    assert "break_even_sales_cents" not in columns


def test_persisted_assumptions_reproduce_workspace_calculation(
    client, app, database_path
):
    response = client.post("/events/new", data=complete_event_inputs())
    _, scenario_id = saved_ids(database_path)

    with app.app_context():
        _, _, scenario = load_event_scenario(scenario_id)
        result = calculate_event_scenario(scenario)
        display = calculation_result_data(result)

    assert f"${display['business_profit']}".encode() in response.data
    assert f"${display['total_event_cost']}".encode() in response.data


def test_save_as_new_requires_unique_trimmed_name(client, database_path):
    client.post("/events/new", data=complete_event_inputs())
    event_id, scenario_id = saved_ids(database_path)
    form_data = complete_event_inputs()
    form_data.update(
        {
            "active_event_id": str(event_id),
            "active_scenario_id": str(scenario_id),
            "save_mode": "new",
            "scenario_name": "   ",
        }
    )

    blank = client.post("/event-analysis/save", data=form_data).get_json()
    form_data["scenario_name"] = " original ESTIMATE "
    duplicate = client.post(
        "/event-analysis/save", data=form_data
    ).get_json()

    assert blank["saved"] is False
    assert blank["scenario_name_error"] == "Scenario name is required."
    assert duplicate["saved"] is False
    assert "already exists" in duplicate["scenario_name_error"]
    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0] == 1


def test_save_as_new_creates_sibling_and_makes_it_active(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    event_id, original_id = saved_ids(database_path)
    form_data = complete_event_inputs()
    form_data.update(
        {
            "travel_cost": "95",
            "active_event_id": str(event_id),
            "active_scenario_id": str(original_id),
            "save_mode": "new",
            "scenario_name": "  Rain plan  ",
        }
    )

    payload = client.post(
        "/event-analysis/save", data=form_data
    ).get_json()

    assert payload["saved"] is True
    assert payload["active_scenario_name"] == "Rain plan"
    assert payload["active_scenario_id"] != original_id
    with sqlite3.connect(database_path) as database:
        rows = database.execute(
            """
            SELECT id, scenario_name, travel_cost_cents
            FROM event_scenarios ORDER BY id
            """
        ).fetchall()
    assert rows == [
        (original_id, "Original estimate", 8000),
        (payload["active_scenario_id"], "Rain plan", 9500),
    ]


def test_same_scenario_name_is_allowed_for_different_events(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    first_event, first_scenario = saved_ids(database_path)
    client.post("/events/new", data=complete_event_inputs())
    second_event, second_scenario = saved_ids(database_path)
    form_data = complete_event_inputs()
    form_data.update(
        {
            "active_event_id": str(second_event),
            "active_scenario_id": str(second_scenario),
            "save_mode": "new",
            "scenario_name": "Shared name",
        }
    )
    assert client.post(
        "/event-analysis/save", data=form_data
    ).get_json()["saved"]
    form_data.update(
        {
            "active_event_id": str(first_event),
            "active_scenario_id": str(first_scenario),
        }
    )

    assert client.post(
        "/event-analysis/save", data=form_data
    ).get_json()["saved"]


def test_overwrite_requires_confirmation_and_preserves_identity(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    event_id, scenario_id = saved_ids(database_path)
    with sqlite3.connect(database_path) as database:
        database.execute(
            """
            UPDATE event_scenarios
            SET updated_at = '2000-01-01 00:00:00'
            WHERE id = ?
            """,
            (scenario_id,),
        )
        database.commit()
    form_data = complete_event_inputs()
    form_data.update(
        {
            "travel_cost": "125",
            "active_event_id": str(event_id),
            "active_scenario_id": str(scenario_id),
            "save_mode": "overwrite",
            "overwrite_confirmed": "false",
        }
    )

    rejected = client.post(
        "/event-analysis/save", data=form_data
    ).get_json()
    form_data["overwrite_confirmed"] = "true"
    saved = client.post(
        "/event-analysis/save", data=form_data
    ).get_json()

    assert rejected["saved"] is False
    assert "Confirm" in rejected["overwrite_error"]
    assert saved["saved"] is True
    assert saved["active_scenario_id"] == scenario_id
    assert saved["active_scenario_name"] == "Original estimate"
    with sqlite3.connect(database_path) as database:
        row = database.execute(
            """
            SELECT event_id, scenario_name, travel_cost_cents, updated_at
            FROM event_scenarios WHERE id = ?
            """,
            (scenario_id,),
        ).fetchone()
        count = database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0]
    assert row[:3] == (event_id, "Original estimate", 12500)
    assert row[3] != "2000-01-01 00:00:00"
    assert count == 1


def test_overwrite_replaces_ordered_children_transactionally(
    client, database_path, monkeypatch
):
    client.post("/events/new", data=complete_event_inputs())
    event_id, scenario_id = saved_ids(database_path)
    form_data = complete_event_inputs()
    form_data.update(
        {
            "employee_labor_rate": ["40"],
            "employee_labor_hours": ["3"],
            "additional_cost_name": ["Security"],
            "additional_cost_amount": ["75"],
            "active_event_id": str(event_id),
            "active_scenario_id": str(scenario_id),
            "save_mode": "overwrite",
            "overwrite_confirmed": "true",
        }
    )
    assert client.post(
        "/event-analysis/save", data=form_data
    ).get_json()["saved"]

    with sqlite3.connect(database_path) as database:
        labor = database.execute(
            """
            SELECT position, hourly_rate_cents, total_paid_minutes
            FROM event_scenario_employee_labor_entries
            WHERE event_scenario_id = ?
            """,
            (scenario_id,),
        ).fetchall()
        costs_before_failure = database.execute(
            """
            SELECT position, cost_name, amount_cents
            FROM event_scenario_additional_costs
            WHERE event_scenario_id = ? ORDER BY position
            """,
            (scenario_id,),
        ).fetchall()
    assert labor == [(0, 4000, 180)]
    assert costs_before_failure[0] == (0, "Security", 7500)

    def fail_children(*args):
        raise sqlite3.IntegrityError("child failure")

    monkeypatch.setattr(
        database_module, "_insert_scenario_children", fail_children
    )
    form_data["employee_labor_rate"] = ["50"]
    failed = client.post(
        "/event-analysis/save", data=form_data
    ).get_json()
    assert failed["saved"] is False
    with sqlite3.connect(database_path) as database:
        labor_after_failure = database.execute(
            """
            SELECT position, hourly_rate_cents, total_paid_minutes
            FROM event_scenario_employee_labor_entries
            WHERE event_scenario_id = ?
            """,
            (scenario_id,),
        ).fetchall()
    assert labor_after_failure == labor
