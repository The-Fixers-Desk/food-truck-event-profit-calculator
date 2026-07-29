from flask import Blueprint, render_template

main = Blueprint("main", __name__)


@main.route("/")
def calculator():
    """Display the Event Calculator screen."""
    return render_template(
        "calculator.html",
        active_page="calculator",
    )


@main.route("/defaults")
def defaults():
    """Display the Defaults screen."""
    return render_template(
        "defaults.html",
        active_page="defaults",
    )


@main.route("/comparison")
def comparison():
    """Display the Comparison screen."""
    return render_template(
        "comparison.html",
        active_page="comparison",
    )