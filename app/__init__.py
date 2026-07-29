from flask import Flask


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    if test_config is not None:
        app.config.update(test_config)

    from app.routes import main

    app.register_blueprint(main)

    return app