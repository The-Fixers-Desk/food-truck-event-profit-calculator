from tests.test_complete_event_inputs_workflow import (
    complete_event_inputs,
    saved_defaults_data,
)


def test_dark_design_tokens_replace_the_light_palette(client):
    tokens = client.get("/static/css/tokens.css").data.decode()
    base = client.get("/static/css/base.css").data.decode()

    assert "--color-background: #101416" in tokens
    assert "--color-surface: #171c1f" in tokens
    assert "--color-sidebar: #0c1113" in tokens
    assert "--color-accent: #c66f36" in tokens
    assert "--color-text: #f1f0ed" in tokens
    assert "--color-success-surface: #152820" in tokens
    assert "--color-warning-surface: #2c2416" in tokens
    assert "--color-danger-surface: #301a1b" in tokens
    assert "--color-info-surface: #162731" in tokens
    assert "#f6f3ed" not in tokens
    assert "color-scheme: dark" in base


def test_dark_component_surfaces_cover_controls_tables_and_dialogs(client):
    components = client.get("/static/css/components.css").data.decode()
    forms = client.get("/static/css/forms.css").data.decode()

    assert "background: var(--color-surface)" in components
    assert "dialog, .dialog, .save-analysis-dialog" in components
    assert "background: rgb(0 0 0 / 72%)" in components
    assert ".save-analysis-dialog::backdrop" in forms
    assert "background: rgb(0 0 0 / 72%)" in forms
    assert ".form-panel" in forms
    assert "background: var(--color-surface)" in forms
    assert ".comparison-table" in forms
    assert "background: var(--color-warning-surface)" in forms


def test_sidebar_has_substantial_brand_and_accessible_selected_navigation(client):
    navigation = client.get("/static/css/navigation.css").data.decode()

    assert "width: clamp(17rem, 18vw, 19rem)" in navigation
    assert "font-size: clamp(1.25rem, 1.35vw, 1.5rem)" in navigation
    assert "min-height: var(--control-height)" in navigation
    assert "font-size: var(--text-md)" in navigation
    assert "box-shadow: inset 3px 0 var(--color-primary)" in navigation
    assert "@media (max-width: 800px)" in navigation
    assert "overflow-x: auto" in navigation


def test_approved_dashboard_hero_and_navigation_are_unchanged(client):
    client.post("/defaults", data=saved_defaults_data())
    page = client.get("/dashboard").data.decode()

    assert "Is your next event worth it?" in page
    assert "Test the demand, costs, and conditions before you commit." in page
    assert "Analyze new event" in page
    for label in (
        "Dashboard",
        "New analysis",
        "Saved events",
        "Business defaults",
        "Data safety",
    ):
        assert label in page
    assert 'aria-current="page"' in page


def test_guided_workflow_and_analysis_keep_their_primary_structure(client):
    inputs = client.get("/events/new").data.decode()
    forms = client.get("/static/css/forms.css").data.decode()

    for stage in (
        "Event details",
        "Demand and weather",
        "Revenue and food costs",
        "Labor",
        "Event costs and fees",
        "Profit target and review",
    ):
        assert stage in inputs
    assert "grid-template-columns: minmax(15rem, 17rem)" in forms
    assert ".section-switcher.workflow-stepper" in forms
    assert "grid-template-columns: minmax(0, 1fr)" in forms
    assert "overflow-x: visible" in forms
    assert "Back" in inputs
    assert "Continue" in inputs

    response = client.post("/events/new", data=complete_event_inputs())
    analysis = response.data.decode()
    assert "Business profit" in analysis
    assert "Break-even" in analysis
    assert "Save as new" in analysis


def test_management_and_safety_screens_remain_available_in_dark_shell(client):
    client.post("/defaults", data=saved_defaults_data())
    client.post("/events/new", data=complete_event_inputs())
    saved = client.get("/saved-events").data.decode()
    safety = client.get("/data-safety").data.decode()

    assert "Search" in saved
    assert "Sort by" in saved
    assert "Compare selected" in saved
    assert "Download backup" in safety
    assert "Restore backup" in safety
    assert 'class="app-shell"' in saved
    assert 'class="app-shell"' in safety
