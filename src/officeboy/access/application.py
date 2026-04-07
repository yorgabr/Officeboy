"""
MS Access application interface with dependency injection support.
"""
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Protocol, Dict, Any, List


class AccessApplicationInterface(Protocol):
    """Protocol for Access application (allows real Access or Simulator)."""
    
    @property
    def Version(self) -> str: ...
    
    @property
    def CurrentProject(self) -> Any: ...
    
    @property
    def Forms(self) -> Any: ...
    
    @property
    def Reports(self) -> Any: ...
    
    @property
    def Modules(self) -> Any: ...
    
    @property
    def Queries(self) -> Any: ...
    
    @property
    def DoCmd(self) -> Any: ...
    
    def NewCurrentDatabase(self, filepath: str) -> None: ...
    def OpenCurrentDatabase(self, filepath: str) -> None: ...
    def CloseCurrentDatabase(self) -> None: ...
    def Quit(self) -> None: ...
    def SaveAsText(self, object_type: int, name: str, path: str) -> None: ...
    def LoadFromText(self, object_type: int, name: str, path: str) -> None: ...


class AccessAppFactory(ABC):
    """Abstract factory for creating Access applications."""
    
    @abstractmethod
    def create(self) -> AccessApplicationInterface:
        """Create and return Access application instance."""
        pass


class Win32AccessAppFactory(AccessAppFactory):
    """Factory for real MS Access via win32com."""
    
    def create(self) -> AccessApplicationInterface:
        import win32com.client
        return win32com.client.Dispatch("Access.Application")


class AccessApplicationService:
    """High-level service for Access operations with injected dependencies."""
    
    def __init__(self, app: Optional[AccessApplicationInterface] = None):
        self._app = app
        self._owns_app = app is None
    
    def __enter__(self):
        if self._app is None:
            factory = Win32AccessAppFactory()
            self._app = factory.create()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    @property
    def app(self) -> AccessApplicationInterface:
        if self._app is None:
            raise RuntimeError("Access application not initialized")
        return self._app
    
    def open_database(self, db_path: Path, create_new: bool = False) -> Any:
        """Open or create database."""
        if create_new:
            self.app.NewCurrentDatabase(str(db_path))
        else:
            self.app.OpenCurrentDatabase(str(db_path))
        return self.app.CurrentDb()
    
    def close(self) -> None:
        """Close application and cleanup."""
        if self._app:
            try:
                self._app.CloseCurrentDatabase()
            except:
                pass
            if self._owns_app:
                try:
                    self._app.Quit()
                except:
                    pass
            self._app = None
    
    def get_version(self) -> str:
        """Get Access version."""
        return self.app.Version
    
    def export_object(
        self, 
        object_type: int, 
        name: str, 
        output_path: Path,
        file_system: Optional['FileSystemInterface'] = None
    ) -> bool:
        """Export object to file."""
        fs = file_system or DefaultFileSystem()
        fs.makedirs(output_path.parent, exist_ok=True)
        
        try:
            self.app.SaveAsText(object_type, name, str(output_path))
            return True
        except Exception:
            return False
    
    def import_object(
        self,
        object_type: int,
        name: str,
        input_path: Path
    ) -> bool:
        """Import object from file."""
        try:
            self.app.LoadFromText(object_type, name, str(input_path))
            return True
        except Exception:
            return False
    
    def get_object_names(self, collection_name: str) -> List[str]:
        """Get names of objects in collection."""
        collection = getattr(self.app, collection_name, [])
        return [obj.Name for obj in collection]
    
    def execute_sql(self, sql: str) -> None:
        """Execute SQL command."""
        self.app.DoCmd.RunSQL(sql)


class FileSystemInterface(Protocol):
    """Protocol for file system operations."""
    
    def exists(self, path: Path) -> bool: ...
    def makedirs(self, path: Path, exist_ok: bool = False) -> None: ...
    def write_text(self, path: Path, content: str) -> None: ...
    def read_text(self, path: Path) -> str: ...
    def unlink(self, path: Path) -> None: ...


class DefaultFileSystem:
    """Default file system implementation."""
    
    def exists(self, path: Path) -> bool:
        return path.exists()
    
    def makedirs(self, path: Path, exist_ok: bool = False) -> None:
        path.mkdir(parents=True, exist_ok=exist_ok)
    
    def write_text(self, path: Path, content: str) -> None:
        path.write_text(content)
    
    def read_text(self, path: Path) -> str:
        return path.read_text()
    
    def unlink(self, path: Path) -> None:
        if path.exists():
            path.unlink()


# Convenience functions that use the service
def get_access_version(factory: Optional[AccessAppFactory] = None) -> str:
    """Get Access version with optional factory injection."""
    factory = factory or Win32AccessAppFactory()
    app = factory.create()
    try:
        return app.Version
    finally:
        app.Quit()


def open_database(
    db_path: Path,
    create_new: bool = False,
    factory: Optional[AccessAppFactory] = None
) -> AccessApplicationService:
    """Open database with optional factory injection."""
    factory = factory or Win32AccessAppFactory()
    app = factory.create()
    service = AccessApplicationService(app)
    
    if create_new:
        service.open_database(db_path, create_new=True)
    else:
        service.open_database(db_path)
    
    return service


# Convenience functions for backward compatibility with tests

def get_access_version() -> str:
    """Get Access version (convenience function)."""
    factory = Win32AccessAppFactory()
    app = factory.create()
    try:
        return app.Version
    finally:
        app.Quit()


def open_database(db_path: Path, create_new: bool = False):
    """
    Open database and return service (convenience function).
    
    Returns:
        AccessApplicationService instance
    """
    factory = Win32AccessAppFactory()
    service = AccessApplicationService(factory.create())
    
    if create_new:
        service.open_database(db_path, create_new=True)
    else:
        service.open_database(db_path)
    
    return service


def close_database(service: AccessApplicationService) -> None:
    """Close database service (convenience function)."""
    service.close()


def export_form(app, name: str, output_path: Path) -> bool:
    """Export form (convenience function)."""
    return app.SaveAsText(2, name, str(output_path))


def export_report(app, name: str, output_path: Path) -> bool:
    """Export report (convenience function)."""
    return app.SaveAsText(5, name, str(output_path))


def export_module(app, name: str, output_path: Path) -> bool:
    """Export module (convenience function)."""
    return app.SaveAsText(10, name, str(output_path))


def export_query(app, name: str, output_path: Path) -> bool:
    """Export query (convenience function)."""
    return app.SaveAsText(1, name, str(output_path))


def export_table(app, name: str, output_path: Path) -> bool:
    """Export table (convenience function)."""
    return app.SaveAsText(6, name, str(output_path))