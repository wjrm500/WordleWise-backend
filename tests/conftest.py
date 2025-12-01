import pytest
import sys
import os

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.app import create_app
from database.Database import Database

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    test_config = {
        "TESTING": True,
        "JWT_SECRET_KEY": "test-secret-key",
        "DATABASE_URL": "sqlite:///:memory:"
    }
    app = create_app(test_config)
    
    yield app

    # Cleanup session after test
    app.config['database'].session.remove()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's CLI commands."""
    return app.test_cli_runner()

@pytest.fixture
def db(app):
    """Get the database instance."""
    return app.config['database']
