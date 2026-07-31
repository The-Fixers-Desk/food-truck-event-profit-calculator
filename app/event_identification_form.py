from datetime import date, time

from werkzeug.datastructures import MultiDict

from app.models import EventIdentity


FIELD_NAMES = ("event_name", "event_date", "start_time", "location")


def blank_event_identification_form() -> dict[str, str]:
    return {name: "" for name in FIELD_NAMES}


def validate_event_identification(
    submitted: MultiDict,
) -> tuple[EventIdentity | None, dict[str, str], dict[str, str]]:
    """Validate the event identity portion of the Event Inputs form."""
    values = {
        name: submitted.get(name, "").strip()
        for name in FIELD_NAMES
    }
    errors: dict[str, str] = {}

    for name, label in (
        ("event_name", "Event name"),
        ("event_date", "Event date"),
        ("start_time", "Start time"),
        ("location", "Location"),
    ):
        if not values[name]:
            errors[name] = f"{label} is required."

    event_date = _parse_date(values["event_date"], errors)
    start_time = _parse_time(values["start_time"], errors)

    if errors:
        return None, values, errors

    identity = EventIdentity(
        event_name=values["event_name"],
        event_date=event_date,
        start_time=start_time,
        location=values["location"],
    )
    return identity, values, errors


def _parse_date(
    value: str,
    errors: dict[str, str],
) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors["event_date"] = "Enter a valid event date."
        return None


def _parse_time(
    value: str,
    errors: dict[str, str],
) -> time | None:
    if not value:
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        errors["start_time"] = "Enter a valid start time."
        return None
