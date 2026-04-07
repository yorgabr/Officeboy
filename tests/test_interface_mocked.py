"""
Interface tests using exclusively the simulator.
Fast and 100% isolated.
"""
import pytest
from pathlib import Path

from .access_simulator import AccessSimulator

pytestmark = [pytest.mark.interface, pytest.mark.unit]


class TestAccessSimulator:
    """Simulator self-tests (ensures mock is valid)."""
    
    def test_simulator_creation(self):
        """Tests simulator creation."""
        sim = AccessSimulator()
        assert sim.Version == "16.0"
        sim.Quit()
    
    def test_database_lifecycle(self, tmp_path):
        """Tests complete database lifecycle in simulator."""
        sim = AccessSimulator()
        db_path = tmp_path / "lifecycle.accdb"
        
        # Creates
        sim.NewCurrentDatabase(str(db_path))
        assert db_path.exists()
        assert "lifecycle" in sim.CurrentProject.Name
        
        # Closes
        sim.CloseCurrentDatabase()
        assert sim.CurrentProject.Name == ""
        
        # Reopens
        sim.OpenCurrentDatabase(str(db_path))
        assert "lifecycle" in sim.CurrentProject.Name
        
        sim.Quit()
    
    def test_sql_execution(self, tmp_path):
        """Tests SQL execution in simulator."""
        sim = AccessSimulator()
        db_path = tmp_path / "sql_test.accdb"
        
        sim.NewCurrentDatabase(str(db_path))
        
        # Creates table
        sim.DoCmd.RunSQL("CREATE TABLE TestTable (ID INT, Name TEXT)")
        
        # Verifies via direct SQLite
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TestTable'")
        assert cursor.fetchone() is not None
        conn.close()
        
        sim.Quit()
    
    def test_export_import_text(self, tmp_path):
        """Tests object export/import."""
        sim = AccessSimulator()
        db_path = tmp_path / "export_import.accdb"
        export_file = tmp_path / "export" / "Form1.txt"
        export_file.parent.mkdir(exist_ok=True)
        
        sim.NewCurrentDatabase(str(db_path))
        
        # Exports
        sim.SaveAsText(2, "Form1", str(export_file))
        assert export_file.exists()
        
        # Imports
        sim.LoadFromText(2, "Form2", str(export_file))
        
        sim.Quit()