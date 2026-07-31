import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask


def configure_logging(app: Flask) -> None:
    """Configure local rotating application logs."""
    paths = app.config.get("DATA_PATHS")
    log_directory = paths.logs if paths is not None else Path(app.instance_path) / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)

    log_file = log_directory / "application.log"

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    app.logger.setLevel(logging.INFO)

    if not any(
        isinstance(handler, RotatingFileHandler)
        for handler in app.logger.handlers
    ):
        app.logger.addHandler(file_handler)

    app.logger.info("Application logging initialized.")
