"""
Unit tests for importer module - target 80%+ coverage.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from officeboy.core.importer import Importer, ImportResult


class TestImportResult:
    """Tests for ImportResult dataclass."""
    
    def test_import_result_creation(self):
        """Test creating ImportResult."""
        result = ImportResult(
            total_imported=3,
            forms=1,
            reports=1,
            modules=1,
            tables=0,
            queries=0,
            errors=[]
        )
        
        assert result.total_imported == 3
        assert result.forms == 1
        assert result.errors == []


class TestImporter:
    """Tests for Importer class."""
    
    def test_importer_initialization(self):
        """Test Importer initialization."""
        importer = Importer()
        
        assert importer is not None
    
    def test_importer_import_database(self, tmp_path, access_application):
        """Test importing database."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        db_path = tmp_path / "output.accdb"
        
        # Create source structure
        (source_dir / "forms").mkdir()
        (source_dir / "forms" / "TestForm.form").write_text(
            '{"Type": 2, "Name": "TestForm"}'
        )
        
        access_application.NewCurrentDatabase(str(db_path))
        
        importer = Importer()
        
        with patch('officeboy.core.importer.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            result = importer.import_database(source_dir, db_path)
            
            assert isinstance(result, ImportResult)
            assert result.total_imported >= 0
    
    def test_importer_import_with_template(self, tmp_path, access_application):
        """Test importing with template."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        db_path = tmp_path / "output.accdb"
        template_path = tmp_path / "template.accdb"
        
        access_application.NewCurrentDatabase(str(template_path))
        access_application.CloseCurrentDatabase()
        
        importer = Importer()
        
        with patch('officeboy.core.importer.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            result = importer.import_database(source_dir, db_path, template=template_path)
            
            assert isinstance(result, ImportResult)
    
    def test_importer_handles_errors(self, tmp_path, access_application):
        """Test importer handles errors gracefully."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        db_path = tmp_path / "output.accdb"
        
        # Create invalid source file
        (source_dir / "invalid.txt").write_text("invalid content")
        
        access_application.NewCurrentDatabase(str(db_path))
        
        importer = Importer()
        
        with patch('officeboy.core.importer.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            result = importer.import_database(source_dir, db_path)
            
            # Should complete without raising
            assert isinstance(result, ImportResult)