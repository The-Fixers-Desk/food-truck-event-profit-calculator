import sqlite3

from tests.test_complete_event_inputs_workflow import complete_event_inputs


def test_event_inputs_has_six_ordered_guided_stages(client):
    page = client.get("/events/new").data.decode()
    labels = (
        "Event details",
        "Demand and weather",
        "Revenue and food costs",
        "Labor",
        "Event costs and fees",
        "Profit target and review",
    )
    positions = [page.index(label) for label in labels]

    assert positions == sorted(positions)
    assert page.count("data-section-target=") == 6
    assert 'id="section-back"' in page
    assert 'id="section-continue"' in page
    assert 'id="analyze-event"' in page
    assert "Analyze event" in page


def test_stepper_script_preserves_dom_values_and_handles_errors_review(client):
    script = client.get("/static/js/event_inputs.js").data.decode()

    assert "showSection" in script
    assert "validateActiveSection" in script
    assert "invalid.reportValidity()" in script
    assert "invalid.focus()" in script
    assert "completedThrough" in script
    assert "has-error" in script
    assert "updateReview" in script
    assert "No values entered yet." in script
    assert ".reset()" not in script


def test_invalid_final_submission_keeps_values_and_marks_error_stage(client):
    form = complete_event_inputs()
    form["event_name"] = ""
    form["location"] = "Preserved long location"

    page = client.post("/events/new", data=form).data.decode()

    assert 'value="Preserved long location"' in page
    assert 'aria-invalid="true"' in page
    assert 'data-form-section="1"' in page


def test_moving_through_stages_does_not_create_records(client, database_path):
    client.get("/events/new")
    client.get("/static/js/event_inputs.js")

    with sqlite3.connect(database_path) as database:
        assert database.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0] == 0


def test_defaults_has_fast_section_navigation_and_sticky_save(client):
    page = client.get("/defaults").data.decode()
    script = client.get("/static/js/business_defaults.js").data.decode()

    for label in (
        "Business and sales",
        "Food and payment costs",
        "Labor and event costs",
        "Profit target",
    ):
        assert label in page
    assert page.count("data-defaults-target=") == 4
    assert "sticky-actions" in page
    assert "showDefaultsSection" in script
    assert "has-error" in script


def test_workspace_has_assumption_navigation_sticky_actions_and_results(client):
    page = client.post("/events/new", data=complete_event_inputs()).data.decode()

    assert 'aria-label="Assumption sections"' in page
    assert page.count("data-section-target=") == 5
    assert "Analysis results" in page
    assert 'aria-label="Key results"' in page
    assert "sticky-actions" in page
    assert "Calculate" not in page


def test_design_system_has_sticky_responsive_and_focus_foundations(client):
    forms = client.get("/static/css/forms.css").data.decode()
    base = client.get("/static/css/base.css").data.decode()
    tokens = client.get("/static/css/tokens.css").data.decode()

    assert ".sticky-actions" in forms
    assert "position: sticky" in forms
    assert "@media (max-width: 800px)" in forms
    assert "@media (max-width: 420px)" in forms
    assert ":focus-visible" in base
    assert "prefers-reduced-motion" in base
    assert "--color-success" in tokens
    assert "--color-warning" in tokens
    assert "--color-danger" in tokens
