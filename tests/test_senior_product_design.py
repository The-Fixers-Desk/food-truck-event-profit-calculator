from tests.test_complete_event_inputs_workflow import complete_event_inputs, saved_defaults_data
from tests.test_saved_events_management import save_sibling


def test_dashboard_has_one_dominant_action_and_no_global_shortcut_cards(client):
    client.post("/defaults", data=saved_defaults_data())
    page = client.get("/dashboard").data.decode()

    assert page.count('class="button button--large dashboard-primary-action"') == 1
    assert page.count("Analyze new event") == 1
    assert "dashboard-shortcuts" not in page
    assert "compact-task-panels" not in page
    assert "Growth" not in page and "Trend" not in page


def test_dashboard_limits_recent_work_and_uses_semantic_row_links(client, database_path):
    client.post("/defaults", data=saved_defaults_data())
    client.post("/events/new", data=complete_event_inputs())
    for name in ("Rain plan", "Higher price", "Lower staffing"):
        save_sibling(client, database_path, name)

    page = client.get("/dashboard").data.decode()

    assert page.count('<a class="recent-work-row') <= 3
    assert "recent-work-row--primary" not in page
    assert "Continue analysis" not in page
    assert 'aria-label="Open Summer Festival,' in page
    assert 'href="/saved-events"' in page


def test_shell_removes_generic_context_and_uses_one_icon_family(client):
    client.post("/defaults", data=saved_defaults_data())
    page = client.get("/dashboard").data.decode()
    navigation = page.split('aria-label="Primary navigation"', 1)[1].split("</nav>", 1)[0]

    assert "Workspace" not in page
    assert "app-context-bar" not in page
    assert navigation.count('class="nav-icon"') == 5
    assert navigation.count("/static/icons/navigation.svg#") == 5
    assert 'aria-current="page"' in navigation


def test_saved_events_preserves_compact_open_compare_and_management(client, database_path):
    client.post("/events/new", data=complete_event_inputs())
    save_sibling(client, database_path, "Rain plan")
    page = client.get("/saved-events").data.decode()

    assert 'id="saved-work-search"' in page
    assert 'id="saved-work-sort"' in page
    assert 'action="/comparison"' in page
    assert page.count('class="scenario-row__open"') == 2
    assert "Manage" in page
    assert "Rename" in page and "Delete" in page
    assert 'class="event-library-table"' in page


def test_hidden_states_override_component_display_rules(client):
    css = client.get("/static/css/base.css").data.decode()
    assert "[hidden]" in css
    assert "display: none !important" in css


def test_analysis_keeps_decision_and_all_scenario_actions(client):
    page = client.post("/events/new", data=complete_event_inputs()).data.decode()

    assert "Business profit" in page
    assert "Profit target" in page
    assert "Break-even customers" in page
    for action in ("Save", "Save as new", "Reset changes", "Rename", "Compare", "Start new analysis"):
        assert action in page
    assert "More actions" in page
    assert "Calculation details" in page
