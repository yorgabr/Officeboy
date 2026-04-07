"""
Pytest configuration with Access Simulator for integration tests.
"""
import sys
from pathlib import Path

import pytest

from .access_simulator import AccessSimulator


def pytest_configure(config):
    """Registers custom markers."""
    config.addinivalue_line("markers", "integration: Integration tests using Access Simulator")
    config.addinivalue_line("markers", "unit: Fast unit tests")


@pytest.fixture(scope="function")
def access_application():
    """Provides Access Simulator (stable, no COM crashes)."""
    app = AccessSimulator()
    yield app
    try:
        app.Quit()
    except:
        pass


@pytest.fixture
def temporary_database(tmp_path, access_application):
    """Creates temporary database using simulator."""
    db_path = tmp_path / "test.accdb"
    
    try:
        access_application.NewCurrentDatabase(str(db_path))
        yield db_path
    finally:
        try:
            access_application.CloseCurrentDatabase()
            if db_path.exists():
                db_path.unlink()
        except:
            pass


@pytest.fixture
def cli_runner():
    """Click CLI runner."""
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def mock_fs():
    """Mock file system."""
    from .test_disassembler_di import MockFileSystem
    return MockFileSystem()


@pytest.fixture
def mock_hash_index():
    """Mock hash index."""
    from .test_disassembler_di import MockHashIndex
    return MockHashIndex()