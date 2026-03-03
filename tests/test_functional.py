"""Functional tests for Officeboy CLI."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.functional
class TestCliFunctional:
    """Functional tests using actual CLI invocation."""
    
    def test_cli_help_command(self):
        """Test CLI help command."""
        result = subprocess.run(
            [sys.executable, "-m", "officeboy.cli", "--help"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert "Officeboy" in result.stdout
    
    def test_cli_version_command(self):
        """Test CLI version command."""
        result = subprocess.run(
            [sys.executable, "-m", "officeboy.cli", "--version"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert "version" in result.stdout.lower()


@pytest.mark.integration
@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
class TestIntegration:
    """Integration tests requiring MS Access."""
    
    def test_full_export_import_cycle(self, tmp_path):
        """Test complete export and import cycle."""
        # This test requires actual MS Access installation
        # and would be skipped in CI environments without Access
        
        access_file = tmp_path / "test_integration.accdb"
        source_dir = tmp_path / "src"
        
        # Create test database (would need actual Access)
        # For now, this serves as a placeholder for integration tests
        pytest.skip("MS Access not available in test environment")