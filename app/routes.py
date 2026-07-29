from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.business_defaults_form import defaults_to_form, validate_defaults_form
from app.database import load_business_defaults, save_business_defaults

main = Blueprint("main", __name__)


@main.route("/")
def calculator():
    """Display the Event Calculator screen."""
    return render_template(
        "calculator.html",
        active_page="calculator",
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
