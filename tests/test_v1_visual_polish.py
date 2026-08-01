from tests.test_complete_event_inputs_workflow import (
    complete_event_inputs,
    saved_defaults_data,
)
from tests.test_saved_events_management import save_sibling


def test_scenario_save_has_specific_busy_and_recovery_states(client):
    page = client.post("/events/new", data=complete_event_inputs()).data.decode()
    script = client.get("/static/js/event_inputs.js").data.decode()

    assert ">Save as new scenario</button>" in page
    assert 'confirmSave.disabled = true' in script
    assert 'confirmSave.setAttribute("aria-busy", "true")' in script
    assert '"Saving…"' in script
    assert '"Overwriting…"' in script
    assert 'confirmSave.disabled = false' in script
    assert 'confirmSave.removeAttribute("aria-busy")' in script
    assert "finally" in script


def test_management_posts_prevent_duplicate_actions_with_specific_verbs(client):
    script = client.get("/static/js/saved_events.js").data.decode()

    assert 'compareButton.disabled = true' in script
    assert 'compareButton.textContent = "Comparing…"' in script
    assert 'document.querySelectorAll(".management-action form")' in script
    assert 'button.disabled = true' in script
    assert '"Deleting…" : "Renaming…"' in script
    assert 'aria-busy' in script


def test_backup_and_restore_have_standard_busy_feedback(client):
    page = client.get("/data-safety").data.decode()
    script = client.get("/static/js/data_safety.js").data.decode()

    assert 'id="download-backup-form"' in page
    assert 'id="restore-backup-form"' in page
    assert "setBusy" in script
    assert "clearBusy" in script
    assert '"Preparing backup…"' in script
    assert '"Restoring…"' in script
    assert 'setAttribute("aria-busy", "true")' in script


def test_customer_actions_use_specific_consistent_wording(client):
    welcome = client.get("/welcome").data.decode()
    client.post("/defaults", data=saved_defaults_data())
    client.post("/events/new", data=complete_event_inputs())
    pages = welcome + "".join(
        client.get(path).data.decode()
        for path in ("/dashboard", "/defaults", "/events/new", "/saved-events", "/data-safety")
    )

    for action in (
        "Start setup",
        "Save changes",
        "Analyze event",
        "Analyze new event",
        "Compare selected",
        "Download backup",
        "Restore backup",
    ):
        assert action in pages
    for vague in (">Submit<", ">Process<", ">Go<"):
        assert vague not in pages


def test_focus_reduced_motion_and_long_content_foundations(client):
    base = client.get("/static/css/base.css").data.decode()
    components = client.get("/static/css/components.css").data.decode()

    assert "outline: 2px solid var(--color-focus)" in base
    assert "scroll-margin-block: 5rem" in base
    assert "overflow-wrap: anywhere" in base
    assert "prefers-reduced-motion: reduce" in base
    assert "transition-duration: 0.01ms !important" in base
    assert 'summary:hover' in components
    assert '[aria-busy="true"]' in components


def test_long_event_scenario_and_location_names_remain_available(
    client, database_path
):
    submitted = complete_event_inputs()
    submitted["event_name"] = "Very long Event name " * 8
    submitted["location"] = "Long customer-facing location " * 8
    client.post("/events/new", data=submitted)
    save_sibling(client, database_path, "Long Scenario name " * 8)

    page = client.get("/saved-events").data.decode()

    assert "Very long Event name" in page
    assert "Long customer-facing location" in page
    assert "Long Scenario name" in page


def test_obsolete_design_system_selectors_and_hardcoded_errors_are_removed(client):
    forms = client.get("/static/css/forms.css").data.decode()
    layout = client.get("/static/css/layout.css").data.decode()

    for obsolete in (
        ".result-summary",
        ".result-section",
        ".dashboard-actions",
        ".dashboard-stats",
        ".placeholder-panel",
        ".data-safety-panel",
    ):
        assert obsolete not in forms
        assert obsolete not in layout
    assert "#a12622" not in forms
    assert "#8b1a1a" not in forms


def test_error_pages_use_current_product_terminology(client):
    not_found = client.get("/missing-screen").data.decode()
    error = client.get("/test-error").data.decode()

    assert "Go to saved events" in not_found
    assert "Back to saved events" in error
    assert "Event Calculator" not in not_found
    assert "Event Calculator" not in error
