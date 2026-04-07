"""
CLI tests without real Access or filesystem.
"""
import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import MagicMock

from officeboy.cli import cli, CLIContext
from officeboy.core.disassembler import DisassemblyResult
from officeboy.core.assembler import AssemblyResult


class MockDisassembler:
    """Mock disassembler for testing."""
    
    def __init__(self, **kwargs):
        self.index_manager = kwargs.get('index_manager')
        self.disassemble_called = False
        self.close_called = False
    
    def disassemble(self, db_path, output_dir, force=False, progress_callback=None):
        self.disassemble_called = True
        return DisassemblyResult(
            total_disassembled=5,
            forms=2,
            reports=1,
            modules=1,
            queries=1,
            skipped=0
        )
    
    def close(self):
        self.close_called = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class MockAssembler:
    """Mock assembler for testing."""
    
    def __init__(self, **kwargs):
        self.assemble_called = False
        self.close_called = False
    
    def assemble(self, source_dir, db_path, template=None, overwrite=False, progress_callback=None):
        self.assemble_called = True
        return AssemblyResult(
            total_assembled=3,
            forms=1,
            reports=1,
            modules=1
        )
    
    def close(self):
        self.close_called = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class MockUnitTestGenerator:
    """Mock unit test generator."""
    
    def generate(self, db_path, output_dir, addin_name="Test"):
        result = MagicMock()
        result.test_count = 10
        result.module_count = 2
        return result


class MockFunctionalTestGenerator:
    """Mock functional test generator."""
    
    def generate(self, db_path, output_dir, library="FlaUI"):
        result = MagicMock()
        result.test_case_count = 15
        result.form_count = 5
        return result


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def mock_context():
    return CLIContext(
        disassembler_class=MockDisassembler,
        assembler_class=MockAssembler,
        unit_gen_class=MockUnitTestGenerator,
        functional_gen_class=MockFunctionalTestGenerator
    )


class TestDisassembleCommand:
    """Tests for disassemble command."""
    
    def test_disassemble_success(self, cli_runner, mock_context, tmp_path):
        """Test successful disassembly."""
        db_file = tmp_path / "test.accdb"
        db_file.touch()
        output_dir = tmp_path / "src"
        
        result = cli_runner.invoke(cli, [
            'disassemble',
            str(db_file),
            str(output_dir)
        ], obj={'context': mock_context})
        
        assert result.exit_code == 0
        assert "Disassembly completed" in result.output
        assert "5 objects" in result.output
    
    def test_disassemble_with_force(self, cli_runner, mock_context, tmp_path):
        """Test disassembly with --force flag."""
        db_file = tmp_path / "test.accdb"
        db_file.touch()
        output_dir = tmp_path / "src"
        
        result = cli_runner.invoke(cli, [
            'disassemble',
            '--force',
            str(db_file),
            str(output_dir)
        ], obj={'context': mock_context})
        
        assert result.exit_code == 0
        assert "Disassembly completed" in result.output
    
    def test_disassemble_with_verbose(self, cli_runner, mock_context, tmp_path):
        """Test disassembly with --verbose flag."""
        db_file = tmp_path / "test.accdb"
        db_file.touch()
        output_dir = tmp_path / "src"
        
        result = cli_runner.invoke(cli, [
            '--verbose',
            'disassemble',
            str(db_file),
            str(output_dir)
        ], obj={'context': mock_context})
        
        assert result.exit_code == 0
    
    def test_disassemble_missing_file(self, cli_runner, mock_context, tmp_path):
        """Test disassembly with missing database."""
        result = cli_runner.invoke(cli, [
            'disassemble',
            str(tmp_path / "missing.accdb"),
            str(tmp_path / "src")
        ], obj={'context': mock_context})
        
        assert result.exit_code != 0
        assert "does not exist" in result.output or "Invalid value" in result.output


class TestAssembleCommand:
    """Tests for assemble command."""
    
    def test_assemble_success(self, cli_runner, mock_context, tmp_path):
        """Test successful assembly."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        db_file = tmp_path / "output.accdb"
        
        result = cli_runner.invoke(cli, [
            'assemble',
            str(source_dir),
            str(db_file)
        ], obj={'context': mock_context})
        
        assert result.exit_code == 0
        assert "Assembly completed" in result.output
        assert "3 objects" in result.output
    
    def test_assemble_file_exists_no_overwrite(self, cli_runner, mock_context, tmp_path):
        """Test assembly fails when file exists without --overwrite."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        db_file = tmp_path / "existing.accdb"
        db_file.touch()
        
        result = cli_runner.invoke(cli, [
            'assemble',
            str(source_dir),
            str(db_file)
        ], obj={'context': mock_context})
        
        assert result.exit_code == 1
        assert "File exists" in result.output
    
    def test_assemble_with_overwrite(self, cli_runner, mock_context, tmp_path):
        """Test assembly with --overwrite flag."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        db_file = tmp_path / "existing.accdb"
        db_file.touch()
        
        result = cli_runner.invoke(cli, [
            'assemble',
            '--overwrite',
            str(source_dir),
            str(db_file)
        ], obj={'context': mock_context})
        
        assert result.exit_code == 0
        assert "Assembly completed" in result.output
    
    def test_assemble_with_template(self, cli_runner, mock_context, tmp_path):
        """Test assembly with --template flag."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        template = tmp_path / "template.accdb"
        template.touch()
        db_file = tmp_path / "output.accdb"
        
        result = cli_runner.invoke(cli, [
            'assemble',
            '--template', str(template),
            str(source_dir),
            str(db_file)
        ], obj={'context': mock_context})
        
        assert result.exit_code == 0


class TestMakeUnitTestsCommand:
    """Tests for make-unit-tests command."""
    
    def test_make_unit_tests_success(self, cli_runner, mock_context, tmp_path):
        """Test successful unit test generation."""
        db_file = tmp_path / "test.accdb"
        db_file.touch()
        output_dir = tmp_path / "tests"
        
        result = cli_runner.invoke(cli, [
            'make-unit-tests',
            str(db_file),
            '--output', str(output_dir),
            '--addin-name', 'MyTests'
        ], obj={'context': mock_context})
        
        assert result.exit_code == 0
        assert "Generated 10 tests" in result.output


class TestMakeFunctionalTestsCommand:
    """Tests for make-functional-tests command."""
    
    def test_make_functional_tests_success(self, cli_runner, mock_context, tmp_path):
        """Test successful functional test generation."""
        db_file = tmp_path / "test.accdb"
        db_file.touch()
        output_dir = tmp_path / "robot"
        
        result = cli_runner.invoke(cli, [
            'make-functional-tests',
            str(db_file),
            '--output', str(output_dir),
            '--library', 'SeleniumLibrary'
        ], obj={'context': mock_context})
        
        assert result.exit_code == 0
        assert "Generated 15 test cases" in result.output


class TestVersionCommand:
    """Tests for version command."""
    
    def test_version(self, cli_runner):
        """Test version display."""
        result = cli_runner.invoke(cli, ['version'])
        
        assert result.exit_code == 0
        assert "Officeboy version" in result.output


class TestMainEntry:
    """Tests for main entry point."""
    
    def test_main_windows(self, cli_runner):
        """Test main on Windows."""
        import sys
        if sys.platform == 'win32':
            result = cli_runner.invoke(cli, ['--help'])
            assert result.exit_code == 0
    
    def test_cli_no_command(self, cli_runner):
        """Test CLI without command shows help."""
        result = cli_runner.invoke(cli, [])
        
        assert result.exit_code == 0
        assert "Usage:" in result.output


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_disassemble_error_handling(self, cli_runner, mock_context, tmp_path):
        """Test disassemble handles errors gracefully."""
        # Create a mock that raises exception
        class FailingDisassembler:
            def __init__(self, **kwargs): pass
            def disassemble(self, **kwargs): raise Exception("COM Error")
            def close(self): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
        
        context = CLIContext(
            disassembler_class=FailingDisassembler,
            assembler_class=MockAssembler
        )
        
        db_file = tmp_path / "test.accdb"
        db_file.touch()
        
        result = cli_runner.invoke(cli, [
            'disassemble',
            str(db_file),
            str(tmp_path / "src")
        ], obj={'context': context})
        
        assert result.exit_code == 1
        assert "Error:" in result.output