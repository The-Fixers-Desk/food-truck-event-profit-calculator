import sqlite3

from app import create_app
from app.database import (
    business_defaults_setup_is_complete,
    get_database,
)
from tests.test_complete_event_inputs_workflow import complete_event_inputs
from tests.test_saved_events_management import save_sibling


def valid_defaults() -> dict[str, str | list[str]]:
    return {
        "business_name": "Roadside Kitchen",
        "average_order_sale_amount": "16.50",
        "food_cost_method_choice": "average_per_order",
        "food_cost_method": "average_per_order",
        "average_food_cost_per_order": "5.25",
        "food_cost_percentage": "",
        "typical_food_cost_total": "",
        "card_sales_percentage": "75",
        "card_processing_percentage": "2.9",
        "default_travel_cost": "",
        "default_owner_labor_pay": "",
        "profit_target_type": "profit_amount",
        "minimum_profit_amount": "400",
        "minimum_profit_margin": "",
        "labor_rate": ["20"],
        "labor_hours": ["8"],
    }


def guarded_app(database_path):
    return create_app(
        {
            "DATABASE": database_path,
            "ENFORCE_SETUP": True,
            "SECRET_KEY": "test",
            "TESTING": True,
            "PROPAGATE_EXCEPTIONS": False,
        }
    )


def test_fresh_launch_welcome_and_get_started_create_no_records(database_path):
    app = guarded_app(database_path)
    client = app.test_client()

    page = client.get("/").data.decode()

    assert "Set business defaults" in page
    assert "Describe an event" in page
    assert "Review the analysis" in page
    assert "Compare options" in page
    assert "Get started" in page
    assert "/defaults?setup=1" in page
    assert client.get("/defaults?setup=1").status_code == 200
    with app.app_context():
        database = get_database()
        assert database.execute(
            "SELECT COUNT(*) FROM business_defaults"
        ).fetchone()[0] == 0
        assert database.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0] == 0


def test_first_save_opens_dashboard_and_survives_restart(database_path):
    app = guarded_app(database_path)
    client = app.test_client()
    assert business_defaults_setup_is_complete_in(app) is False

    response = client.post("/defaults", data=valid_defaults())

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    assert business_defaults_setup_is_complete_in(app) is True

    restarted = guarded_app(database_path)
    response = restarted.test_client().get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    assert business_defaults_setup_is_complete_in(restarted) is True


def test_failed_first_save_stays_on_defaults_and_setup_remains_incomplete(
    database_path,
):
    app = guarded_app(database_path)
    submitted = valid_defaults()
    submitted["average_order_sale_amount"] = ""
    submitted["card_sales_percentage"] = "63"

    response = app.test_client().post("/defaults", data=submitted)

    assert response.status_code == 200
    assert b'value="63"' in response.data
    assert b"Average order sale amount is required." in response.data
    assert business_defaults_setup_is_complete_in(app) is False
    assert b"Welcome" in guarded_app(database_path).test_client().get("/").data


def test_existing_setup_skips_welcome_and_dashboard_has_empty_states(
    database_path,
):
    app = guarded_app(database_path)
    client = app.test_client()
    client.post("/defaults", data=valid_defaults())

    dashboard = client.get("/dashboard").data.decode()

    assert "Business defaults are available" in dashboard
    assert "<strong>0</strong> saved Events" in dashboard
    assert "<strong>0</strong> saved Scenarios" in dashboard
    assert "No recent work yet" in dashboard
    assert "At least two saved Scenarios are required." in dashboard
    assert "/events/new" in dashboard
    assert "/saved-events" in dashboard
    assert "/defaults" in dashboard
    assert client.get("/welcome").status_code == 302


def test_new_event_is_clean_and_prefilled_from_current_defaults(database_path):
    app = guarded_app(database_path)
    client = app.test_client()
    client.post("/defaults", data=valid_defaults())

    page = client.get("/events/new").data.decode()

    assert 'name="event_name"' in page
    assert 'id="event_name"' in page
    assert 'type="text" value="" required' in page
    assert 'name="average_order_sale_amount"' in page
    assert 'value="16.5"' in page
    with app.app_context():
        assert get_database().execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0] == 0


def test_setup_protected_routes_ignore_stale_session(database_path):
    app = guarded_app(database_path)
    client = app.test_client()
    with client.session_transaction() as session:
        session["onboarding_complete"] = True

    for path in (
        "/dashboard",
        "/events/new",
        "/saved-events",
        "/comparison",
        "/events/1/scenarios/1",
    ):
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/welcome")


def test_dashboard_counts_and_enables_comparison_with_two_scenarios(
    database_path,
):
    app = guarded_app(database_path)
    client = app.test_client()
    client.post("/defaults", data=valid_defaults())
    client.post("/events/new", data=complete_event_inputs())

    one_scenario = client.get("/dashboard").data.decode()
    assert "<strong>1</strong> saved Event" in one_scenario
    assert "<strong>1</strong> saved Scenario" in one_scenario
    assert "At least two saved Scenarios are required." in one_scenario

    save_sibling(client, database_path, "Rain plan")
    ready = client.get("/dashboard").data.decode()
    assert "<strong>2</strong> saved Scenarios" in ready
    assert "At least two saved Scenarios are required." not in ready
    assert "/saved-events#comparison-selection-form" in ready


def test_dashboard_repository_failure_uses_error_handler(
    database_path, monkeypatch
):
    app = guarded_app(database_path)
    client = app.test_client()
    client.post("/defaults", data=valid_defaults())
    monkeypatch.setattr(
        "app.routes.saved_event_counts",
        lambda: (_ for _ in ()).throw(sqlite3.OperationalError("broken")),
    )

    response = client.get("/dashboard")

    assert response.status_code == 500
    assert b"Something went wrong" in response.data


def business_defaults_setup_is_complete_in(app) -> bool:
    with app.app_context():
        return business_defaults_setup_is_complete()
