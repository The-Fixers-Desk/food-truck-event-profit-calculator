from flask import Blueprint, render_template

main = Blueprint("main", __name__)


@main.route("/")
def calculator():
    """Display the calculator landing page."""
    return render_template("calculator.html")