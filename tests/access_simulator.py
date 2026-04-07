"""
Access Simulator - Sophisticated MS Access mock for integration testing.
Simulates COM objects, SQLite persistence (temporary files), and export/import operations.
"""
import os
import sys
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from typing import Dict, List, Optional


class MockDoCmd:
    """Simulates DoCmd (Access commands)."""
    
    def __init__(self, db_connection: sqlite3.Connection):
        self._db = db_connection
    
    def RunSQL(self, sql: str):
        """Executes SQL against simulated database."""
        sql_upper = sql.upper()
        
        if "CREATE TABLE" in sql_upper:
            try:
                self._db.execute(sql)
                self._db.commit()
            except sqlite3.OperationalError:
                pass  # Table already exists, ignore
    
    def OutputTo(self, object_type, object_name, output_format, output_file):
        """Simulates export (for disassembly tests)."""
        pass
    
    def TransferText(self, transfer_type, specification_name, table_name, file_name, has_field_names=True):
        """Simulates text import/export."""
        pass


class MockCurrentDb:
    """Simulates CurrentDb (current database)."""
    
    def __init__(self, db_path: Path):
        self.Name = str(db_path)
        self._path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._cursor = self._conn.cursor()
    
    def OpenRecordset(self, query: str):
        """Simulates recordset."""
        return MockRecordset(self._cursor.execute(query))
    
    def Execute(self, sql: str):
        """Executes SQL."""
        self._conn.execute(sql)
        self._conn.commit()
    
    def TableDefs(self):
        """Returns table definitions."""
        cursor = self._conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = []
        for row in cursor.fetchall():
            mock_table = MagicMock()
            mock_table.Name = row[0]
            tables.append(mock_table)
        return tables


class MockRecordset:
    """Simulates Recordset."""
    
    def __init__(self, cursor):
        self._cursor = cursor
        self.EOF = False
        self.Fields = []
    
    def MoveNext(self):
        pass
    
    def Close(self):
        pass


class MockCollection:
    """Simulates collections (Forms, Reports, Modules, etc)."""
    
    def __init__(self, item_type: str, db_path: Path):
        self._item_type = item_type
        self._db_path = db_path
        self._items: Dict[str, MagicMock] = {}
    
    def __iter__(self):
        return iter(self._items.values())
    
    def __len__(self):
        return len(self._items)
    
    def __getitem__(self, name: str):
        return self._items[name]
    
    def Add(self, item):
        self._items[item.Name] = item


class AccessSimulator:
    """
    Simulator for Access.Application.
    Maintains state in SQLite (temporary files) for real persistence between operations.
    """
    
    Version = "16.0"  # Simulates Access 2016/365
    
    def __init__(self):
        self._current_db: Optional[Path] = None
        self._db_connection: Optional[sqlite3.Connection] = None
        self._temp_dir = tempfile.mkdtemp(prefix="access_sim_")
        self.DoCmd = None
        
        # Empty collections initially
        self.Forms = MockCollection("Form", Path(self._temp_dir))
        self.Reports = MockCollection("Report", Path(self._temp_dir))
        self.Modules = MockCollection("Module", Path(self._temp_dir))
        self.Queries = MockCollection("Query", Path(self._temp_dir))
        
        # Project properties
        self.CurrentProject = MagicMock()
        self.CurrentProject.FullName = ""
        self.CurrentProject.Name = ""
    
    def NewCurrentDatabase(self, db_path: str):
        """Creates new database (SQLite as backend)."""
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Creates empty SQLite file
        conn = sqlite3.connect(str(path))
        conn.execute("CREATE TABLE IF NOT EXISTS __access_meta (key TEXT, value TEXT)")
        conn.commit()
        conn.close()
        
        self._open_database(path)
    
    def OpenCurrentDatabase(self, db_path: str):
        """Opens existing database."""
        path = Path(db_path)
        if not path.exists():
            raise FileNotFoundError(f"Database '{db_path}' not found")
        self._open_database(path)
    
    def _open_database(self, path: Path):
        """Opens internal connection."""
        self._current_db = path
        self._db_connection = sqlite3.connect(str(path))
        self.DoCmd = MockDoCmd(self._db_connection)
        self.CurrentDb = lambda: MockCurrentDb(path)
        self.CurrentProject.FullName = str(path)
        self.CurrentProject.Name = path.stem
    
    def CloseCurrentDatabase(self):
        """Closes current database."""
        if self._db_connection:
            self._db_connection.close()
            self._db_connection = None
        self._current_db = None
        self.CurrentProject.FullName = ""
        self.CurrentProject.Name = ""
    
    def Quit(self):
        """Closes application."""
        self.CloseCurrentDatabase()
    
    def SaveAsText(self, object_type: int, object_name: str, file_path: str):
        """
        Simulates exporting object to text file.
        Creates .txt or .form file with JSON metadata.
        """
        export_path = Path(file_path)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = {
            "Type": object_type,
            "Name": object_name,
            "Version": "20",
            "Properties": {},
            "Controls": []
        }
        
        export_path.write_text(json.dumps(content, indent=2))
    
    def LoadFromText(self, object_type: int, object_name: str, file_path: str):
        """Simulates importing object from text file."""
        import_path = Path(file_path)
        if not import_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Simulates object creation in database
        if object_type == 2:  # Form (acForm)
            mock_form = MagicMock()
            mock_form.Name = object_name
            self.Forms.Add(mock_form)


def is_admin() -> bool:
    """Checks if has administrator privileges."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def has_real_access() -> bool:
    """Checks if real Access is installed."""
    if sys.platform != "win32":
        return False
    try:
        import win32com.client
        app = win32com.client.Dispatch("Access.Application")
        app.Quit()
        return True
    except:
        return False


def create_access_app():
    """
    Factory that returns real Access if available,
    or simulator if no Access or permissions.
    """
    if has_real_access():
        import win32com.client
        return win32com.client.Dispatch("Access.Application")
    else:
        return AccessSimulator()