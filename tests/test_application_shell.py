from tests.test_complete_event_inputs_workflow import (
    complete_event_inputs,
    saved_defaults_data,
)


def configured_shell(client):
    client.post("/defaults", data=saved_defaults_data())
    return client.get("/dashboard").data.decode()


def test_normal_pages_share_one_sidebar_navigation_and_product_identity(client):
    page = configured_shell(client)

    assert page.count('aria-label="Primary navigation"') == 1
    assert page.count('class="app-sidebar"') == 1
    assert "The Fixer&rsquo;s Desk" in page
    assert "Food Truck Event Profit Calculator" in page
    assert page.count('id="main-content"') == 1
    assert 'href="#main-content"' in page


def test_global_navigation_contains_only_major_destinations(client):
    page = configured_shell(client)

    for label, href in (
        ("Dashboard", "/dashboard"),
        ("New analysis", "/events/new"),
        ("Saved events", "/saved-events"),
        ("Business defaults", "/defaults"),
        ("Data safety", "/data-safety"),
    ):
        assert label in page
        assert f'href="{href}"' in page
    navigation = page.split('aria-label="Primary navigation"', 1)[1].split(
        "</nav>", 1
    )[0]
    for local_label in (
        "Demand and weather",
        "Revenue and food costs",
        "Profit target",
        "Compare scenarios",
    ):
        assert local_label not in navigation


def test_current_destination_uses_icon_restrained_state_and_aria(client):
    page = configured_shell(client)
    navigation = page.split('aria-label="Primary navigation"', 1)[1].split(
        "</nav>", 1
    )[0]

    assert 'nav-link nav-link--active' in navigation
    assert 'aria-current="page"' in navigation
    assert 'class="nav-icon" aria-hidden="true"' in navigation
    assert "/static/icons/navigation.svg#dashboard" in navigation
    assert 'class="nav-marker"' not in navigation


def test_setup_incomplete_shell_hides_setup_dependent_destinations(client, app):
    app.config["ENFORCE_SETUP"] = True
    page = client.get("/").data.decode()
    navigation = page.split('aria-label="Primary navigation"', 1)[1].split(
        "</nav>", 1
    )[0]

    assert "Welcome" in navigation
    assert "Business defaults" in navigation
    assert "Data safety" in navigation
    assert "New analysis" not in navigation
    assert "Saved events" not in navigation


def test_event_and_scenario_identity_appear_in_analysis_header(client):
    page = client.post("/events/new", data=complete_event_inputs()).data.decode()
    context = page.split('class="page-header"', 1)[1].split("</header>", 1)[0]

    assert "Summer Festival" in context
    assert "Original estimate" in context


def test_global_navigation_keeps_dirty_workspace_hooks(client):
    page = client.post("/events/new", data=complete_event_inputs()).data.decode()
    navigation = page.split('aria-label="Primary navigation"', 1)[1].split(
        "</nav>", 1
    )[0]

    assert navigation.count("data-discard-navigation") == 5
    script = client.get("/static/js/event_inputs.js").data.decode()
    assert "Discard unsaved changes and leave this analysis?" in script


def test_responsive_shell_is_one_navigation_system(client):
    css = client.get("/static/css/navigation.css").data.decode()

    assert "@media (max-width: 800px)" in css
    assert ".app-sidebar" in css
    assert "overflow-x: auto" in css
    compact_rules = css.split("@media (max-width: 800px)", 1)[1]
    assert ".app-sidebar {\n    display: none" not in compact_rules
    assert ".app-navigation {\n    display: none" not in compact_rules


def test_recovery_shell_exposes_only_data_safety(client, app):
    app.config["RECOVERY_MODE"] = True
    page = client.get("/data-safety").data.decode()
    navigation = page.split('aria-label="Primary navigation"', 1)[1].split(
        "</nav>", 1
    )[0]

    assert "Data safety" in navigation
    assert "Dashboard" not in navigation
    assert "New analysis" not in navigation
    assert "Saved events" not in navigation
    assert "Business defaults" not in navigation


def test_shared_page_width_primitives_without_generic_context_bar(client):
    css = client.get("/static/css/layout.css").data.decode()

    for primitive in (
        ".app-workspace",
        ".app-main--calculator",
        ".workspace-page--wide",
        ".workspace-page--form",
        ".workspace-page--list",
        ".workspace-page--recovery",
    ):
        assert primitive in css
    assert ".app-context-bar" not in css
    page = configured_shell(client)
    assert "Workspace" not in page
