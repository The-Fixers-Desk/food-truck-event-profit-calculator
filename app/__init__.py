from flask import Flask, session
from pathlib import Path
import sqlite3

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
        MAX_CONTENT_LENGTH=101 * 1024 * 1024,
        SECRET_KEY="development-only",
    )

    if test_config is not None:
        app.config.update(test_config)

    from app.data_paths import ApplicationDataPaths

    if test_config and "DATA_ROOT" in test_config and "DATABASE" not in test_config:
        app.config["DATABASE"] = Path(test_config["DATA_ROOT"]) / "app.db"
    app.config["DATA_PATHS"] = ApplicationDataPaths.from_config(app.config)

    configure_logging(app)

    from app.errors import register_error_handlers
    from app.routes import main

    app.register_blueprint(main)
    register_error_handlers(app)

    from app.database import close_database, initialize_database

    app.teardown_appcontext(close_database)
    from app.migrations import DatabaseMigrationError

    app.config["RECOVERY_MODE"] = False
    with app.app_context():
        try:
            initialize_database()
        except (DatabaseMigrationError, sqlite3.Error):
            app.logger.exception("Customer database could not be opened.")
            close_database()
            app.config["RECOVERY_MODE"] = True

    @app.context_processor
    def application_state():
        from app.database import business_defaults_setup_is_complete

        return {
            "business_defaults_setup_complete": (
                not app.config.get("RECOVERY_MODE")
                and (
                    not app.config.get("ENFORCE_SETUP", True)
                    or business_defaults_setup_is_complete()
                )
            ),
            "onboarding_deferred": bool(session.get("onboarding_deferred")),
        }

    if app.config.get("TESTING"):

        @app.route("/test-system-states")
        def test_system_states():
            from flask import render_template

            return render_template(
                "system_states.html",
                active_page="dashboard",
            )

        @app.route("/test-error")
        def test_error():
            raise RuntimeError("Intentional test error.")

    return app
