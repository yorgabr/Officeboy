"""Pytest configuration and fixtures."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Mock win32com for non-Windows platforms
if sys.platform != "win32":
    sys.modules["win32com"] = MagicMock()
    sys.modules["win32com.client"] = MagicMock()


@pytest.fixture
def temp_dir(tmp_path):
    """Provide temporary directory."""
    return tmp_path


@pytest.fixture
def mock_access_app():
    """Provide mocked Access application."""
    with patch("officeboy.access.application.AccessApplication") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def sample_access_file(tmp_path):
    """Create sample Access file path."""
    access_file = tmp_path / "test.accdb"
    access_file.touch()
    return access_file


@pytest.fixture
def sample_source_dir(tmp_path):
    """Create sample source directory structure."""
    source_dir = tmp_path / "src"
    
    # Create subdirectories for object types
    for obj_type in ["Forms", "Reports", "Modules", "Queries", "Macros", "Tables"]:
        (source_dir / obj_type).mkdir(parents=True)
    
    return source_dir