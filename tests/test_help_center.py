import re

from app import create_app
from tests.test_complete_event_inputs_workflow import complete_event_inputs, saved_defaults_data


def test_help_control_opens_dedicated_help_center(client):
    shell = client.get("/welcome").data.decode()
    assert 'href="/help" aria-label="Help Center"' in shell

    response = client.get("/help")
    page = response.data.decode()
    assert response.status_code == 200
    assert "<h1>Help Center</h1>" in page
    assert 'class="app-shell"' in page


def test_help_section_navigation_and_bundled_guidance_render_offline(client):
    page = client.get("/help").data.decode()
    for target, heading in (
        ("getting-started", "Getting started"),
        ("core-concepts", "Core concepts"),
        ("data-safety-help", "Data and safety"),
        ("troubleshooting", "Common troubleshooting"),
        ("support-information", "Support information"),
        ("contact-support", "Still need help?"),
    ):
        assert f'href="#{target}"' in page
        assert f'id="{target}"' in page
        assert heading in page
    assert "Business Defaults and event inputs" in page
    assert "Events and Scenarios" in page
    assert "Worth it" in page and "Borderline" in page and "Not worth it" in page
    assert "backup import failed" in page.lower()
    assert "https://" not in page


def test_support_contact_and_boundaries_are_exact_and_publish_no_phone_number(client):
    page = client.get("/help").data.decode()
    assert page.count("contact@fixersdesk.com") == 2
    assert 'href="mailto:contact@fixersdesk.com"' in page
    assert "Support begins by email" in page
    assert "a phone call may be arranged" in page
    assert "Tax, legal, financial, event-planning" in page
    assert not re.search(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}", page)
    assert "response time" not in page.lower()


def test_external_support_url_is_centralized_and_graceful(tmp_path):
    unavailable = create_app({"DATA_ROOT": tmp_path / "none", "TESTING": True, "ENFORCE_SETUP": False})
    page = unavailable.test_client().get("/help").data.decode()
    assert "external product support page is not configured yet" in page

    configured = create_app({
        "DATA_ROOT": tmp_path / "configured",
        "TESTING": True,
        "ENFORCE_SETUP": False,
        "SUPPORT_URL": "https://support.fixersdesk.com/food-truck-calculator",
    })
    page = configured.test_client().get("/help").data.decode()
    assert page.count("https://support.fixersdesk.com/food-truck-calculator") == 1
    assert 'target="_blank" rel="noopener noreferrer"' in page
    assert "opens in a new window" in page


def test_diagnostics_include_required_metadata_and_exclude_customer_data(client):
    defaults = saved_defaults_data()
    defaults["business_name"] = "Private Rolling Kitchen"
    client.post("/defaults", data=defaults)
    event = complete_event_inputs()
    event["event_name"] = "Secret Harbor Festival"
    event["location"] = "Private Venue Address"
    client.post("/events/new", data=event)
    client.post("/local-profile", data={"display_name": "Private Owner", "email_address": "private@example.com"})

    response = client.get("/help/support-information")
    assert response.status_code == 200
    assert set(response.json) == {
        "app_name",
        "app_version",
        "operating_system",
        "data_storage",
        "database_schema_version",
        "last_successful_export",
    }
    serialized = response.get_data(as_text=True)
    for private_value in (
        "Private Rolling Kitchen",
        "Secret Harbor Festival",
        "Private Venue Address",
        "private@example.com",
        "Private Owner",
        str(client.application.config["DATABASE"]),
    ):
        assert private_value not in serialized
    assert response.json["app_name"] == "Food Truck Event Profit Calculator"
    assert response.json["app_version"]
    assert response.json["database_schema_version"] == "3"
    assert response.json["data_storage"] == "Local application data on this device"


def test_copy_support_information_adds_screen_and_connection_client_side(client):
    page = client.get("/help").data.decode()
    script = client.get("/static/js/help.js").data.decode()
    assert 'id="copy-support-information"' in page
    assert 'role="status" aria-live="polite"' in page
    assert "navigator.clipboard.writeText" in script
    assert "navigator.onLine" in script
    assert "window.location.pathname" in script
    assert "Support information copied" in script
    assert "Support information could not be copied" in script
    for forbidden in ("event_name", "event_location", "email_address", "financial_values", "stack_trace"):
        assert forbidden not in script


def test_help_navigation_is_keyboard_and_responsive_ready(client):
    page = client.get("/help").data.decode()
    script = client.get("/static/js/help.js").data.decode()
    css = client.get("/static/css/components.css").data.decode()
    assert 'aria-label="Help Center sections"' in page
    assert page.count('tabindex="-1" aria-labelledby=') == 6
    assert "section?.focus()" in script
    assert "copySupportButton.focus()" in script
    assert "@media (max-width: 767px)" in css
    assert ".help-center-layout { grid-template-columns: 1fr;" in css
