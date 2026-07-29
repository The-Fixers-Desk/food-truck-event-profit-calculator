from collections.abc import Generator
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app


@pytest.fixture()
def database_path(tmp_path: Path) -> Path:
    """Return an isolated persistent database path."""
    return tmp_path / "test.db"


@pytest.fixture()
def app(database_path: Path) -> Generator[Flask, None, None]:
    """Create a fresh Flask application for each test."""
    application = create_app(
        {
            "DATABASE": database_path,
            "SECRET_KEY": "test",
            "TESTING": True,
            "PROPAGATE_EXCEPTIONS": False,
        }
    )

    yield application


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """Create a test client for making requests to the application."""
    return app.test_client()
