"""
Unit tests for access.application module using AccessSimulator.
Target: Increase coverage from 9% to 80%+.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from officeboy.access.application import (
    get_access_version,
    open_database,
    close_database,
    export_form,
    export_report,
    export_module,
    export_query,
    export_table
)


class TestGetAccessVersion:
    """Tests for get_access_version function."""
    
    def test_get_version_with_simulator(self, access_application):
        """Test getting version from simulator."""
        with patch('officeboy.access.application.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            version = get_access_version()
            
            assert version == "16.0"
            access_application.Quit.assert_called_once()


class TestOpenDatabase:
    """Tests for open_database function."""
    
    def test_open_database_success(self, access_application, tmp_path):
        """Test opening database."""
        db_path = tmp_path / "test.accdb"
        access_application.NewCurrentDatabase(str(db_path))
        access_application.CloseCurrentDatabase()
        
        with patch('officeboy.access.application.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            app, db = open_database(str(db_path))
            
            assert app is access_application
            access_application.OpenCurrentDatabase.assert_called_with(str(db_path))
    
    def test_open_database_create_new(self, access_application, tmp_path):
        """Test creating new database."""
        db_path = tmp_path / "new.accdb"
        
        with patch('officeboy.access.application.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            app, db = open_database(str(db_path), create_new=True)
            
            access_application.NewCurrentDatabase.assert_called_with(str(db_path))


class TestCloseDatabase:
    """Tests for close_database function."""
    
    def test_close_database(self, access_application):
        """Test closing database."""
        close_database(access_application)
        
        access_application.CloseCurrentDatabase.assert_called_once()
        access_application.Quit.assert_called_once()


class TestExportFunctions:
    """Tests for export functions."""
    
    def test_export_form(self, access_application, tmp_path):
        """Test exporting form."""
        export_path = tmp_path / "forms" / "TestForm.txt"
        export_path.parent.mkdir(parents=True)
        
        # Setup mock form
        mock_form = MagicMock()
        mock_form.Name = "TestForm"
        mock_form.HasModule = True
        access_application.Forms.Add(mock_form)
        
        with patch('officeboy.access.application.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            export_form(access_application, "TestForm", str(export_path))
            
            assert export_path.exists()
    
    def test_export_report(self, access_application, tmp_path):
        """Test exporting report."""
        export_path = tmp_path / "reports" / "TestReport.txt"
        export_path.parent.mkdir(parents=True)
        
        with patch('officeboy.access.application.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            export_report(access_application, "TestReport", str(export_path))
            
            assert export_path.exists()
    
    def test_export_module(self, access_application, tmp_path):
        """Test exporting module."""
        export_path = tmp_path / "modules" / "TestModule.txt"
        export_path.parent.mkdir(parents=True)
        
        with patch('officeboy.access.application.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            export_module(access_application, "TestModule", str(export_path))
            
            assert export_path.exists()
    
    def test_export_query(self, access_application, tmp_path):
        """Test exporting query."""
        export_path = tmp_path / "queries" / "TestQuery.txt"
        export_path.parent.mkdir(parents=True)
        
        with patch('officeboy.access.application.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            export_query(access_application, "TestQuery", str(export_path))
            
            assert export_path.exists()
    
    def test_export_table(self, access_application, tmp_path):
        """Test exporting table."""
        export_path = tmp_path / "tables" / "TestTable.txt"
        export_path.parent.mkdir(parents=True)
        
        with patch('officeboy.access.application.Dispatch') as mock_dispatch:
            mock_dispatch.return_value = access_application
            
            export_table(access_application, "TestTable", str(export_path))
            
            assert export_path.exists()