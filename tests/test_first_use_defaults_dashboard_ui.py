import sqlite3
import re

from tests.test_dashboard_onboarding import guarded_app, valid_defaults
from tests.test_complete_event_inputs_workflow import complete_event_inputs


def test_welcome_contains_approved_progress_actions_and_reassurance(database_path):
    client = guarded_app(database_path).test_client()
    page = client.get("/welcome").data.decode()

    for copy in (
        "First-time setup",
        "Welcome to your event profit calculator",
        "Setup",
        "Defaults",
        "Dashboard",
        "Start setup",
        "What you&rsquo;ll set up",
        "I&rsquo;ll do this later",
        "What happens next",
        "Before you begin",
        "Your data is private",
        "No accounts. No cloud.",
    ):
        assert copy in page
    assert 'action="/welcome/defer"' in page
    assert 'href="#setup-preview"' in page


def test_deferring_onboarding_opens_dashboard_without_creating_data(database_path):
    app = guarded_app(database_path)
    client = app.test_client()

    response = client.post("/welcome/defer")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    dashboard = client.get("/dashboard").data.decode()
    assert "Finish setup to analyze" in dashboard
    assert "Continue setup" in dashboard
    assert 'aria-disabled="true"' in dashboard
    with sqlite3.connect(database_path) as database:
        assert database.execute("SELECT COUNT(*) FROM business_defaults").fetchone()[0] == 0
        assert database.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_deferred_onboarding_survives_app_restart_with_session_cookie(database_path):
    first = guarded_app(database_path)
    first_client = first.test_client()
    first_client.post("/welcome/defer")
    cookie = first_client.get_cookie("session")

    restarted = guarded_app(database_path)
    restarted_client = restarted.test_client()
    restarted_client.set_cookie("session", cookie.value)

    response = restarted_client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_defaults_wizard_has_exact_steps_snapshot_and_save_states(database_path):
    client = guarded_app(database_path).test_client()
    page = client.get("/defaults?setup=1").data.decode()

    labels = (
        "Revenue assumptions",
        "Food cost method",
        "Profit rule",
        "Operating assumptions",
        "Review",
    )
    assert all(label in page for label in labels)
    step_labels = re.findall(
        r'<span class="workflow-stepper__copy"><strong>([^<]+)</strong>', page
    )
    assert step_labels == list(labels)
    assert page.count("data-defaults-target=") == 5
    assert "Current default snapshot" in page
    assert "Progress saved automatically" in page
    assert "Save and finish later" in page
    assert "Finish setup" in page
    assert "Setup<br>" in page and "completed" in page
    assert "Defaults<br>" in page and "active" in page


def test_defaults_wizard_script_supports_drafts_conditions_and_review(client):
    script = client.get("/static/js/business_defaults.js").data.decode()

    for behavior in (
        'const draftKey = "business-defaults-draft"',
        "window.localStorage.setItem",
        "window.localStorage.getItem",
        "showConfirmedFoodMethod",
        "updateProfitTarget(true)",
        "validateDefaultsSection",
        "updateDefaultsReview",
        "finishLaterButton.addEventListener",
    ):
        assert behavior in script


def test_finish_later_preserves_setup_incomplete_and_returns_to_dashboard(database_path):
    app = guarded_app(database_path)
    client = app.test_client()

    response = client.post("/defaults/finish-later")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with sqlite3.connect(database_path) as database:
        assert database.execute("SELECT COUNT(*) FROM business_defaults").fetchone()[0] == 0


def test_complete_welcome_defaults_dashboard_flow_and_revisit(database_path):
    app = guarded_app(database_path)
    client = app.test_client()

    assert client.get("/").status_code == 200
    client.post("/welcome/defer")
    response = client.post("/defaults", data=valid_defaults())

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    dashboard = client.get("/dashboard").data.decode()
    assert "Analyze new event" in dashboard
    assert client.get("/welcome").status_code == 302
    defaults = client.get("/defaults").data.decode()
    assert "First-time setup" not in defaults
    assert "Save changes" in defaults


def test_dashboard_uses_three_real_most_recent_events(database_path):
    app = guarded_app(database_path)
    client = app.test_client()
    client.post("/defaults", data=valid_defaults())
    for number in range(4):
        event = complete_event_inputs()
        event["event_name"] = f"Event {number}"
        client.post("/events/new", data=event)

    page = client.get("/dashboard").data.decode()

    assert "Event 3" in page
    assert "Event 2" in page
    assert "Event 1" in page
    assert "Event 0" not in page
    assert "View all saved events" in page
