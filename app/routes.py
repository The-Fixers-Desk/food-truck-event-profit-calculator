from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.business_defaults_form import defaults_to_form, validate_defaults_form
from app.database import load_business_defaults, save_business_defaults
from app.event_inputs_form import (
    blank_event_inputs_form,
    protection_reductions,
    validate_event_inputs,
    weather_allows_protection,
)

main = Blueprint("main", __name__)


@main.route("/", methods=("GET", "POST"))
def calculator():
    """Display the Event Inputs screen."""
    errors = {}
    if request.method == "POST":
        _, form_values, errors = validate_event_inputs(request.form)
    else:
        form_values = blank_event_inputs_form()

    return render_template(
        "calculator.html",
        active_page="calculator",
        form_values=form_values,
        errors=errors,
        protection_reductions=protection_reductions(form_values),
        show_event_protection=weather_allows_protection(form_values),
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
