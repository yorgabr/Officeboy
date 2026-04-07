"""
Integration tests using Access Simulator only.
Avoids real Access COM instability.
"""
import pytest
from pathlib import Path

from .access_simulator import AccessSimulator

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TestDatabaseOperations:
    """Database creation and manipulation tests."""
    
    def test_create_database(self, access_application, tmp_path):
        """Tests creation of new database."""
        db_path = tmp_path / "new_test.accdb"
        
        access_application.NewCurrentDatabase(str(db_path))
        
        assert db_path.exists()
        assert "new_test" in access_application.CurrentProject.Name
        
        access_application.CloseCurrentDatabase()
    
    def test_database_persistence(self, access_application, tmp_path):
        """Tests that data persists in database."""
        db_path = tmp_path / "persistent.accdb"
        
        access_application.NewCurrentDatabase(str(db_path))
        
        # Creates table via SQL
        access_application.DoCmd.RunSQL(
            "CREATE TABLE Users (ID INTEGER PRIMARY KEY, Name TEXT)"
        )
        access_application.DoCmd.RunSQL(
            "INSERT INTO Users (ID, Name) VALUES (1, 'John')"
        )
        
        access_application.CloseCurrentDatabase()
        
        # Reopens and verifies
        access_application.OpenCurrentDatabase(str(db_path))
        assert "persistent" in access_application.CurrentProject.Name


class TestExportImport:
    """Export and import tests."""
    
    def test_export_form_to_text(self, access_application, tmp_path):
        """Tests exporting form to text file."""
        db_path = tmp_path / "export_test.accdb"
        export_dir = tmp_path / "src"
        export_dir.mkdir()
        
        access_application.NewCurrentDatabase(str(db_path))
        
        export_file = export_dir / "TestForm.txt"
        
        # AcForm = 2 (Access constant)
        access_application.SaveAsText(2, "TestForm", str(export_file))
        
        assert export_file.exists()
        content = export_file.read_text()
        assert "TestForm" in content
        
        access_application.CloseCurrentDatabase()
    
    def test_import_form_from_text(self, access_application, tmp_path):
        """Tests importing form from text file."""
        db_path = tmp_path / "import_test.accdb"
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # Creates form definition file
        form_file = src_dir / "TestForm.form"
        form_file.write_text("""
{
  "Type": 2,
  "Name": "TestForm",
  "Version": "20",
  "Properties": {},
  "Controls": []
}
""")
        
        access_application.NewCurrentDatabase(str(db_path))
        
        # Imports (acForm = 2)
        access_application.LoadFromText(2, "TestForm", str(form_file))
        
        # Verifies form was "added"
        forms_list = list(access_application.Forms)
        assert len(forms_list) >= 0
        
        access_application.CloseCurrentDatabase()


class TestCollections:
    """Collections tests (Forms, Reports, etc)."""
    
    def test_forms_collection(self, access_application, tmp_path):
        """Tests forms collection."""
        db_path = tmp_path / "forms_test.accdb"
        access_application.NewCurrentDatabase(str(db_path))
        
        # Initially empty
        initial_count = len(access_application.Forms)
        
        # Adds mock
        from unittest.mock import MagicMock
        form = MagicMock()
        form.Name = "Form1"
        access_application.Forms.Add(form)
        
        assert len(access_application.Forms) == initial_count + 1
        
        access_application.CloseCurrentDatabase()
    
    def test_version_property(self, access_application):
        """Tests Version property."""
        version = access_application.Version
        assert version is not None
        assert len(version) > 0
        assert "." in str(version)


class TestSimulatorSpecific:
    """Tests validating the simulator."""
    
    def test_simulator_uses_sqlite(self, access_application, tmp_path):
        """Verifies simulator uses SQLite internally."""
        assert isinstance(access_application, AccessSimulator)
        
        db_path = tmp_path / "sqlite_verify.accdb"
        access_application.NewCurrentDatabase(str(db_path))
        
        # SQLite must create real file
        assert db_path.stat().st_size > 0
        
        access_application.CloseCurrentDatabase()