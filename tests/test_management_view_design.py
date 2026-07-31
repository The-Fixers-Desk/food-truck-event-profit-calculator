from tests.test_complete_event_inputs_workflow import (
    complete_event_inputs,
    saved_defaults_data,
)
from tests.test_saved_events_management import save_sibling


def test_welcome_is_compact_three_step_orientation(client):
    page = client.get("/welcome").data.decode()

    assert 'class="page onboarding-page workspace-page--empty"' in page
    assert page.count('class="concise-onboarding-step"') == 3
    assert 'aria-label="Getting started steps"' in page
    assert "Get started" in page


def test_dashboard_has_one_primary_launch_and_no_destination_shortcuts(client):
    client.post("/defaults", data=saved_defaults_data())
    page = client.get("/dashboard").data.decode()

    assert 'class="button button--large dashboard-primary-action"' in page
    assert "Analyze new event" in page
    assert "No recent work yet" in page
    assert page.count("Analyze new event") == 1
    assert "dashboard-shortcuts" not in page
    assert "Useful shortcuts" not in page
    for fake_metric in ("Growth", "Average profit", "Success rate", "Trend"):
        assert fake_metric not in page


def test_dashboard_renders_accessible_whole_row_recent_work(client, database_path):
    client.post("/defaults", data=saved_defaults_data())
    client.post("/events/new", data=complete_event_inputs())
    save_sibling(client, database_path, "Rain plan")

    page = client.get("/dashboard").data.decode()

    assert "Continue where you left off" in page
    assert "Summer Festival" in page
    assert "Rain plan" in page
    assert 'class="recent-work-row recent-work-row--primary"' in page
    assert 'aria-label="Open Summer Festival, Rain plan analysis"' in page
    assert "Continue analysis" not in page


def test_saved_library_has_accessible_search_sort_and_no_results(client):
    client.post("/events/new", data=complete_event_inputs())
    page = client.get("/saved-events").data.decode()

    assert 'role="search"' in page
    assert 'for="saved-work-search"' in page
    assert 'type="search"' in page
    assert 'for="saved-work-sort"' in page
    assert "Recently modified" in page
    assert "Event date" in page
    assert "Event name" in page
    assert 'id="saved-work-no-results" hidden' in page
    assert "No matching saved work" in page
    assert 'id="saved-work-filter-status"' in page
    assert 'aria-live="polite"' in page


def test_saved_library_script_filters_sorts_clears_and_marks_selection(client):
    script = client.get("/static/js/saved_events.js").data.decode()

    assert "filterSavedWork" in script
    assert "sortSavedWork" in script
    assert "resetSearch" in script
    assert "toLocaleLowerCase" in script
    assert 'sort === "modified"' not in script  # default branch is modified-first
    assert 'sort === "event-date"' in script
    assert 'sort === "name"' in script
    assert 'classList.toggle(\n        "is-selected"' in script


def test_saved_rows_expose_event_scenario_identity_and_primary_actions(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    save_sibling(client, database_path, "Rain plan")
    page = client.get("/saved-events").data.decode()

    assert 'class="saved-event event-library-row"' in page
    assert 'data-event-name="Summer Festival"' in page
    assert 'data-event-date="2026-08-15"' in page
    assert 'data-scenario-name="Rain plan"' in page
    assert page.count('class="scenario-row__open"') == 2
    assert page.count('aria-label="Open Summer Festival,') == 2
    assert "Rename event" in page
    assert "Delete event" in page


def test_comparison_has_sticky_controls_identity_and_local_scrollers(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    _, second = save_sibling(client, database_path, "Rain plan")
    _, first = save_sibling(client, database_path, "Higher price")

    page = client.post(
        "/comparison", data={"scenario_id": [str(first), str(second)]}
    ).data.decode()

    assert 'class="comparison-controls sticky-management-controls"' in page
    assert "Comparison baseline" in page
    assert "Show differences only" in page
    assert page.count('class="comparison-identity comparison-header"') == 2
    assert 'role="region" tabindex="0"' in page
    assert "Business profit" in page
    assert "Break-even customers" in page


def test_data_safety_has_clear_normal_and_high_impact_tasks(client):
    page = client.get("/data-safety").data.decode()

    assert 'class="safety-action-grid"' in page
    assert "Download backup" in page
    assert "Restore replaces all current application data" in page
    assert "It does not merge records" in page
    assert 'class="button-destructive" id="restore-backup"' in page
    assert ">Restore backup</button>" in page
    assert "creates a recovery snapshot" in page
    assert "SQLite" not in page


def test_management_components_stack_at_narrow_widths(client):
    css = client.get("/static/css/components.css").data.decode()

    for component in (
        ".management-toolbar",
        ".management-row",
        ".selected-count-bar",
        ".compact-task-panels",
        ".task-panel",
        ".safety-action-panel",
        ".concise-onboarding-step",
    ):
        assert component in css
    assert "@media (max-width: 800px)" in css
    assert ".management-toolbar, .management-row, .safety-action-grid" in css
