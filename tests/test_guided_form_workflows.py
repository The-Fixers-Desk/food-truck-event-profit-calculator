import sqlite3

from tests.test_complete_event_inputs_workflow import complete_event_inputs


def test_defaults_uses_five_stage_review_workflow(client):
    page = client.get("/defaults").data.decode()

    assert 'class="guided-workflow"' in page
    assert 'aria-label="Defaults setup stages"' in page
    assert page.count("data-defaults-target=") == 5
    assert 'data-defaults-section="5"' in page
    assert "Review your business defaults" in page
    assert 'id="save-defaults" type="submit" hidden' in page
    assert "Save changes" in page


def test_defaults_stage_navigation_does_not_submit_or_reset_values(client):
    script = client.get("/static/js/business_defaults.js").data.decode()

    assert "completedThrough" in script
    assert "validateDefaultsSection" in script
    assert "updateDefaultsReview" in script
    assert 'defaultsForm.addEventListener("submit"' in script
    assert "event.preventDefault()" in script
    assert ".reset()" not in script


def test_event_inputs_uses_same_guided_workflow_and_review_primitives(client):
    page = client.get("/events/new").data.decode()
    script = client.get("/static/js/event_inputs.js").data.decode()

    assert 'class="guided-workflow"' in page
    assert 'class="section-switcher workflow-stepper event-stepper"' in page
    assert page.count('class="stage-completion-indicator"') == 6
    assert "stage-review" in page
    assert 'card.className = "review-section"' in script
    assert "updateReview" in script


def test_final_validation_marks_and_opens_first_invalid_event_stage(client):
    submitted = complete_event_inputs()
    submitted["event_name"] = ""
    submitted["owner_labor_pay"] = "-1"

    page = client.post("/events/new", data=submitted).data.decode()
    script = client.get("/static/js/event_inputs.js").data.decode()

    assert 'data-form-section="1"' in page
    assert 'aria-invalid="true"' in page
    assert "has-error" in script
    assert "firstEventError.focus()" in script


def test_stage_navigation_alone_writes_no_event_or_defaults_records(
    client, database_path
):
    client.get("/defaults")
    client.get("/events/new")
    client.get("/static/js/business_defaults.js")
    client.get("/static/js/event_inputs.js")

    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM business_defaults"
        ).fetchone()[0] == 0
        assert database.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0] == 0


def test_workflow_css_has_reusable_desktop_and_narrow_structure(client):
    css = client.get("/static/css/forms.css").data.decode()

    for primitive in (
        ".guided-workflow",
        ".workflow-stepper",
        ".workflow-stage",
        ".form-grid",
        ".labor-entry",
        ".additional-cost-entry",
        ".review-section",
        ".validation-summary",
        ".sticky-actions",
    ):
        assert primitive in css
    assert "@media (min-width: 900px)" in css
    assert "@media (max-width: 800px)" in css
    assert "grid-template-columns" in css
