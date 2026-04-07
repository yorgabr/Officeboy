"""
Database assembler to build Access database from source files.
"""
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Callable

from officeboy.access.application import (
    AccessApplicationService,
    AccessAppFactory,
    Win32AccessAppFactory,
    FileSystemInterface,
    DefaultFileSystem
)


@dataclass
class AssemblyResult:
    """Assembly operation result."""
    total_assembled: int = 0
    forms: int = 0
    reports: int = 0
    modules: int = 0
    queries: int = 0
    macros: int = 0
    tables: int = 0
    errors: List[str] = field(default_factory=list)


class Assembler:
    """Database assembler with dependency injection."""
    
    def __init__(
        self,
        access_factory: Optional[AccessAppFactory] = None,
        file_system: Optional[FileSystemInterface] = None
    ):
        self.access_factory = access_factory or Win32AccessAppFactory()
        self.fs = file_system or DefaultFileSystem()
        self._access_service: Optional[AccessApplicationService] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    @property
    def access_service(self) -> AccessApplicationService:
        if self._access_service is None:
            app = self.access_factory.create()
            self._access_service = AccessApplicationService(app)
        return self._access_service
    
    def close(self):
        """Cleanup resources."""
        if self._access_service:
            self._access_service.close()
            self._access_service = None
    
    def assemble(
        self,
        source_dir: Path,
        db_path: Path,
        template: Optional[Path] = None,
        overwrite: bool = False,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> AssemblyResult:
        """
        Assemble database from source directory.
        
        Args:
            source_dir: Source directory with exported objects
            db_path: Destination database path
            template: Optional template database
            overwrite: Overwrite existing database
            progress_callback: Progress callback
        """
        result = AssemblyResult()
        
        if not self.fs.exists(source_dir):
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
        
        if self.fs.exists(db_path) and not overwrite:
            raise FileExistsError(f"Database exists: {db_path}")
        
        if template and self.fs.exists(template):
            self._create_from_template(db_path, template)
        else:
            self.access_service.open_database(db_path, create_new=True)
        
        try:
            assemblers = [
                ("forms", 2, "forms"),
                ("reports", 5, "reports"),
                ("modules", 10, "modules"),
                ("queries", 1, "queries"),
                ("macros", 4, "macros"),
            ]
            
            for dir_name, obj_type, attr_name in assemblers:
                count, errors = self._assemble_collection(
                    source_dir / dir_name,
                    obj_type,
                    progress_callback
                )
                setattr(result, attr_name, count)
                result.total_assembled += count
                result.errors.extend(errors)
            
        finally:
            self.access_service.close()
        
        return result
    
    def _create_from_template(self, db_path: Path, template: Path) -> None:
        """Create database from template."""
        shutil.copy(str(template), str(db_path))
        self.access_service.open_database(db_path)
    
    def _assemble_collection(
        self,
        source_dir: Path,
        obj_type: int,
        progress_callback: Optional[Callable]
    ) -> tuple[int, List[str]]:
        """Assemble objects from directory."""
        count = 0
        errors = []
        
        if not self.fs.exists(source_dir):
            return 0, []
        
        try:
            files = list(source_dir.glob("*.txt")) + list(source_dir.glob("*.form"))
        except Exception:
            return 0, []
        
        for i, file_path in enumerate(files):
            name = file_path.stem
            
            if progress_callback:
                progress_callback(name, i + 1, len(files))
            
            try:
                success = self.access_service.import_object(
                    obj_type, name, file_path
                )
                if success:
                    count += 1
                else:
                    errors.append(f"Failed to assemble {name}")
            except Exception as e:
                errors.append(f"Error assembling {name}: {str(e)}")
        
        return count, errors
    
    def assemble_object(
        self,
        db_path: Path,
        obj_type: int,
        name: str,
        input_path: Path
    ) -> bool:
        """Assemble single object."""
        if not self.fs.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        if not self.fs.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        self.access_service.open_database(db_path)
        try:
            return self.access_service.import_object(obj_type, name, input_path)
        finally:
            self.access_service.close()