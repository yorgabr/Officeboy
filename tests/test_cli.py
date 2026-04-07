"""
CLI tests.
"""
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from officeboy.cli import cli, main


pytestmark = pytest.mark.unit


class TestCliMain:
    """Tests for main CLI entry point."""

    def test_cli_version_flag(self, cli_runner):
        """Test --version flag displays version."""
        result = cli_runner.invoke(cli, ["--version"])
        
        assert result.exit_code == 0
        assert "Officeboy version" in result.output

    def test_cli_help_flag(self, cli_runner):
        """Test --help flag displays help."""
        result = cli_runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "Officeboy" in result.output
        assert "MS Access" in result.output

    def test_cli_no_command_shows_help(self, cli_runner):
        """Test running CLI without command shows help."""
        result = cli_runner.invoke(cli, [])
        
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_cli_verbose_flag(self, cli_runner, mocker):
        """Test --verbose flag enables debug logging."""
        mock_setup = mocker.patch('officeboy.cli.setup_logging')
        
        cli_runner.invoke(cli, ["--verbose", "--version"])
        
        mock_setup.assert_called_once_with(True)

    def test_main_exits_on_non_windows(self, mocker, monkeypatch):
        """Test main() exits on non-Windows platforms."""
        monkeypatch.setattr('os.name', 'posix')
        mock_exit = mocker.patch('sys.exit')
        mock_echo = mocker.patch('click.echo')
        
        main()
        
        # On Windows, this will be called twice (once with 1, once with 0)
        # We just verify it was called with error code 1 at some point
        mock_exit.assert_any_call(1)
        mock_echo.assert_called()


class TestDisassemblyCommand:
    """Tests for disassembly command using pytest-mock."""

    def test_disassembly_missing_file(self, cli_runner):
        """Test disassembly fails with missing file."""
        result = cli_runner.invoke(cli, ["disassembly", "nonexistent.accdb", "./src"])
        
        assert result.exit_code != 0
        assert "does not exist" in result.output or "Invalid value" in result.output

    def test_disassembly_success(self, cli_runner, tmp_path, mocker):
        """Test successful disassembly."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        source_dir = tmp_path / "src"
        
        # Create mock result object using pytest-mock
        mock_result = mocker.MagicMock()
        mock_result.total_exported = 5
        mock_result.forms = 1
        mock_result.reports = 1
        mock_result.modules = 1
        mock_result.queries = 1
        mock_result.macros = 1
        mock_result.tables = 0
        mock_result.skipped = 0
        
        mock_exporter_class = mocker.patch('officeboy.cli.AccessExporter')
        mock_instance = mocker.MagicMock()
        mock_instance.export_all.return_value = mock_result
        mock_exporter_class.return_value = mock_instance
        
        result = cli_runner.invoke(cli, [
            "disassembly",
            str(access_file),
            str(source_dir),
        ])
        
        assert result.exit_code == 0
        assert "Export completed successfully" in result.output
        assert "5 objects" in result.output

    def test_disassembly_with_force_flag(self, cli_runner, tmp_path, mocker):
        """Test disassembly with --force flag."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        source_dir = tmp_path / "src"
        
        mock_exporter_class = mocker.patch('officeboy.cli.AccessExporter')
        mock_instance = mocker.MagicMock()
        mock_instance.export_all.return_value = mocker.MagicMock(
            total_exported=0,
            skipped=0,
        )
        mock_exporter_class.return_value = mock_instance
        
        result = cli_runner.invoke(cli, [
            "disassembly",
            "--force",
            str(access_file),
            str(source_dir),
        ])
        
        mock_exporter_class.assert_called_once()
        call_kwargs = mock_exporter_class.call_args.kwargs
        assert call_kwargs["force_export"] is True


class TestAssemblyCommand:
    """Tests for assembly command."""

    def test_assembly_file_exists_no_overwrite(self, cli_runner, tmp_path):
        """Test assembly fails when file exists without --overwrite."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        (source_dir / "dummy.txt").touch()
        
        access_file = tmp_path / "test.accdb"
        access_file.touch()  # File exists
        
        result = cli_runner.invoke(cli, [
            "assembly",
            str(source_dir),
            str(access_file),
        ])
        
        assert result.exit_code == 1
        assert "File exists" in result.output

    def test_assembly_success(self, cli_runner, tmp_path, mocker):
        """Test successful assembly."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        access_file = tmp_path / "test.accdb"
        
        mock_result = mocker.MagicMock()
        mock_result.total_imported = 3
        mock_result.forms = 1
        mock_result.reports = 1
        mock_result.modules = 1
        
        mock_importer_class = mocker.patch('officeboy.cli.AccessImporter')
        mock_instance = mocker.MagicMock()
        mock_instance.import_all.return_value = mock_result
        mock_importer_class.return_value = mock_instance
        
        result = cli_runner.invoke(cli, [
            "assembly",
            str(source_dir),
            str(access_file),
        ])
        
        assert result.exit_code == 0
        assert "Assembly completed successfully" in result.output

    def test_assembly_with_template(self, cli_runner, tmp_path, mocker):
        """Test assembly with template."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        access_file = tmp_path / "output.accdb"
        template = tmp_path / "template.accdb"
        template.touch()
        
        mock_importer_class = mocker.patch('officeboy.cli.AccessImporter')
        mock_instance = mocker.MagicMock()
        mock_instance.import_all.return_value = mocker.MagicMock(total_imported=1)
        mock_importer_class.return_value = mock_instance
        
        result = cli_runner.invoke(cli, [
            "assembly",
            "--template", str(template),
            str(source_dir),
            str(access_file),
        ])
        
        assert result.exit_code == 0
        call_kwargs = mock_importer_class.call_args.kwargs
        assert call_kwargs["template"] == template


class TestMakeUnitTestsCommand:
    """Tests for make-unit-tests command."""

    def test_make_unit_tests_success(self, cli_runner, tmp_path, mocker):
        """Test successful unit test generation."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        output_dir = tmp_path / "tests"
        
        mock_result = mocker.MagicMock()
        mock_result.module_count = 2
        mock_result.test_count = 10
        
        mock_gen_class = mocker.patch('officeboy.cli.UnitTestGenerator')
        mock_instance = mocker.MagicMock()
        mock_instance.generate.return_value = mock_result
        mock_gen_class.return_value = mock_instance
        
        result = cli_runner.invoke(cli, [
            "make-unit-tests",
            str(access_file),
            "--output", str(output_dir),
        ])
        
        assert result.exit_code == 0
        assert "Unit test Add-in generated successfully" in result.output
        assert "2 test modules" in result.output
        assert "10 total tests" in result.output

    def test_make_unit_tests_with_addin_name(self, cli_runner, tmp_path, mocker):
        """Test unit test generation with custom add-in name."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        
        mock_gen_class = mocker.patch('officeboy.cli.UnitTestGenerator')
        mock_instance = mocker.MagicMock()
        mock_instance.generate.return_value = mocker.MagicMock(
            module_count=1,
            test_count=5,
        )
        mock_gen_class.return_value = mock_instance
        
        cli_runner.invoke(cli, [
            "make-unit-tests",
            "--addin-name", "CustomTests",
            str(access_file),
        ])
        
        call_kwargs = mock_gen_class.call_args.kwargs
        assert call_kwargs["addin_name"] == "CustomTests"


class TestMakeFunctionalTestsCommand:
    """Tests for make-functional-tests command."""

    def test_make_functional_tests_success(self, cli_runner, tmp_path, mocker):
        """Test successful functional test generation."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        output_dir = tmp_path / "robot"
        
        mock_result = mocker.MagicMock()
        mock_result.spec_count = 3
        mock_result.form_count = 3
        mock_result.test_case_count = 15
        
        mock_gen_class = mocker.patch('officeboy.cli.FunctionalTestGenerator')
        mock_instance = mocker.MagicMock()
        mock_instance.generate.return_value = mock_result
        mock_gen_class.return_value = mock_instance
        
        result = cli_runner.invoke(cli, [
            "make-functional-tests",
            str(access_file),
            "--output", str(output_dir),
        ])
        
        assert result.exit_code == 0
        assert "Functional tests generated successfully" in result.output
        assert "3 test specifications" in result.output
        assert "15" in result.output

    def test_make_functional_tests_with_library(self, cli_runner, tmp_path, mocker):
        """Test functional test generation with custom library."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        
        mock_gen_class = mocker.patch('officeboy.cli.FunctionalTestGenerator')
        mock_instance = mocker.MagicMock()
        mock_instance.generate.return_value = mocker.MagicMock(
            spec_count=1,
            form_count=1,
            test_case_count=5,
        )
        mock_gen_class.return_value = mock_instance
        
        cli_runner.invoke(cli, [
            "make-functional-tests",
            "--library", "SeleniumLibrary",
            str(access_file),
        ])
        
        call_kwargs = mock_gen_class.call_args.kwargs
        assert call_kwargs["library"] == "SeleniumLibrary"


class TestErrorHandling:
    """Tests for CLI error handling."""

    def test_disassembly_exception_handling(self, cli_runner, tmp_path, mocker):
        """Test disassembly handles exceptions gracefully."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        source_dir = tmp_path / "src"
        
        mock_exporter_class = mocker.patch('officeboy.cli.AccessExporter')
        mock_exporter_class.side_effect = Exception("Access error")
        
        result = cli_runner.invoke(cli, [
            "disassembly",
            str(access_file),
            str(source_dir),
        ])
        
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_assembly_exception_handling(self, cli_runner, tmp_path, mocker):
        """Test assembly handles exceptions gracefully."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        access_file = tmp_path / "test.accdb"
        
        mock_importer_class = mocker.patch('officeboy.cli.AccessImporter')
        mock_importer_class.side_effect = Exception("Import error")
        
        result = cli_runner.invoke(cli, [
            "assembly",
            str(source_dir),
            str(access_file),
        ])
        
        assert result.exit_code == 1
        assert "Error:" in result.output