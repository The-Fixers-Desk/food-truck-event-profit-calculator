import sqlite3

import pytest

import app.database as database_module
from app import create_app
from tests.test_complete_event_inputs_workflow import (
    complete_event_inputs,
    saved_defaults_data,
)


def latest_ids(database_path):
    with sqlite3.connect(database_path) as database:
        return database.execute(
            """
            SELECT event_id, id FROM event_scenarios
            ORDER BY id DESC LIMIT 1
            """
        ).fetchone()


def save_sibling(client, database_path, name, **changes):
    event_id, scenario_id = latest_ids(database_path)
    form_data = complete_event_inputs()
    form_data.update(changes)
    form_data.update(
        {
            "active_event_id": str(event_id),
            "active_scenario_id": str(scenario_id),
            "save_mode": "new",
            "scenario_name": name,
        }
    )
    payload = client.post(
        "/event-analysis/save", data=form_data
    ).get_json()
    assert payload["saved"] is True
    return event_id, payload["active_scenario_id"]


def test_saved_events_empty_state_and_navigation(client):
    page = client.get("/saved-events").data.decode()

    assert "No saved events yet" in page
    assert "Start an event analysis" in page
    assert "Saved events" in client.get("/events/new").data.decode()


def test_events_are_grouped_with_identity_and_scenarios(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    save_sibling(client, database_path, "Rain plan")

    page = client.get("/saved-events").data.decode()

    assert "Summer Festival" in page
    assert "2026-08-15 at 11:00" in page
    assert "Town Square" in page
    assert "2 saved Scenarios" in page
    assert "Original estimate" in page
    assert "Rain plan" in page
    assert page.count("Open analysis") == 2


def test_event_and_scenario_ordering_is_modified_first_and_deterministic(
    client, database_path
):
    first = complete_event_inputs()
    first["event_name"] = "Older Event"
    client.post("/events/new", data=first)
    first_event, _ = latest_ids(database_path)
    save_sibling(client, database_path, "Older sibling")
    second = complete_event_inputs()
    second["event_name"] = "Newer Event"
    client.post("/events/new", data=second)
    second_event, _ = latest_ids(database_path)
    with sqlite3.connect(database_path) as database:
        database.execute(
            "UPDATE events SET updated_at = '2026-01-01 00:00:00' "
            "WHERE id = ?",
            (first_event,),
        )
        database.execute(
            "UPDATE event_scenarios SET updated_at = "
            "'2026-01-01 00:00:00' WHERE event_id = ?",
            (first_event,),
        )
        database.execute(
            "UPDATE events SET updated_at = '2026-02-01 00:00:00' "
            "WHERE id = ?",
            (second_event,),
        )
        database.execute(
            "UPDATE event_scenarios SET updated_at = "
            "'2026-02-01 00:00:00' WHERE event_id = ?",
            (second_event,),
        )
        database.commit()

    page = client.get("/saved-events").data.decode()

    assert page.index("Newer Event") < page.index("Older Event")
    older_event_section = page.split(
        f'data-event-id="{first_event}"', 1
    )[1]
    assert older_event_section.index("Older sibling") < (
        older_event_section.index("Original estimate")
    )


def test_opening_each_saved_scenario_reuses_clean_workspace_without_duplicates(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    event_id, second_id = save_sibling(
        client,
        database_path,
        "Owner only",
        employee_labor_rate=[],
        employee_labor_hours=[],
        additional_cost_name=["Security"],
        additional_cost_amount=["90"],
    )
    with sqlite3.connect(database_path) as database:
        scenario_ids = [
            row[0]
            for row in database.execute(
                "SELECT id FROM event_scenarios ORDER BY id"
            )
        ]

    for scenario_id in scenario_ids:
        response = client.get(
            f"/events/{event_id}/scenarios/{scenario_id}"
        )
        assert response.status_code == 200
        assert b'data-workspace="true"' in response.data
        assert b'id="open-save-analysis"' in response.data
        assert b"disabled" in response.data.split(
            b'id="open-save-analysis"', 1
        )[1].split(b">", 1)[0]
    second_page = client.get(
        f"/events/{event_id}/scenarios/{second_id}"
    ).data
    assert b'value="Security"' in second_page
    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0] == 1
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0] == 2


@pytest.mark.parametrize(
    "path",
    (
        "/events/999/scenarios/999",
        "/events/999/scenarios/1",
    ),
)
def test_missing_saved_scenario_uses_not_found_page(client, path):
    response = client.get(path)

    assert response.status_code == 404
    assert b"Page Not Found" in response.data


def test_event_rename_validation_and_scope(client, database_path):
    client.post("/events/new", data=complete_event_inputs())
    event_id, scenario_id = latest_ids(database_path)

    invalid = client.post(
        f"/events/{event_id}/rename", data={"event_name": "   "}
    )
    assert b"Event name is required." in invalid.data
    assert b'value="   "' in invalid.data

    response = client.post(
        f"/events/{event_id}/rename",
        data={"event_name": "  Renamed Festival  "},
        follow_redirects=True,
    )
    assert b"Event name updated." in response.data
    with sqlite3.connect(database_path) as database:
        event = database.execute(
            """
            SELECT event_name, event_date, start_time_minutes, location
            FROM events WHERE id = ?
            """,
            (event_id,),
        ).fetchone()
        scenario = database.execute(
            "SELECT scenario_name FROM event_scenarios WHERE id = ?",
            (scenario_id,),
        ).fetchone()
    assert event == (
        "Renamed Festival",
        "2026-08-15",
        660,
        "Town Square",
    )
    assert scenario == ("Original estimate",)


def test_scenario_rename_validation_uniqueness_and_scope(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    event_id, second_id = save_sibling(
        client, database_path, "Rain plan"
    )
    with sqlite3.connect(database_path) as database:
        first_id = database.execute(
            "SELECT MIN(id) FROM event_scenarios WHERE event_id = ?",
            (event_id,),
        ).fetchone()[0]
        assumptions_before = database.execute(
            "SELECT estimated_attendance FROM event_scenarios WHERE id = ?",
            (second_id,),
        ).fetchone()

    blank = client.post(
        f"/events/{event_id}/scenarios/{second_id}/rename",
        data={"scenario_name": "  "},
    )
    assert b"Scenario name is required." in blank.data
    assert b'value="  "' in blank.data

    duplicate = client.post(
        f"/events/{event_id}/scenarios/{second_id}/rename",
        data={"scenario_name": " original ESTIMATE "},
    )
    assert b"already exists" in duplicate.data

    success = client.post(
        f"/events/{event_id}/scenarios/{second_id}/rename",
        data={"scenario_name": "  Wet weather  "},
        follow_redirects=True,
    )
    assert b"Scenario name updated." in success.data
    with sqlite3.connect(database_path) as database:
        rows = database.execute(
            """
            SELECT id, scenario_name FROM event_scenarios
            WHERE event_id = ? ORDER BY id
            """,
            (event_id,),
        ).fetchall()
        assumptions_after = database.execute(
            "SELECT estimated_attendance FROM event_scenarios WHERE id = ?",
            (second_id,),
        ).fetchone()
    assert rows == [
        (first_id, "Original estimate"),
        (second_id, "Wet weather"),
    ]
    assert assumptions_after == assumptions_before


def test_deleting_nonfinal_scenario_preserves_event_and_sibling(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    event_id, second_id = save_sibling(
        client, database_path, "Delete me"
    )

    response = client.post(
        f"/events/{event_id}/scenarios/{second_id}/delete",
        data={"confirmed": "yes"},
        follow_redirects=True,
    )

    assert b"Scenario deleted." in response.data
    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM events WHERE id = ?", (event_id,)
        ).fetchone()[0] == 1
        assert database.execute(
            "SELECT scenario_name FROM event_scenarios WHERE event_id = ?",
            (event_id,),
        ).fetchall() == [("Original estimate",)]
        assert database.execute(
            """
            SELECT COUNT(*) FROM event_scenario_employee_labor_entries
            WHERE event_scenario_id = ?
            """,
            (second_id,),
        ).fetchone()[0] == 0


def test_final_scenario_cannot_be_deleted_individually(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    event_id, scenario_id = latest_ids(database_path)

    response = client.post(
        f"/events/{event_id}/scenarios/{scenario_id}/delete",
        data={"confirmed": "yes"},
    )

    assert b"final scenario cannot be deleted individually" in response.data
    assert b"Delete the complete event instead" in response.data


def test_confirmed_event_delete_cascades_and_failure_rolls_back(
    client, database_path, monkeypatch
):
    client.post("/events/new", data=complete_event_inputs())
    event_id, _ = save_sibling(client, database_path, "Sibling")

    def fail_after_delete(database, target_event_id):
        database.execute(
            "DELETE FROM events WHERE id = ?", (target_event_id,)
        )
        raise sqlite3.IntegrityError("forced failure")

    monkeypatch.setattr(
        database_module, "_delete_event_row", fail_after_delete
    )
    failed = client.post(
        f"/events/{event_id}/delete", data={"confirmed": "yes"}
    )
    assert b"event could not be deleted" in failed.data
    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM events WHERE id = ?", (event_id,)
        ).fetchone()[0] == 1
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios WHERE event_id = ?",
            (event_id,),
        ).fetchone()[0] == 2

    monkeypatch.undo()
    deleted = client.post(
        f"/events/{event_id}/delete",
        data={"confirmed": "yes"},
        follow_redirects=True,
    )
    assert b"Event and its saved scenarios deleted." in deleted.data
    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM events WHERE id = ?", (event_id,)
        ).fetchone()[0] == 0
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios WHERE event_id = ?",
            (event_id,),
        ).fetchone()[0] == 0
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenario_additional_costs"
        ).fetchone()[0] == 0


def test_names_deletions_and_rows_persist_after_restart(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    event_id, deleted_id = save_sibling(
        client, database_path, "Delete before restart"
    )
    _, remaining_id = save_sibling(
        client,
        database_path,
        "Keep after restart",
        additional_cost_name=["Security", "Water"],
        additional_cost_amount=["90", "25"],
    )
    client.post(
        f"/events/{event_id}/rename",
        data={"event_name": "Restart Festival"},
    )
    client.post(
        f"/events/{event_id}/scenarios/{deleted_id}/delete",
        data={"confirmed": "yes"},
    )

    restarted = create_app(
        {
            "DATABASE": database_path,
            "ENFORCE_SETUP": False,
            "SECRET_KEY": "restart-test",
            "TESTING": True,
        }
    )
    restart_client = restarted.test_client()
    page = restart_client.get("/saved-events").data
    opened = restart_client.get(
        f"/events/{event_id}/scenarios/{remaining_id}"
    ).data

    assert b"Restart Festival" in page
    assert b"Keep after restart" in page
    assert b"Delete before restart" not in page
    assert opened.index(b'value="Security"') < opened.index(
        b'value="Water"'
    )


def test_management_preserves_business_defaults(client, database_path):
    client.post("/defaults", data=saved_defaults_data())
    with sqlite3.connect(database_path) as database:
        before = database.execute(
            "SELECT * FROM business_defaults"
        ).fetchone()
    client.post("/events/new", data=complete_event_inputs())
    event_id, scenario_id = latest_ids(database_path)
    client.post(
        f"/events/{event_id}/scenarios/{scenario_id}/rename",
        data={"scenario_name": "Renamed"},
    )
    client.post(
        f"/events/{event_id}/rename",
        data={"event_name": "Renamed Event"},
    )

    with sqlite3.connect(database_path) as database:
        after = database.execute(
            "SELECT * FROM business_defaults"
        ).fetchone()
    assert after == before


def test_dirty_workspace_navigation_uses_discard_confirmation(client):
    client.post("/events/new", data=complete_event_inputs())
    script = client.get("/static/js/event_inputs.js").data.decode()

    assert "Discard unsaved changes and leave this analysis?" in script
    assert 'workspaceForm.dataset.dirty === "true"' in script
    assert "event.preventDefault()" in script
    assert "discardNavigationApproved" in script
    assert "beforeunload" in script
