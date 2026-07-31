from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from app.business_defaults_form import defaults_to_form, validate_defaults_form
from app.database import load_business_defaults, save_business_defaults
from app.event_inputs_form import (
    blank_event_inputs_form,
    calculation_result_data,
    calculate_demand_preview,
    protection_reductions,
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
    if request.method == "POST":
        identity, form_values, errors, result = (
            validate_and_calculate_event_analysis(request.form)
        )
        if result is not None:
            workspace = True
            analysis = calculation_result_data(result)
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


@main.route("/comparison")
def comparison():
    """Display the Comparison screen."""
    return render_template(
        "comparison.html",
        active_page="comparison",
    )
