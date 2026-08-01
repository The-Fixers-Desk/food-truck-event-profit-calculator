from tests.test_complete_event_inputs_workflow import complete_event_inputs, saved_defaults_data


def configured_page(client, path="/dashboard"):
    client.post("/defaults", data=saved_defaults_data())
    return client.get(path).data.decode()


def test_approved_shell_geometry_and_charcoal_tokens(client):
    tokens = client.get("/static/css/tokens.css").data.decode()
    layout = client.get("/static/css/layout.css").data.decode()

    for token in (
        "--color-background: #111315",
        "--color-sidebar: #121416",
        "--color-surface: #181b1d",
        "--color-surface-elevated: #1e2123",
        "--color-surface-subtle: #151719",
        "--color-accent: #c47a3a",
        "--sidebar-width: 280px",
        "--topbar-height: 64px",
        "--content-width: 1280px",
    ):
        assert token in tokens
    assert "grid-template-columns: var(--sidebar-width)" in layout
    assert "grid-template-rows: var(--topbar-height)" in layout


def test_shell_renders_topbar_breadcrumbs_utilities_and_workspace_block(client):
    page = configured_page(client)

    assert 'class="app-topbar"' in page
    assert 'aria-label="Breadcrumb"' in page
    assert 'aria-label="Search saved events"' in page
    assert 'aria-label="Notifications"' in page
    assert 'aria-label="Help"' in page
    assert 'id="workspace-menu-trigger"' in page
    assert "Local workspace" in page
    assert 'aria-current="page"' in page


def test_mobile_drawer_is_keyboard_managed_and_restores_focus(client):
    page = configured_page(client)
    script = client.get("/static/js/shell.js").data.decode()

    assert 'id="mobile-menu-trigger"' in page
    assert 'aria-controls="app-sidebar"' in page
    assert 'id="drawer-backdrop"' in page
    assert 'event.key === "Escape"' in script
    assert 'event.key === "Tab"' in script
    assert "menuTrigger.focus()" in script
    assert 'sidebar.setAttribute("aria-hidden"' in script


def test_system_state_api_and_real_empty_state(client):
    macro = client.application.jinja_env.loader.get_source(
        client.application.jinja_env, "_system_state.html"
    )[0]
    page = configured_page(client, "/saved-events")

    for option in (
        "variant", "icon", "title", "description", "primary_label",
        "primary_href", "secondary_label", "secondary_href", "retry",
        "live", "status_label",
    ):
        assert option in macro
    assert "No saved events yet" in page
    assert "Start first analysis" in page
    assert "Learn how it works" in page
    assert 'system-state--empty' in page


def test_every_system_state_has_a_deterministic_testing_route(client):
    page = client.get("/test-system-states").data.decode()

    for variant in ("empty", "loading", "error", "not-found", "offline"):
        assert f'system-state--{variant}' in page
    assert "Local data available" in page


def test_loading_state_is_integrated_with_event_submission(client):
    page = client.get("/events/new").data.decode()
    script = client.get("/static/js/event_inputs.js").data.decode()

    assert "Calculating your estimate&hellip;" in page
    assert 'id="calculation-loading-state"' in page
    assert page.count('system-state__skeleton-row') == 3
    assert 'aria-live="polite" aria-busy="true"' in page
    assert "calculationLoadingState.hidden = false" in script


def test_error_and_not_found_use_shared_recovery_pattern(client):
    not_found = client.get("/missing-event").data.decode()
    error = client.get("/test-error").data.decode()

    assert "This event no longer exists" in not_found
    assert "Go to saved events" in not_found
    assert 'system-state--not-found' in not_found
    assert "We couldn&#39;t load this event" in error
    assert "Retry" in error
    assert "Back to saved events" in error
    assert 'data-retry-page' in error


def test_offline_state_is_available_without_blocking_local_content(client):
    page = configured_page(client)
    script = client.get("/static/js/shell.js").data.decode()

    assert 'id="offline-system-state"' in page
    assert "You&rsquo;re offline" in page
    assert "Local data available" in page
    assert 'window.addEventListener("offline"' in script
    assert "navigator.onLine" in script
    assert "Dashboard" in page


def test_primary_routes_keep_rendering_inside_the_shared_shell(client):
    client.post("/defaults", data=saved_defaults_data())
    for path in (
        "/dashboard", "/events/new", "/saved-events", "/defaults",
        "/data-safety",
    ):
        page = client.get(path).data.decode()
        assert 'class="app-shell"' in page
        assert 'class="app-topbar"' in page
        assert 'id="main-content"' in page

    workspace = client.post("/events/new", data=complete_event_inputs()).data.decode()
    assert "Business profit" in workspace
    assert 'class="app-topbar"' in workspace
