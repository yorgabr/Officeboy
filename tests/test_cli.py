"""Unit tests for CLI module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from officeboy.cli import cli, main


class TestCliMain:
    """Tests for main CLI entry point."""
    
    def test_cli_version_flag(self):
        """Test --version flag displays version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        
        assert result.exit_code == 0
        assert "Officeboy version" in result.output
    
    def test_cli_help_flag(self):
        """Test --help flag displays help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "Officeboy" in result.output
        assert "MS Access" in result.output
    
    def test_cli_no_command_shows_help(self):
        """Test running CLI without command shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, [])
        
        assert result.exit_code == 0
        assert "Usage:" in result.output
    
    def test_cli_verbose_flag(self):
        """Test --verbose flag enables debug logging."""
        runner = CliRunner()
        
        with patch("officeboy.cli.setup_logging") as mock_setup:
            runner.invoke(cli, ["--verbose", "--version"])
            
            mock_setup.assert_called_once_with(True)
    
    def test_main_exits_on_non_windows(self):
        """Test main() exits on non-Windows platforms."""
        with patch("os.name", "posix"):
            with patch("sys.exit") as mock_exit:
                with patch("click.echo") as mock_echo:
                    main()
                    if sys.platform != "win32":
                        mock_exit.assert_called_once_with(1)
                    else:
                        # In Windows, the process is different - it only checks that 
                        # it was called with 1 at some point.
                        mock_exit.assert_any_call(1)
                    mock_echo.assert_called()


class TestDisassemblyCommand:
    """Tests for disassembly command."""
    
    def test_disassembly_missing_file(self):
        """Test disassembly fails with missing file."""
        runner = CliRunner()
        result = runner.invoke(cli, ["disassembly", "nonexistent.accdb", "./src"])
        
        assert result.exit_code != 0
        assert "does not exist" in result.output or "Invalid value" in result.output
    
    def test_disassembly_success(self, tmp_path):
        """Test successful disassembly."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        source_dir = tmp_path / "src"
        
        runner = CliRunner()
        
        with patch("officeboy.cli.AccessExporter") as mock_exporter:
            mock_instance = MagicMock()
            mock_instance.export_all.return_value = MagicMock(
                total_exported=5,
                forms=1,
                reports=1,
                modules=1,
                queries=1,
                macros=1,
                tables=0,
                skipped=0,
            )
            mock_exporter.return_value = mock_instance
            
            result = runner.invoke(cli, [
                "disassembly",
                str(access_file),
                str(source_dir),
            ])
            
            assert result.exit_code == 0
            assert "Export completed successfully" in result.output
            assert "5 objects" in result.output
    
    def test_disassembly_with_force_flag(self, tmp_path):
        """Test disassembly with --force flag."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        source_dir = tmp_path / "src"
        
        runner = CliRunner()
        
        with patch("officeboy.cli.AccessExporter") as mock_exporter:
            mock_instance = MagicMock()
            mock_instance.export_all.return_value = MagicMock(
                total_exported=0,
                skipped=0,
            )
            mock_exporter.return_value = mock_instance
            
            result = runner.invoke(cli, [
                "disassembly",
                "--force",
                str(access_file),
                str(source_dir),
            ])
            
            mock_exporter.assert_called_once()
            call_kwargs = mock_exporter.call_args.kwargs
            assert call_kwargs["force_export"] is True


class TestAssemblyCommand:
    """Tests for assembly command."""
    
    def test_assembly_file_exists_no_overwrite(self, tmp_path):
        """Test assembly fails when file exists without --overwrite."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        (source_dir / "dummy.txt").touch()
        
        access_file = tmp_path / "test.accdb"
        access_file.touch()  # File exists
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            "assembly",
            str(source_dir),
            str(access_file),
        ])
        
        assert result.exit_code == 1
        assert "File exists" in result.output
    
    def test_assembly_success(self, tmp_path):
        """Test successful assembly."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        access_file = tmp_path / "test.accdb"
        
        runner = CliRunner()
        
        with patch("officeboy.cli.AccessImporter") as mock_importer:
            mock_instance = MagicMock()
            mock_instance.import_all.return_value = MagicMock(
                total_imported=3,
                forms=1,
                reports=1,
                modules=1,
            )
            mock_importer.return_value = mock_instance
            
            result = runner.invoke(cli, [
                "assembly",
                str(source_dir),
                str(access_file),
            ])
            
            assert result.exit_code == 0
            assert "Assembly completed successfully" in result.output
    
    def test_assembly_with_template(self, tmp_path):
        """Test assembly with template."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        access_file = tmp_path / "output.accdb"
        template = tmp_path / "template.accdb"
        template.touch()
        
        runner = CliRunner()
        
        with patch("officeboy.cli.AccessImporter") as mock_importer:
            mock_instance = MagicMock()
            mock_instance.import_all.return_value = MagicMock(total_imported=1)
            mock_importer.return_value = mock_instance
            
            result = runner.invoke(cli, [
                "assembly",
                "--template", str(template),
                str(source_dir),
                str(access_file),
            ])
            
            assert result.exit_code == 0
            call_kwargs = mock_importer.call_args.kwargs
            assert call_kwargs["template"] == template


class TestMakeUnitTestsCommand:
    """Tests for make-unit-tests command."""
    
    def test_make_unit_tests_success(self, tmp_path):
        """Test successful unit test generation."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        output_dir = tmp_path / "tests"
        
        runner = CliRunner()
        
        with patch("officeboy.cli.UnitTestGenerator") as mock_gen:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = MagicMock(
                module_count=2,
                test_count=10,
            )
            mock_gen.return_value = mock_instance
            
            result = runner.invoke(cli, [
                "make-unit-tests",
                str(access_file),
                "--output", str(output_dir),
            ])
            
            assert result.exit_code == 0
            assert "Unit test Add-in generated successfully" in result.output
            assert "2 test modules" in result.output
            assert "10 total tests" in result.output
    
    def test_make_unit_tests_with_addin_name(self, tmp_path):
        """Test unit test generation with custom add-in name."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        
        runner = CliRunner()
        
        with patch("officeboy.cli.UnitTestGenerator") as mock_gen:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = MagicMock(
                module_count=1,
                test_count=5,
            )
            mock_gen.return_value = mock_instance
            
            runner.invoke(cli, [
                "make-unit-tests",
                "--addin-name", "CustomTests",
                str(access_file),
            ])
            
            call_kwargs = mock_gen.call_args.kwargs
            assert call_kwargs["addin_name"] == "CustomTests"


class TestMakeFunctionalTestsCommand:
    """Tests for make-functional-tests command."""
    
    def test_make_functional_tests_success(self, tmp_path):
        """Test successful functional test generation."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        output_dir = tmp_path / "robot"
        
        runner = CliRunner()
        
        with patch("officeboy.cli.FunctionalTestGenerator") as mock_gen:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = MagicMock(
                spec_count=3,
                form_count=3,
                test_case_count=15,
            )
            mock_gen.return_value = mock_instance
            
            result = runner.invoke(cli, [
                "make-functional-tests",
                str(access_file),
                "--output", str(output_dir),
            ])
            
            assert result.exit_code == 0
            assert "Functional tests generated successfully" in result.output
            assert "3 test specifications" in result.output
            assert "15" in result.output
    
    def test_make_functional_tests_with_library(self, tmp_path):
        """Test functional test generation with custom library."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        
        runner = CliRunner()
        
        with patch("officeboy.cli.FunctionalTestGenerator") as mock_gen:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = MagicMock(
                spec_count=1,
                form_count=1,
                test_case_count=5,
            )
            mock_gen.return_value = mock_instance
            
            runner.invoke(cli, [
                "make-functional-tests",
                "--library", "SeleniumLibrary",
                str(access_file),
            ])
            
            call_kwargs = mock_gen.call_args.kwargs
            assert call_kwargs["library"] == "SeleniumLibrary"


class TestErrorHandling:
    """Tests for CLI error handling."""
    
    def test_disassembly_exception_handling(self, tmp_path):
        """Test disassembly handles exceptions gracefully."""
        access_file = tmp_path / "test.accdb"
        access_file.touch()
        source_dir = tmp_path / "src"
        
        runner = CliRunner()
        
        with patch("officeboy.cli.AccessExporter") as mock_exporter:
            mock_exporter.side_effect = Exception("Access error")
            
            result = runner.invoke(cli, [
                "disassembly",
                str(access_file),
                str(source_dir),
            ])
            
            assert result.exit_code == 1
            assert "Error:" in result.output
    
    def test_assembly_exception_handling(self, tmp_path):
        """Test assembly handles exceptions gracefully."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        access_file = tmp_path / "test.accdb"
        
        runner = CliRunner()
        
        with patch("officeboy.cli.AccessImporter") as mock_importer:
            mock_importer.side_effect = Exception("Import error")
            
            result = runner.invoke(cli, [
                "assembly",
                str(source_dir),
                str(access_file),
            ])
            
            assert result.exit_code == 1
            assert "Error:" in result.output