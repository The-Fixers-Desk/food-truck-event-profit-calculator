import sqlite3

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from app.business_defaults_form import defaults_to_form, validate_defaults_form
from app.calculations import calculate_event_scenario
from app.database import (
    FinalScenarioDeletionError,
    ScenarioNameConflict,
    create_event_scenario,
    create_event_with_initial_scenario,
    delete_event,
    delete_event_scenario,
    list_saved_events,
    load_business_defaults,
    load_event_scenario,
    overwrite_event_scenario,
    rename_event,
    rename_event_scenario,
    save_business_defaults,
)
from app.event_inputs_form import (
    blank_event_inputs_form,
    calculation_result_data,
    calculate_demand_preview,
    event_scenario_to_form,
    protection_reductions,
    scenario_from_form_values,
    validate_and_calculate_event_analysis,
    weather_allows_protection,
)

main = Blueprint("main", __name__)


@main.route("/", methods=("GET", "POST"))
def calculator():
    """Display the Event Inputs screen."""
    errors = {}
    workspace = False
    identity = None
    analysis = None
    active_event_id = None
    active_scenario_id = None
    active_scenario_name = None
    save_error = None
    if request.method == "POST":
        identity, form_values, errors, result = (
            validate_and_calculate_event_analysis(request.form)
        )
        if result is not None:
            try:
                scenario = scenario_from_form_values(
                    form_values, "Original estimate"
                )
                active_event_id, active_scenario_id = (
                    create_event_with_initial_scenario(identity, scenario)
                )
            except sqlite3.Error:
                save_error = (
                    "The event could not be saved. Please try again."
                )
            else:
                workspace = True
                _, identity, scenario = load_event_scenario(
                    active_scenario_id
                )
                form_values = event_scenario_to_form(identity, scenario)
                active_scenario_name = scenario.scenario_name
                analysis = calculation_result_data(
                    calculate_event_scenario(scenario)
                )
    else:
        form_values = blank_event_inputs_form(load_business_defaults())

    return render_template(
        "calculator.html",
        active_page="calculator",
        form_values=form_values,
        errors=errors,
        protection_reductions=protection_reductions(form_values),
        show_event_protection=weather_allows_protection(form_values),
        workspace=workspace,
        event_identity=identity,
        analysis=analysis,
        active_event_id=active_event_id,
        active_scenario_id=active_scenario_id,
        active_scenario_name=active_scenario_name,
        save_error=save_error,
    )


@main.post("/event-inputs/demand-preview")
def demand_preview():
    """Return a calculation-backed shared-demand preview without saving."""
    preview, errors = calculate_demand_preview(request.form)
    if errors:
        return jsonify({"ready": False, "errors": errors})
    return jsonify({"ready": True, **preview})


@main.post("/event-analysis/calculate")
def recalculate_event_analysis():
    """Validate and calculate current workspace assumptions without saving."""
    _, _, errors, result = validate_and_calculate_event_analysis(
        request.form
    )
    if errors:
        return jsonify(
            {
                "valid": False,
                "errors": errors,
                "status": (
                    "Results will update after the highlighted values "
                    "are corrected."
                ),
            }
        )
    return jsonify(
        {
            "valid": True,
            "result": calculation_result_data(result),
            "status": "Analysis updated.",
        }
    )


@main.post("/event-analysis/save")
def save_event_analysis():
    """Save current valid assumptions as a sibling or overwrite the active one."""
    _, values, errors, result = validate_and_calculate_event_analysis(
        request.form
    )
    if errors:
        return jsonify(
            {
                "saved": False,
                "errors": errors,
                "message": "Correct the highlighted values before saving.",
            }
        )
    try:
        event_id = int(request.form.get("active_event_id", ""))
        scenario_id = int(request.form.get("active_scenario_id", ""))
    except ValueError:
        return jsonify(
            {
                "saved": False,
                "save_error": "The active scenario could not be identified.",
            }
        ), 400

    mode = request.form.get("save_mode", "new")
    try:
        stored_event_id, _, stored = load_event_scenario(scenario_id)
        if stored_event_id != event_id:
            raise ValueError("The active scenario does not match.")
        if mode == "new":
            name = request.form.get("scenario_name", "").strip()
            if not name:
                return jsonify(
                    {
                        "saved": False,
                        "scenario_name_error": "Scenario name is required.",
                    }
                )
            scenario = scenario_from_form_values(values, name)
            new_scenario_id = create_event_scenario(event_id, scenario)
            scenario_id = new_scenario_id
            active_name = name
            message = f'Scenario "{name}" saved.'
        elif mode == "overwrite":
            if request.form.get("overwrite_confirmed") != "true":
                return jsonify(
                    {
                        "saved": False,
                        "overwrite_error": (
                            "Confirm that you want to overwrite the "
                            "current scenario."
                        ),
                    }
                )
            scenario = scenario_from_form_values(
                values, stored.scenario_name
            )
            overwrite_event_scenario(scenario_id, scenario)
            active_name = stored.scenario_name
            message = f'Scenario "{active_name}" overwritten.'
        else:
            return jsonify(
                {"saved": False, "save_error": "Choose a save option."}
            )
    except ScenarioNameConflict as error:
        return jsonify(
            {
                "saved": False,
                "scenario_name_error": str(error),
            }
        )
    except (sqlite3.Error, ValueError):
        return jsonify(
            {
                "saved": False,
                "save_error": "The scenario could not be saved.",
            }
        )

    return jsonify(
        {
            "saved": True,
            "active_event_id": event_id,
            "active_scenario_id": scenario_id,
            "active_scenario_name": active_name,
            "result": calculation_result_data(result),
            "message": message,
        }
    )


@main.route("/defaults", methods=("GET", "POST"))
def defaults():
    """Display the Defaults screen."""
    errors = {}
    if request.method == "POST":
        defaults_record, form_values, errors = validate_defaults_form(
            request.form
        )
        if defaults_record is not None:
            save_business_defaults(defaults_record)
            flash("Business defaults saved successfully.", "success")
            return redirect(url_for("main.defaults"))
    else:
        form_values = defaults_to_form(load_business_defaults())

    return render_template(
        "defaults.html",
        active_page="defaults",
        form_values=form_values,
        errors=errors,
    )


@main.get("/saved-events")
def saved_events():
    """Display saved Events grouped with their Scenarios."""
    return _render_saved_events()


@main.get("/events/<int:event_id>/scenarios/<int:scenario_id>")
def open_saved_scenario(event_id: int, scenario_id: int):
    """Open one persisted Scenario in the existing analysis workspace."""
    try:
        stored_event_id, identity, scenario = load_event_scenario(
            scenario_id
        )
    except ValueError:
        abort(404)
    if stored_event_id != event_id:
        abort(404)
    form_values = event_scenario_to_form(identity, scenario)
    return render_template(
        "calculator.html",
        active_page="calculator",
        form_values=form_values,
        errors={},
        protection_reductions=protection_reductions(form_values),
        show_event_protection=weather_allows_protection(form_values),
        workspace=True,
        event_identity=identity,
        analysis=calculation_result_data(
            calculate_event_scenario(scenario)
        ),
        active_event_id=event_id,
        active_scenario_id=scenario_id,
        active_scenario_name=scenario.scenario_name,
        save_error=None,
    )


@main.post("/events/<int:event_id>/rename")
def rename_saved_event(event_id: int):
    name = request.form.get("event_name", "")
    if not name.strip():
        return _render_saved_events(
            event_errors={event_id: "Event name is required."},
            event_values={event_id: name},
        )
    if not rename_event(event_id, name):
        abort(404)
    flash("Event name updated.", "success")
    return redirect(url_for("main.saved_events"))


@main.post("/events/<int:event_id>/scenarios/<int:scenario_id>/rename")
def rename_saved_scenario(event_id: int, scenario_id: int):
    try:
        stored_event_id, _, _ = load_event_scenario(scenario_id)
    except ValueError:
        abort(404)
    if stored_event_id != event_id:
        abort(404)
    name = request.form.get("scenario_name", "")
    if not name.strip():
        return _render_saved_events(
            scenario_errors={
                scenario_id: "Scenario name is required."
            },
            scenario_values={scenario_id: name},
        )
    try:
        renamed = rename_event_scenario(scenario_id, name)
    except ScenarioNameConflict as error:
        return _render_saved_events(
            scenario_errors={scenario_id: str(error)},
            scenario_values={scenario_id: name},
        )
    if not renamed:
        abort(404)
    flash("Scenario name updated.", "success")
    return redirect(url_for("main.saved_events"))


@main.post("/events/<int:event_id>/scenarios/<int:scenario_id>/delete")
def delete_saved_scenario(event_id: int, scenario_id: int):
    try:
        stored_event_id, _, scenario = load_event_scenario(scenario_id)
    except ValueError:
        abort(404)
    if stored_event_id != event_id:
        abort(404)
    if request.form.get("confirmed") != "yes":
        return _render_saved_events(
            scenario_errors={
                scenario_id: (
                    f'Confirm deletion of "{scenario.scenario_name}".'
                )
            }
        )
    try:
        deleted = delete_event_scenario(scenario_id)
    except FinalScenarioDeletionError as error:
        return _render_saved_events(
            scenario_errors={scenario_id: str(error)}
        )
    if not deleted:
        abort(404)
    flash("Scenario deleted.", "success")
    return redirect(url_for("main.saved_events"))


@main.post("/events/<int:event_id>/delete")
def delete_saved_event(event_id: int):
    events = list_saved_events()
    event = next((item for item in events if item["id"] == event_id), None)
    if event is None:
        abort(404)
    if request.form.get("confirmed") != "yes":
        return _render_saved_events(
            event_errors={
                event_id: (
                    f'Confirm deletion of "{event["event_name"]}" and '
                    f'all {event["scenario_count"]} saved scenarios.'
                )
            }
        )
    try:
        deleted = delete_event(event_id)
    except sqlite3.Error:
        return _render_saved_events(
            event_errors={
                event_id: "The event could not be deleted."
            }
        )
    if not deleted:
        abort(404)
    flash("Event and its saved scenarios deleted.", "success")
    return redirect(url_for("main.saved_events"))


@main.get("/comparison")
def comparison():
    """Keep the former navigation URL as a Saved Events alias."""
    return redirect(url_for("main.saved_events"))


def _render_saved_events(
    *,
    event_errors: dict | None = None,
    event_values: dict | None = None,
    scenario_errors: dict | None = None,
    scenario_values: dict | None = None,
):
    return render_template(
        "saved_events.html",
        active_page="saved_events",
        events=list_saved_events(),
        event_errors=event_errors or {},
        event_values=event_values or {},
        scenario_errors=scenario_errors or {},
        scenario_values=scenario_values or {},
    )
    delete_event,
    delete_event_scenario,
    list_saved_events,
    rename_event,
    rename_event_scenario,
