from flask import Flask

from app.logging_config import configure_logging


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    if test_config is not None:
        app.config.update(test_config)

    configure_logging(app)

    from app.errors import register_error_handlers
    from app.routes import main

    app.register_blueprint(main)
    register_error_handlers(app)

    if app.config.get("TESTING"):

        @app.route("/test-error")
        def test_error():
            raise RuntimeError("Intentional test error.")

    return app