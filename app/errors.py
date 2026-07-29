from flask import Flask, render_template
from werkzeug.exceptions import InternalServerError, NotFound


def register_error_handlers(app: Flask) -> None:
    """Register application-wide error handlers."""

    @app.errorhandler(NotFound)
    def handle_not_found(error: NotFound):
        app.logger.warning(
            "Page not found: %s",
            error.description,
        )

        return render_template(
            "errors/404.html",
            active_page=None,
        ), 404

    @app.errorhandler(InternalServerError)
    def handle_internal_server_error(error: InternalServerError):
        if error.original_exception is not None:
            app.logger.error(
                "Unhandled application error.",
                exc_info=error.original_exception,
            )
        else:
            app.logger.error("Internal server error.")

        return render_template(
            "errors/500.html",
            active_page=None,
        ), 500