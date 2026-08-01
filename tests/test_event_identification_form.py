import sqlite3

import pytest


def valid_event_identification() -> dict[str, str]:
    return {
        "event_name": "Summer Festival",
        "event_date": "2026-08-15",
        "start_time": "11:00",
        "location": "Town Square",
    }


def saved_event_counts(database_path) -> tuple[int, int]:
    with sqlite3.connect(database_path) as database:
        event_count = database.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]
        scenario_count = database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0]
    return event_count, scenario_count


def test_event_inputs_page_opens(client):
    response = client.get("/events/new")

    assert response.status_code == 200
    assert b"<h1>Enter the details for this event</h1>" in response.data
    assert b"Event basics" in response.data


@pytest.mark.parametrize(
    ("field_name", "input_type"),
    (
        ("event_name", "text"),
        ("event_date", "date"),
        ("start_time", "time"),
        ("location", "text"),
    ),
)
def test_event_identification_fields_are_present_and_required(
    client, field_name, input_type
):
    response = client.get("/events/new")

    assert f'name="{field_name}"'.encode() in response.data
    assert f'type="{input_type}"'.encode() in response.data
    assert b"required" in response.data


@pytest.mark.parametrize(
    ("field_name", "expected_error"),
    (
        ("event_name", b"Event name is required."),
        ("event_date", b"Event date is required."),
        ("start_time", b"Start time is required."),
        ("location", b"Location is required."),
    ),
)
def test_required_event_identification_fields_are_validated(
    client, field_name, expected_error
):
    form_data = valid_event_identification()
    form_data[field_name] = ""

    response = client.post("/events/new", data=form_data)

    assert response.status_code == 200
    assert expected_error in response.data
    assert f'id="{field_name}-error"'.encode() in response.data


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "expected_error"),
    (
        ("event_date", "not-a-date", b"Enter a valid event date."),
        ("start_time", "not-a-time", b"Enter a valid start time."),
    ),
)
def test_invalid_values_are_preserved(
    client, field_name, invalid_value, expected_error
):
    form_data = valid_event_identification()
    form_data[field_name] = invalid_value

    response = client.post("/events/new", data=form_data)

    assert expected_error in response.data
    assert f'value="{invalid_value}"'.encode() in response.data
    assert b'value="Summer Festival"' in response.data
    assert b'value="Town Square"' in response.data


@pytest.mark.parametrize("valid_submission", (False, True))
def test_event_identification_does_not_create_records(
    client, database_path, valid_submission
):
    form_data = valid_event_identification()
    if not valid_submission:
        form_data["event_name"] = ""

    client.post("/events/new", data=form_data)

    assert saved_event_counts(database_path) == (0, 0)


def test_navigation_reaches_event_inputs(client):
    response = client.get("/defaults")

    assert b'href="/"' in response.data
    assert b'href="/events/new"' in response.data
    assert b"New analysis" in response.data
