"""
Unit tests for exporter.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from officeboy.core.exporter import Exporter, ExportResult, ObjectType
from officeboy.access.application import AccessApplicationInterface


class MockAccessApp:
    """Mock Access application for testing."""
    
    Version = "16.0"
    
    def __init__(self):
        self.CurrentProject = MagicMock()
        self.Forms = []
        self.Reports = []
        self.Modules = []
        self.Queries = []
        self.Macros = []
        self.Tables = []
        self.DoCmd = MagicMock()
    
    def NewCurrentDatabase(self, path):
        pass
    
    def OpenCurrentDatabase(self, path):
        pass
    
    def CloseCurrentDatabase(self):
        pass
    
    def Quit(self):
        pass
    
    def SaveAsText(self, obj_type, name, path):
        Path(path).write_text(f"Exported {name}")
    
    def LoadFromText(self, obj_type, name, path):
        pass


class MockFileSystem:
    """Mock file system for testing."""
    
    def __init__(self):
        self.files = {}
        self.dirs = set()
    
    def exists(self, path: Path) -> bool:
        return str(path) in self.files or str(path) in self.dirs
    
    def makedirs(self, path: Path, exist_ok: bool = False):
        self.dirs.add(str(path))
    
    def write_text(self, path: Path, content: str):
        self.files[str(path)] = content
    
    def read_text(self, path: Path) -> str:
        return self.files.get(str(path), "")
    
    def unlink(self, path: Path):
        if str(path) in self.files:
            del self.files[str(path)]


class MockHashIndex:
    """Mock hash index."""
    
    def __init__(self):
        self.hashes = {}
    
    def get(self, path):
        return self.hashes.get(path)
    
    def update(self, path, hash_val):
        self.hashes[path] = hash_val


@pytest.fixture
def mock_app():
    return MockAccessApp()


@pytest.fixture
def mock_fs():
    return MockFileSystem()


@pytest.fixture
def mock_factory(mock_app):
    factory = MagicMock()
    factory.create.return_value = mock_app
    return factory


class TestExporterDI:
    """Exporter tests with full dependency injection."""
    
    def test_exporter_with_mock_dependencies(self, mock_factory, mock_fs):
        """Test exporter with all dependencies mocked."""
        exporter = Exporter(
            access_factory=mock_factory,
            file_system=mock_fs
        )
        
        assert exporter.access_factory == mock_factory
        assert exporter.fs == mock_fs
    
    def test_export_database_success(self, mock_factory, mock_fs, mock_app):
        """Test successful database export."""
        # Setup mock app with one form
        mock_form = MagicMock()
        mock_form.Name = "TestForm"
        mock_app.Forms = [mock_form]
        
        exporter = Exporter(
            access_factory=mock_factory,
            file_system=mock_fs
        )
        
        db_path = Path("C:/test.accdb")
        output_dir = Path("C:/output")
        
        # Create database file in mock fs
        mock_fs.files["C:/test.accdb"] = "exists"
        
        result = exporter.export_database(db_path, output_dir)
        
        assert isinstance(result, ExportResult)
        assert result.forms == 1
        assert result.total_exported == 1
        assert "C:/output/forms/TestForm.txt" in mock_fs.files
    
    def test_export_skips_unchanged(self, mock_factory, mock_fs, mock_app):
        """Test that unchanged files are skipped."""
        mock_form = MagicMock()
        mock_form.Name = "TestForm"
        mock_app.Forms = [mock_form]
        
        # Pre-populate hash index
        hash_index = MockHashIndex()
        # Simulate file already exists with same hash
        
        exporter = Exporter(
            access_factory=mock_factory,
            file_system=mock_fs,
            hash_index=hash_index
        )
        
        # Setup: file exists with known hash
        mock_fs.files["C:/output/forms/TestForm.txt"] = "content"
        
        with patch('officeboy.core.exporter.calculate_hash') as mock_hash:
            mock_hash.return_value = "same_hash"
            hash_index.hashes["C:/output/forms/TestForm.txt"] = "same_hash"
            
            result = exporter.export_database(
                Path("C:/test.accdb"), 
                Path("C:/output")
            )
            
            assert result.skipped == 1
            assert result.forms == 0  # Not exported, just skipped
    
    def test_export_force_overrides_skip(self, mock_factory, mock_fs, mock_app):
        """Test force export overrides skip logic."""
        mock_form = MagicMock()
        mock_form.Name = "TestForm"
        mock_app.Forms = [mock_form]
        
        hash_index = MockHashIndex()
        mock_fs.files["C:/output/forms/TestForm.txt"] = "content"
        
        exporter = Exporter(
            access_factory=mock_factory,
            file_system=mock_fs,
            hash_index=hash_index
        )
        
        with patch('officeboy.core.exporter.calculate_hash') as mock_hash:
            mock_hash.return_value = "same_hash"
            hash_index.hashes["C:/output/forms/TestForm.txt"] = "same_hash"
            
            result = exporter.export_database(
                Path("C:/test.accdb"),
                Path("C:/output"),
                force_export=True
            )
            
            assert result.skipped == 0
            assert result.forms == 1
    
    def test_export_handles_errors_gracefully(self, mock_factory, mock_fs, mock_app):
        """Test that export continues despite individual errors."""
        mock_form = MagicMock()
        mock_form.Name = "TestForm"
        mock_app.Forms = [mock_form]
        
        # Make SaveAsText raise exception
        def fail_save(*args, **kwargs):
            raise Exception("COM Error")
        
        mock_app.SaveAsText = fail_save
        
        exporter = Exporter(
            access_factory=mock_factory,
            file_system=mock_fs
        )
        
        # Should not raise, should return 0 exports
        result = exporter.export_database(Path("C:/test.accdb"), Path("C:/output"))
        
        assert result.forms == 0
        assert len(result.errors) > 0
    
    def test_export_single_object(self, mock_factory, mock_fs, mock_app):
        """Test exporting single object."""
        exporter = Exporter(
            access_factory=mock_factory,
            file_system=mock_fs
        )
        
        mock_fs.files["C:/test.accdb"] = "exists"
        
        result = exporter.export_single_object(
            Path("C:/test.accdb"),
            ObjectType.FORM,
            "MyForm",
            Path("C:/output/MyForm.txt")
        )
        
        assert result is True
        assert "C:/output/MyForm.txt" in mock_fs.files
    
    def test_exporter_context_manager(self, mock_factory, mock_fs):
        """Test exporter as context manager."""
        with Exporter(access_factory=mock_factory, file_system=mock_fs) as exporter:
            assert exporter is not None
        
        # Verify cleanup happened
        mock_factory.create.return_value.Quit.assert_called()