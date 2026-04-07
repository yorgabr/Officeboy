"""
Pytest configuration - forces Access Simulator for stability.
Avoids COM crashes from real MS Access in automated tests.
"""
import sys
from pathlib import Path

import pytest

# Import simulator only
from .access_simulator import AccessSimulator


def pytest_configure(config):
    """Registers custom markers."""
    config.addinivalue_line("markers", "integration: Integration tests using Access Simulator")
    config.addinivalue_line("markers", "simulator: Tests for the simulator itself")


@pytest.fixture(scope="function")
def access_application():
    """
    Provides Access Simulator (never uses real Access to avoid COM crashes).
    Function scope ensures clean state for each test.
    """
    app = AccessSimulator()
    yield app
    try:
        app.Quit()
    except:
        pass


@pytest.fixture
def temporary_database(tmp_path, access_application):
    """Creates temporary database using simulator."""
    db_path = tmp_path / "test_integration.accdb"
    app = access_application
    
    try:
        app.NewCurrentDatabase(str(db_path))
        yield db_path
    finally:
        try:
            app.CloseCurrentDatabase()
            if db_path.exists():
                db_path.unlink()
        except:
            pass


@pytest.fixture
def sample_access_file(tmp_path):
    """Creates empty .accdb file for tests."""
    db_path = tmp_path / "sample.accdb"
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE IF NOT EXISTS dummy (id INT)")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def cli_runner():
    """Click CLI runner."""
    from click.testing import CliRunner
    return CliRunner()