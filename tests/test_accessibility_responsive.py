import re

import pytest

from tests.test_complete_event_inputs_workflow import complete_event_inputs


@pytest.mark.parametrize(
    ("path", "title", "heading"),
    (
        ("/", "Welcome", "Welcome to your event profit calculator"),
        ("/defaults", "Defaults", "Set your business defaults once"),
        ("/events/new", "Event Inputs", "Enter the details for this event"),
        ("/saved-events", "Saved Events", "Saved events"),
        ("/data-safety", "Data Safety", "Back up or restore your data"),
    ),
)
def test_pages_have_skip_target_title_landmarks_and_one_h1(
    client, path, title, heading
):
    page = client.get(path).data.decode()

    assert '<a class="skip-link" href="#main-content">' in page
    assert 'id="main-content" tabindex="-1">' in page
    assert '<nav class="app-navigation" aria-label="Primary navigation">' in page
    assert f"<title>\n      {title}" in page
    assert page.count("<h1") == 1
    assert f"<h1>{heading}</h1>" in page


def test_current_navigation_destination_is_programmatically_identified(client):
    page = client.get("/events/new").data.decode()
    active = re.search(
        r'<a[^>]+nav-link--active[^>]+aria-current="page"[^>]*>', page
    )
    assert active is not None


def test_event_error_summary_is_focusable_and_input_is_preserved(client):
    form = complete_event_inputs()
    form["event_name"] = ""
    form["location"] = "Preserved location"

    page = client.post("/events/new", data=form).data.decode()

    assert 'id="event-error-summary" role="alert"' in page
    assert 'tabindex="-1"' in page
    assert "Correct the highlighted fields" in page
    assert 'aria-invalid="true"' in page
    assert 'value="Preserved location"' in page


def test_repeatable_controls_have_numbered_names_focus_and_announcements(client):
    event_script = client.get("/static/js/event_inputs.js").data.decode()
    defaults_script = client.get("/static/js/business_defaults.js").data.decode()

    for text in (
        "Remove employee labor entry ${index + 1}",
        "Additional cost ${index + 1} name",
        "Additional cost ${index + 1} amount",
        "Remove additional cost ${index + 1}",
        "nextFocus.focus()",
        'setAttribute("role", "status")',
    ):
        assert text in event_script
    assert "Remove default labor entry ${index + 1}" in defaults_script
    assert "nextFocus.focus()" in defaults_script


def test_save_dialog_has_name_description_and_focus_restoration(client):
    page = client.post("/events/new", data=complete_event_inputs()).data.decode()
    script = client.get("/static/js/event_inputs.js").data.decode()

    assert 'aria-labelledby="save-analysis-title"' in page
    assert 'aria-describedby="save-analysis-description"' in page
    assert 'id="save-analysis-description"' in page
    assert 'addEventListener("close", () => saveDialogTrigger.focus())' in script
    assert ".showModal()" in script


def test_workspace_live_status_and_invalid_announcement(client):
    page = client.post("/events/new", data=complete_event_inputs()).data.decode()
    invalid = complete_event_inputs()
    invalid["estimated_attendance"] = "bad"
    payload = client.post("/event-analysis/calculate", data=invalid).get_json()

    assert 'id="analysis-update-status"' in page
    assert 'aria-live="polite"' in page
    assert payload["status"] == (
        "Results have not updated. Correct the highlighted fields."
    )


def test_comparison_tables_have_named_focusable_overflow_regions(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    from tests.test_saved_events_management import latest_ids, save_sibling
    event_id, first_id = latest_ids(database_path)
    _, second_id = save_sibling(client, database_path, "Alternative")

    page = client.post(
        "/comparison",
        data={"scenario_id": [str(first_id), str(second_id)]},
    ).data.decode()

    assert page.count('role="region" tabindex="0"') == 2
    assert 'aria-label="Financial results comparison"' in page
    assert 'aria-label="Assumptions comparison"' in page
    assert page.count("<caption class=\"visually-hidden\">") == 2
    assert 'scope="row"' in page
    assert "Baseline:" in page
    assert "Show differences only" in page


def test_focus_contrast_and_narrow_layout_foundations(client):
    base = client.get("/static/css/base.css").data.decode()
    forms = client.get("/static/css/forms.css").data.decode()
    tokens = client.get("/static/css/tokens.css").data.decode()

    assert ".skip-link:focus" in base
    assert ":focus-visible" in base
    assert ".visually-hidden" in base
    assert "prefers-reduced-motion" in base
    assert "@media (max-width: 420px)" in forms
    assert "grid-template-columns: minmax(0, 1fr)" in forms
    assert "overflow-x: auto" in forms
    for token in ("--color-success", "--color-warning", "--color-danger"):
        assert token in tokens
