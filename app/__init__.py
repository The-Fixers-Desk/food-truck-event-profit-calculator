from flask import Flask


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    from app.routes import main
    app.register_blueprint(main)

    return app