from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app


@pytest.fixture()
def app() -> Generator[Flask, None, None]:
    """Create a fresh Flask application for each test."""
    application = create_app(
        {
            "TESTING": True,
        }
    )

    yield application


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """Create a test client for making requests to the application."""
    return app.test_client()