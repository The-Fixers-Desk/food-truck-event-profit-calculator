from tests.test_complete_event_inputs_workflow import (
    complete_event_inputs,
    saved_defaults_data,
)


def test_shared_layout_uses_fluid_content_widths(client):
    css = client.get("/static/css/layout.css").data.decode()
    tokens = client.get("/static/css/tokens.css").data.decode()

    assert "--content-width: 1680px" in tokens
    assert "calc(100% - clamp(2rem, 4vw, 5rem))" in css
    assert "padding-block: clamp(" in css
    assert "--content-width: 1760px" in css
    assert ".workspace-page--list { max-width: 1380px; }" in css


def test_dashboard_composes_hero_and_recent_work_across_desktop_widths(client):
    client.post("/defaults", data=saved_defaults_data())
    client.post("/events/new", data=complete_event_inputs())
    page = client.get("/dashboard").data.decode()
    css = client.get("/static/css/components.css").data.decode()

    assert page.index("dashboard-intro") < page.index("dashboard-recent")
    assert "Analyze new event" in page
    assert "Continue where you left off" in page
    assert "font-size: clamp(3rem, 4.5vw, 4.75rem)" in css
    assert "@media (min-width: 1800px)" in css
    assert "grid-template-columns: minmax(32rem, 0.78fr)" in css


def test_sidebar_branding_and_selected_navigation_remain_accessible(client):
    client.post("/defaults", data=saved_defaults_data())
    page = client.get("/dashboard").data.decode()
    css = client.get("/static/css/navigation.css").data.decode()

    assert "Food Truck Event Profit Calculator" in page
    assert "The Fixer&rsquo;s Desk" in page
    assert 'aria-current="page"' in page
    assert "width: clamp(14.5rem, 16vw, 16.5rem)" in css
    assert "box-shadow: inset 3px 0 var(--color-primary)" in css
    assert ".nav-link--active .nav-icon" in css


def test_analysis_uses_fluid_columns_without_changing_section_order(client):
    css = client.get("/static/css/forms.css").data.decode()

    assert "grid-template-columns: minmax(32rem, 1.12fr)" in css
    assert "gap: clamp(var(--space-5), 2.5vw, var(--space-8))" in css
    assert "@media (max-width: 1100px)" in css
    assert "grid-template-columns: minmax(0, 1fr)" in css


def test_focus_reduced_motion_and_horizontal_containment_are_preserved(client):
    base = client.get("/static/css/base.css").data.decode()
    navigation = client.get("/static/css/navigation.css").data.decode()
    forms = client.get("/static/css/forms.css").data.decode()

    assert ":focus-visible" in base
    assert "@media (prefers-reduced-motion: reduce)" in base
    assert "overflow-x: auto" in navigation
    assert ".comparison-table-wrap" in forms
    assert "overflow-x: auto" in forms
