from tests.test_complete_event_inputs_workflow import complete_event_inputs


def workspace_page(client):
    return client.post("/events/new", data=complete_event_inputs()).data.decode()


def test_decision_summary_precedes_assumptions_and_detailed_results(client):
    page = workspace_page(client)

    decision = page.index('class="analysis-overview"')
    assumptions = page.index('class="workspace-assumptions"')
    details = page.index('class="analysis-results"')

    assert decision < assumptions < details
    assert "Business profit" in page
    assert "Profit target" in page
    assert "Profit margin" in page
    assert "Break-even buyers" in page
    assert "data-recommendation-label" in page


def test_primary_metrics_and_expandable_breakdowns_render(client):
    page = workspace_page(client)

    assert 'class="financial-metrics"' in page
    for label in (
        "Revenue",
        "Food costs",
        "Employee labor",
        "Owner pay",
        "Fixed costs",
        "Organizer fees",
        "Total costs",
    ):
        assert label in page
    for heading in (
        "Revenue",
        "Food",
        "Labor",
        "Fees",
        "Additional costs",
        "Profit calculations",
    ):
        assert f"<summary>{heading}</summary>" in page
    assert page.count('class="calculation-section"') == 6


def test_scenario_actions_are_consolidated_and_available(client):
    page = workspace_page(client)
    action_bar = page.split('class="scenario-action-bar"', 1)[1].split(
        "</section>", 1
    )[0]

    for action in (
        "Original estimate",
        "Save",
        "Save as new",
        "Reset changes",
        "Rename",
        "Compare",
    ):
        assert action in action_bar
    assert 'id="open-save-analysis"' in action_bar
    assert 'id="open-save-as-new"' in action_bar


def test_workspace_header_and_overview_match_saved_scenario_workflow(client):
    page = workspace_page(client)

    assert 'id="workspace-scenario-selector"' in page
    assert "Duplicate scenario" in page
    assert "Compare scenarios" in page
    assert "Scenarios" in page
    assert "Event snapshot" in page
    assert "Input summary" in page
    assert "Estimated revenue" in page
    assert "Estimated profit" in page
    assert "Profitability summary" in page
    assert "Decision checks" in page
    assert "What changes the result" in page
    assert 'href="#adjustable-assumptions"' in page


def test_workspace_live_script_updates_new_decision_regions(client):
    script = client.get("/static/js/event_inputs.js").data.decode()

    assert "result.recommendation_label" in script
    assert "result.recommendation_tone" in script
    assert "updateCostComposition(result)" in script
    assert 'document.querySelector("#workspace-scenario-selector")' in script


def test_warnings_are_contextual_and_live(client):
    page = workspace_page(client)

    assert 'class="warning-panel workspace-warning-panel"' in page
    assert "Factual warnings" in page
    assert 'id="analysis-warnings" class="analysis-warnings" aria-live="polite"' in page


def test_live_update_contract_updates_decision_and_all_metrics(client):
    script = client.get("/static/js/event_inputs.js").data.decode()

    assert 'document.querySelectorAll("[data-result-field]")' in script
    assert 'document.querySelector("#decision-recommendation")' in script
    assert "result.profit_target?.is_met" in script
    assert "result.profitability_status" in script
    assert "recommendation.textContent" in script


def test_workspace_css_preserves_two_regions_and_narrow_source_order(client):
    css = client.get("/static/css/forms.css").data.decode()

    for component in (
        ".decision-summary",
        ".financial-metric",
        ".scenario-action-bar",
        ".warning-panel",
        ".recommendation-summary",
        ".grouped-financial-breakdown",
        ".calculation-section",
    ):
        assert component in css
    assert "grid-template-columns: minmax(32rem, 1.12fr)" in css
    assert "@media (max-width: 1100px)" in css
    assert "@media (max-width: 800px)" in css
    assert ".decision-region," in css


def test_expandable_calculations_have_semantic_keyboard_controls(client):
    page = workspace_page(client)

    assert page.count("<details class=\"calculation-section\">") == 6
    assert page.count("<summary>") >= 6
    assert 'aria-labelledby="profitability-summary-title"' in page
    assert 'aria-labelledby="analysis-results-title"' in page
