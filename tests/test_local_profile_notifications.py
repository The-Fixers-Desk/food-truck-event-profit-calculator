import sqlite3

from app import create_app
from app.local_state import create_notification, maybe_create_backup_reminder
from tests.test_dashboard_onboarding import valid_defaults
from tests.test_complete_event_inputs_workflow import complete_event_inputs


def test_top_level_breadcrumb_is_not_duplicated_and_nested_is_preserved(client):
    client.post("/defaults", data=valid_defaults())
    dashboard = client.get("/dashboard").data.decode()
    assert dashboard.count('class="breadcrumbs__current"') == 1
    breadcrumb = dashboard.split('<nav class="breadcrumbs"', 1)[1].split("</nav>", 1)[0]
    assert ">Dashboard</a>" not in breadcrumb

    workspace = client.post("/events/new", data=complete_event_inputs()).data.decode()
    workspace_breadcrumb = workspace.split('<nav class="breadcrumbs"', 1)[1].split("</nav>", 1)[0]
    assert "Saved events" in workspace_breadcrumb
    assert "Analysis" in workspace_breadcrumb
    assert workspace_breadcrumb.count("&middot;") == 2 or workspace_breadcrumb.count("·") == 2
    assert 'aria-current="page"' in workspace


def test_event_inputs_uses_integrated_estimate_guidance(client):
    page = client.get("/events/new").data.decode()
    assert 'class="estimate-guidance"' in page
    assert "This estimate applies only to this event." in page
    assert "You can save multiple scenarios" in page
    assert 'id="about-estimates"' not in page


def test_local_profile_create_validate_edit_and_restart(app, client, database_path):
    fallback = client.get("/welcome").data.decode()
    assert "Set up local profile" in fallback
    invalid = client.post("/local-profile", data={"display_name": "", "email_address": "bad"})
    assert invalid.status_code == 400
    assert invalid.json["errors"] == {
        "display_name": "Enter a display name.",
        "email_address": "Enter an email address in a valid format.",
    }

    saved = client.post("/local-profile", data={"display_name": "Alex Morgan", "email_address": " ALEX@Example.com "})
    assert saved.status_code == 200
    page = client.get("/welcome").data.decode()
    assert "Alex Morgan" in page
    assert "alex@example.com" in page
    assert ">AM<" in page

    restarted = create_app({"DATABASE": database_path, "TESTING": True, "ENFORCE_SETUP": False, "SECRET_KEY": "test"})
    assert "Alex Morgan" in restarted.test_client().get("/welcome").data.decode()


def test_long_profile_values_are_constrained_and_render_with_full_value_title(client):
    name = "A" * 120
    email = "person@" + "e" * 40 + ".example"
    assert client.post("/local-profile", data={"display_name": name, "email_address": email}).status_code == 200
    page = client.get("/welcome").data.decode()
    assert f'title="{name}"' in page
    assert f'title="{email}"' in page
    assert client.post("/local-profile", data={"display_name": "A" * 121, "email_address": email}).status_code == 400


def test_notifications_order_read_dismiss_persist_and_are_actionable(app, client, database_path):
    with app.app_context():
        first = create_notification("first", "First local update")
        second = create_notification("second", "Second local update", action_url="/data-safety", action_label="Open Data Safety")
    page = client.get("/welcome").data.decode()
    assert page.index("Second local update") < page.index("First local update")
    assert "2 unread" in page
    assert "Open Data Safety" in page
    assert client.post(f"/notifications/{first}/read").json["updated"] is True
    assert client.post(f"/notifications/{second}/dismiss").json["updated"] is True

    restarted = create_app({"DATABASE": database_path, "TESTING": True, "ENFORCE_SETUP": False, "SECRET_KEY": "test"})
    restarted_page = restarted.test_client().get("/welcome").data.decode()
    assert "Second local update" not in restarted_page
    assert "First local update" in restarted_page
    assert "2 unread" not in restarted_page


def test_notification_retention_mark_all_and_empty_state(app, client):
    with app.app_context():
        for number in range(55):
            create_notification(f"item_{number}", f"Update {number}")
        assert app.extensions is not None
    database = sqlite3.connect(app.config["DATABASE"])
    assert database.execute("SELECT COUNT(*) FROM notifications").fetchone()[0] == 50
    database.close()
    assert client.post("/notifications/read-all").json["updated"] is True
    database = sqlite3.connect(app.config["DATABASE"])
    assert database.execute("SELECT COUNT(*) FROM notifications WHERE read_at IS NULL").fetchone()[0] == 0
    database.execute("UPDATE notifications SET dismissed_at = CURRENT_TIMESTAMP")
    database.commit()
    database.close()
    assert "You&rsquo;re all caught up." in client.get("/welcome").data.decode()


def test_backup_reminder_requires_data_and_is_throttled(app, client):
    with app.app_context():
        maybe_create_backup_reminder(last_export=None)
        database = sqlite3.connect(app.config["DATABASE"])
        assert database.execute("SELECT COUNT(*) FROM notifications").fetchone()[0] == 0
        database.close()
    client.post("/defaults", data=valid_defaults())
    client.get("/dashboard")
    client.get("/dashboard")
    database = sqlite3.connect(app.config["DATABASE"])
    assert database.execute("SELECT COUNT(*) FROM notifications WHERE code='backup_reminder'").fetchone()[0] == 1
    database.close()


def test_profile_and_notifications_follow_clear_reset_and_event_delete_contract(app, client):
    client.post("/local-profile", data={"display_name": "Local Owner", "email_address": "owner@example.com"})
    client.post("/defaults", data=valid_defaults())
    with app.app_context():
        create_notification("review", "Review this")
    client.post("/data-safety/reset-defaults", data={"confirmation": "reset-defaults"})
    database = sqlite3.connect(app.config["DATABASE"])
    assert database.execute("SELECT COUNT(*) FROM local_profile").fetchone()[0] == 1
    assert database.execute("SELECT COUNT(*) FROM notifications").fetchone()[0] >= 1
    database.close()
    client.post("/data-safety/clear", data={"confirmation_phrase": "CLEAR ALL DATA"})
    database = sqlite3.connect(app.config["DATABASE"])
    assert database.execute("SELECT COUNT(*) FROM local_profile").fetchone()[0] == 0
    assert database.execute("SELECT COUNT(*) FROM notifications").fetchone()[0] == 0
    database.close()


def test_shell_script_has_keyboard_outside_click_and_profile_hooks(client):
    script = client.get("/static/js/shell.js").data.decode()
    assert 'event.key === "Escape"' in script
    assert 'event.target.closest(".topbar-utilities")' in script
    assert "data-notifications-read-all" in script
    assert "profileDialog.showModal()" in script
