from flask import Flask
from pathlib import Path

from app.logging_config import configure_logging


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        instance_relative_config=True,
    )
    app.config.from_mapping(
        DATABASE=Path(app.root_path).parent / "data" / "app.db",
        ENFORCE_SETUP=True,
        SECRET_KEY="development-only",
    )

    if test_config is not None:
        app.config.update(test_config)

    configure_logging(app)

    from app.errors import register_error_handlers
    from app.routes import main

    app.register_blueprint(main)
    register_error_handlers(app)

    from app.database import close_database, initialize_database

    app.teardown_appcontext(close_database)
    with app.app_context():
        initialize_database()

    @app.context_processor
    def application_state():
        from app.database import business_defaults_setup_is_complete

        return {
            "business_defaults_setup_complete": (
                not app.config.get("ENFORCE_SETUP", True)
                or business_defaults_setup_is_complete()
            )
        }

    if app.config.get("TESTING"):

        @app.route("/test-error")
        def test_error():
            raise RuntimeError("Intentional test error.")

    return app
