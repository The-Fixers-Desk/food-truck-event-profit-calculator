import sqlite3

import pytest

from app.comparison import build_comparison
from tests.test_complete_event_inputs_workflow import complete_event_inputs
from tests.test_saved_events_management import latest_ids, save_sibling


def scenario_ids(database_path):
    with sqlite3.connect(database_path) as database:
        return [
            row[0]
            for row in database.execute(
                "SELECT id FROM event_scenarios ORDER BY id"
            )
        ]


def create_scenarios(client, database_path, count=4):
    client.post("/events/new", data=complete_event_inputs())
    for index in range(2, count + 1):
        save_sibling(
            client,
            database_path,
            f"Scenario {index}",
            travel_cost=str(80 + index * 10),
        )
    return scenario_ids(database_path)


@pytest.mark.parametrize("count", (2, 3, 4))
def test_selecting_two_three_or_four_scenarios(
    client, database_path, count
):
    ids = create_scenarios(client, database_path, count)

    response = client.post(
        "/comparison", data={"scenario_id": [str(item) for item in ids]}
    )

    assert response.status_code == 200
    assert b"Scenario Comparison" in response.data
    assert response.data.count(b"Open analysis") == count


def test_comparing_scenarios_from_different_events_is_rejected(client, database_path):
    first = complete_event_inputs()
    first["event_name"] = "First Event"
    client.post("/events/new", data=first)
    first_id = latest_ids(database_path)[1]
    second = complete_event_inputs()
    second["event_name"] = "Second Event"
    client.post("/events/new", data=second)
    second_id = latest_ids(database_path)[1]

    page = client.post(
        "/comparison",
        data={"scenario_id": [str(first_id), str(second_id)]},
    ).data

    assert b"One or more selected Scenarios are no longer available." in page


@pytest.mark.parametrize(
    ("selected", "message"),
    (
        ([], b"Select at least two Scenarios"),
        (["1"], b"Select at least two Scenarios"),
        (
            ["1", "1"],
            b"The same Scenario cannot be selected more than once.",
        ),
        (
            ["1", "2", "3", "4", "5"],
            b"Select no more than four Scenarios.",
        ),
    ),
)
def test_comparison_selection_validation(client, selected, message):
    response = client.post(
        "/comparison", data={"scenario_id": selected}
    )

    assert response.status_code == 200
    assert message in response.data


def test_first_selected_is_baseline_and_baseline_can_change(
    client, database_path
):
    ids = create_scenarios(client, database_path, 2)

    page = client.post(
        "/comparison",
        data={"scenario_id": [str(ids[1]), str(ids[0])]},
    ).data.decode()
    script = client.get("/static/js/comparison.js").data.decode()

    first_radio = page.split(
        f'value="{ids[1]}"', 1
    )[1].split(">", 1)[0]
    assert "checked" in first_radio
    assert "Baseline:" in page
    assert "data-baseline" in page
    assert "updateBaseline" in script
    assert "aria-live" in page


def test_exact_money_count_percentage_and_category_differences(
    client, app, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    _, second_id = save_sibling(
        client,
        database_path,
        "Changed",
        travel_cost="100",
        organizer_commission_percentage="10",
        other_competing_food_vendors="0",
        weather_outlook="favorable",
        custom_weather_reduction="",
        event_protection="fully_outdoors",
    )
    first_id = scenario_ids(database_path)[0]

    with app.app_context():
        comparison = build_comparison([first_id, second_id])

    rows = {
        row["key"]: row
        for row in (
            comparison["result_rows"] + comparison["assumption_rows"]
        )
    }
    assert rows["travel_cost"]["differences"][first_id][second_id] == (
        "+$20.00"
    )
    assert rows["organizer_commission"]["differences"][first_id][
        second_id
    ] == "+5.00 percentage points"
    assert rows["total_food_vendors"]["differences"][first_id][
        second_id
    ] == "-5.00"
    assert rows["weather_outlook"]["differences"][first_id][
        second_id
    ] == "Different from baseline"


def test_unavailable_results_are_not_given_numeric_differences(
    client, app, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    _, second_id = save_sibling(
        client,
        database_path,
        "Zero sales",
        expected_sales_amount="0",
    )
    first_id = scenario_ids(database_path)[0]

    with app.app_context():
        comparison = build_comparison([first_id, second_id])

    margin = next(
        row
        for row in comparison["result_rows"]
        if row["key"] == "profit_margin"
    )
    assert margin["display"][second_id] == "Not available."
    assert margin["differences"][first_id][second_id] == "Not available."


def test_factual_highlights_include_ties_targets_and_warning_differences(
    client, app, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    _, tied_id = save_sibling(client, database_path, "Exact copy")
    _, loss_id = save_sibling(
        client,
        database_path,
        "Costly",
        manual_food_cost_total="9000",
    )
    ids = scenario_ids(database_path)

    with app.app_context():
        comparison = build_comparison(ids)

    highlights = comparison["highlights"]
    assert highlights["highest_profit"] == [ids[0], tied_id]
    assert highlights["lowest_cost"] == [ids[0], tied_id]
    assert loss_id in highlights["target_not_met"]
    assert highlights["warning_differences"][loss_id]


def test_complete_assumptions_and_ordered_rows_are_compared(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    _, second_id = save_sibling(
        client,
        database_path,
        "Different rows",
        employee_labor_rate=["30", "40"],
        employee_labor_hours=["2", "3"],
        additional_cost_name=["Water", "Security"],
        additional_cost_amount=["25", "90"],
    )
    first_id = scenario_ids(database_path)[0]

    page = client.post(
        "/comparison",
        data={"scenario_id": [str(first_id), str(second_id)]},
    ).data.decode()

    for label in (
        "Estimated attendance",
        "Percentage expected to buy food",
        "Average order amount",
        "Food-cost method",
        "Sales paid by card",
        "Employee labor entries",
        "Owner labor pay",
        "Generator or utility",
        "Named miscellaneous costs",
        "Profit-target value",
    ):
        assert label in page
    assert page.index("$30.00/hour") < page.index("$40.00/hour")
    assert page.index("Water: $25.00") < page.index("Security: $90.00")
    assert 'data-assumption-row="employee_labor_entries"' in page
    assert 'data-identical="false"' in page


def test_differences_only_keeps_results_and_hides_identical_assumptions(
    client, database_path
):
    ids = create_scenarios(client, database_path, 2)

    page = client.post(
        "/comparison", data={"scenario_id": [str(item) for item in ids]}
    ).data.decode()
    script = client.get("/static/js/comparison.js").data.decode()

    assert "Show differences only" in page
    assert 'data-comparison-row="business_profit"' in page
    assert 'data-identical="true"' in page
    assert 'querySelectorAll("[data-assumption-row]")' in script
    assert 'row.dataset.identical === "true"' in script


def test_comparison_recalculates_without_modifying_storage_or_defaults(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    save_sibling(client, database_path, "Second")
    ids = scenario_ids(database_path)
    with sqlite3.connect(database_path) as database:
        before = database.iterdump()
        before_sql = tuple(before)

    response = client.post(
        "/comparison", data={"scenario_id": [str(item) for item in ids]}
    )

    assert response.status_code == 200
    with sqlite3.connect(database_path) as database:
        after_sql = tuple(database.iterdump())
    assert after_sql == before_sql


def test_missing_selected_scenario_has_customer_facing_error(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    existing = latest_ids(database_path)[1]

    response = client.post(
        "/comparison",
        data={"scenario_id": [str(existing), "999"]},
    )

    assert b"no longer available" in response.data
    assert b"Saved Events" in response.data


def test_compared_scenario_opens_clean_existing_workspace(
    client, database_path
):
    client.post("/events/new", data=complete_event_inputs())
    event_id, second_id = save_sibling(
        client, database_path, "Open me", travel_cost="123"
    )

    response = client.get(
        f"/events/{event_id}/scenarios/{second_id}"
    )

    assert b"Open me" in response.data
    assert b'value="123"' in response.data
    save_button = response.data.split(
        b'id="open-save-analysis"', 1
    )[1].split(b">", 1)[0]
    assert b"disabled" in save_button
    with sqlite3.connect(database_path) as database:
        assert database.execute(
            "SELECT COUNT(*) FROM event_scenarios"
        ).fetchone()[0] == 2


def test_comparison_has_selection_keep_and_mobile_switching_controls(
    client, database_path
):
    ids = create_scenarios(client, database_path, 3)
    page = client.post(
        "/comparison", data={"scenario_id": [str(item) for item in ids]}
    ).data.decode()
    script = client.get("/static/js/comparison.js").data.decode()

    assert "Compare your scenarios" in page
    assert 'id="comparison-event"' in page
    assert "Add scenario" in page
    assert 'id="keep-selected-scenario"' in page
    assert page.count("data-mobile-scenario=") == 3
    assert "Strongest current option" in page
    assert "Best profit" in page
    assert "Best margin" in page
    assert "Lowest break-even" in page
    assert "selectScenario" in script
    assert "window.location.assign(destination)" in script


def test_duplicate_scenario_creates_copy_and_opens_it(client, database_path):
    client.post("/events/new", data=complete_event_inputs())
    event_id, scenario_id = latest_ids(database_path)

    response = client.post(
        f"/events/{event_id}/scenarios/{scenario_id}/duplicate"
    )

    assert response.status_code == 302
    with sqlite3.connect(database_path) as database:
        rows = database.execute(
            "SELECT id, scenario_name FROM event_scenarios ORDER BY id"
        ).fetchall()
    assert [row[1] for row in rows] == ["Original estimate", "Original estimate Copy"]
    assert response.headers["Location"].endswith(
        f"/events/{event_id}/scenarios/{rows[-1][0]}"
    )


def test_selection_and_comparison_structure_are_accessible_and_responsive(
    client, database_path
):
    ids = create_scenarios(client, database_path, 2)
    saved_page = client.get("/saved-events").data.decode()
    comparison_page = client.post(
        "/comparison", data={"scenario_id": [str(item) for item in ids]}
    ).data.decode()
    styles = client.get("/static/css/forms.css").data.decode()

    assert "Select Summer Festival — Original estimate" in saved_page
    assert 'aria-live="polite"' in saved_page
    assert '<table class="comparison-table">' in comparison_page
    assert 'scope="row"' in comparison_page
    assert "@media (max-width: 700px)" in styles
    assert "overflow-x: auto" in styles
