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
    # Setup - create app with test config
    app = create_app()
    app.config.update({
        "TESTING": True,
        "JWT_SECRET_KEY": "test-secret-key",
    })
    
    # Use an in-memory database for tests
    test_db = Database(database_url="sqlite:///:memory:")
    app.config['database'] = test_db

    yield app

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
