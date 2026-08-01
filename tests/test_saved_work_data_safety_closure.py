import sqlite3

from tests.test_complete_event_inputs_workflow import (
    complete_event_inputs,
    saved_defaults_data,
)


def test_saved_event_library_has_approved_summary_filters_and_actions(
    client,
):
    client.post("/events/new", data=complete_event_inputs())

    page = client.get("/saved-events").data.decode()

    assert "Event library" in page
    assert "Your saved events" in page
    assert "All events" in page
    assert "Worth it" in page
    assert "Borderline" in page
    assert "Not worth it" in page
    assert "Saved events" in page
    assert "Total scenarios" in page
    assert "Recently updated" in page
    assert "Recommendation" in page
    assert "Open" in page
    assert "Manage" in page


def test_saved_event_search_filter_sort_and_no_results_use_query_state(client):
    first = complete_event_inputs()
    first["event_name"] = "Alpha Market"
    first["location"] = "North lot"
    client.post("/events/new", data=first)
    second = complete_event_inputs()
    second["event_name"] = "Zulu Fair"
    second["location"] = "South lot"
    client.post("/events/new", data=second)

    searched = client.get("/saved-events?q=Alpha&sort=name").data.decode()
    assert "Alpha Market" in searched
    assert "Zulu Fair" not in searched
    assert 'value="Alpha"' in searched
    assert 'value="name" selected' in searched

    empty = client.get("/saved-events?q=missing&status=worth-it").data.decode()
    assert "No events match these filters" in empty
    assert "Clear filters" in empty


def test_data_safety_summary_privacy_actions_and_sample_format(client):
    client.post("/defaults", data=saved_defaults_data())
    client.post("/events/new", data=complete_event_inputs())

    page = client.get("/data-safety").data.decode()
    assert "Your data stays on this device" in page
    for label in (
        "Stored locally",
        "No cloud sync",
        "No account required",
        "Works offline",
        "Export all data",
        "Import backup",
        "Download sample format",
        "Delete all saved events",
        "Reset business defaults",
        "Clear app data",
    ):
        assert label in page

    sample = client.get("/data-safety/sample-format")
    assert sample.status_code == 200
    assert sample.mimetype == "application/json"
    assert b"manifest.json" in sample.data
    assert b"database.sqlite" in sample.data


def test_successful_export_updates_persistent_last_export_status(
    client, restart_application, app
):
    before = client.get("/data-safety").data.decode()
    assert "Not exported yet" in before

    exported = client.post("/data-safety/backup")
    assert exported.status_code == 200
    assert "Not exported yet" not in client.get("/data-safety").data.decode()

    restarted = restart_application(app)
    assert "Not exported yet" not in restarted.test_client().get(
        "/data-safety"
    ).data.decode()


def test_scoped_destructive_actions_require_confirmation_and_preserve_other_data(
    client, database_path
):
    client.post("/defaults", data=saved_defaults_data())
    client.post("/events/new", data=complete_event_inputs())

    client.post("/data-safety/delete-events", data={})
    with sqlite3.connect(database_path) as database:
        assert database.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1

    client.post(
        "/data-safety/delete-events",
        data={"confirmation": "delete-events"},
    )
    with sqlite3.connect(database_path) as database:
        assert database.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
        assert database.execute("SELECT COUNT(*) FROM business_defaults").fetchone()[0] == 1

    client.post("/events/new", data=complete_event_inputs())
    client.post(
        "/data-safety/reset-defaults",
        data={"confirmation": "reset-defaults"},
    )
    with sqlite3.connect(database_path) as database:
        assert database.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1
        assert database.execute("SELECT COUNT(*) FROM business_defaults").fetchone()[0] == 0


def test_clear_everything_requires_phrase_and_removes_all_customer_data(
    client, database_path
):
    client.post("/defaults", data=saved_defaults_data())
    client.post("/events/new", data=complete_event_inputs())

    client.post("/data-safety/clear", data={"confirmation_phrase": "wrong"})
    with sqlite3.connect(database_path) as database:
        assert database.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1

    response = client.post(
        "/data-safety/clear",
        data={"confirmation_phrase": "CLEAR ALL DATA"},
    )
    assert response.headers["Location"].endswith("/welcome")
    with sqlite3.connect(database_path) as database:
        assert database.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
        assert database.execute("SELECT COUNT(*) FROM event_scenarios").fetchone()[0] == 0
        assert database.execute("SELECT COUNT(*) FROM business_defaults").fetchone()[0] == 0


def test_reusable_system_states_have_a_deterministic_review_route(client):
    page = client.get("/system-states")
    assert page.status_code == 200
    assert b"System page patterns" in page.data
    assert b"Calculating your estimate" in page.data
    assert b"We couldn&#39;t load this event" in page.data
