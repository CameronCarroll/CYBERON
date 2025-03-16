import pytest
from app import create_app
from unittest.mock import patch

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app(testing=True)
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def mock_query_engine():
    """Mock the query engine for testing."""
    with patch('app.routes.api.query_engine') as mock:
        yield mock