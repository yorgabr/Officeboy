"""
Database disassembler to break down Access database into source files.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Callable

from officeboy.access.application import (
    AccessApplicationService,
    AccessAppFactory,
    Win32AccessAppFactory,
    FileSystemInterface,
    DefaultFileSystem
)
from officeboy.core.hasher import calculate_hash, HashIndex
from officeboy.core.index import IndexManager


@dataclass
class DisassemblyResult:
    """Disassembly operation result."""
    total_disassembled: int = 0
    forms: int = 0
    reports: int = 0
    modules: int = 0
    queries: int = 0
    macros: int = 0
    tables: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)


class ObjectType:
    """Access object type constants."""
    FORM = 2
    REPORT = 5
    MODULE = 10
    QUERY = 1
    MACRO = 4
    TABLE = 6


class Disassembler:
    """Database disassembler with dependency injection."""
    
    def __init__(
        self,
        access_factory: Optional[AccessAppFactory] = None,
        file_system: Optional[FileSystemInterface] = None,
        index_manager: Optional[IndexManager] = None,
        hash_index: Optional[HashIndex] = None
    ):
        self.access_factory = access_factory or Win32AccessAppFactory()
        self.fs = file_system or DefaultFileSystem()
        self.index = index_manager
        self.hash_index = hash_index
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
    
    def disassemble(
        self,
        db_path: Path,
        output_dir: Path,
        force: bool = False,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> DisassemblyResult:
        """
        Disassemble database into source files.
        
        Args:
            db_path: Path to Access database
            output_dir: Destination directory
            force: Skip hash checks
            progress_callback: Called with (item_name, current, total)
        """
        result = DisassemblyResult()
        
        if not self.fs.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        self._setup_output_dirs(output_dir)
        
        self.access_service.open_database(db_path)
        
        try:
            disassemblers = [
                (ObjectType.FORM, "forms", "Forms"),
                (ObjectType.REPORT, "reports", "Reports"),
                (ObjectType.MODULE, "modules", "Modules"),
                (ObjectType.QUERY, "queries", "Queries"),
                (ObjectType.MACRO, "macros", "Macros"),
                (ObjectType.TABLE, "tables", "Tables"),
            ]
            
            for obj_type, dir_name, coll_name in disassemblers:
                count, skipped = self._disassemble_collection(
                    obj_type,
                    output_dir / dir_name,
                    coll_name,
                    force,
                    progress_callback
                )
                setattr(result, dir_name, count)
                result.total_disassembled += count
                result.skipped += skipped
            
            if self.index:
                self._update_index(db_path, output_dir)
                
        finally:
            self.access_service.close()
        
        return result
    
    def _setup_output_dirs(self, output_dir: Path) -> None:
        """Create output directory structure."""
        for subdir in ["forms", "reports", "modules", "queries", "macros", "tables"]:
            self.fs.makedirs(output_dir / subdir, exist_ok=True)
    
    def _disassemble_collection(
        self,
        obj_type: int,
        output_dir: Path,
        collection_name: str,
        force: bool,
        progress_callback: Optional[Callable]
    ) -> tuple[int, int]:
        """Disassemble objects from collection."""
        count = 0
        skipped = 0
        
        try:
            names = self.access_service.get_object_names(collection_name)
        except Exception:
            return 0, 0
        
        for i, name in enumerate(names):
            if progress_callback:
                progress_callback(name, i + 1, len(names))
            
            output_path = output_dir / f"{name}.txt"
            
            if not force and self._is_unchanged(output_path):
                skipped += 1
                continue
            
            success = self.access_service.export_object(
                obj_type, name, output_path, self.fs
            )
            
            if success:
                count += 1
                self._update_hash(output_path)
        
        return count, skipped
    
    def _is_unchanged(self, path: Path) -> bool:
        """Check if file is unchanged."""
        if not self.fs.exists(path):
            return False
        if self.hash_index is None:
            return False
        
        current_hash = calculate_hash(path)
        stored_hash = self.hash_index.get(str(path))
        return current_hash == stored_hash
    
    def _update_hash(self, path: Path) -> None:
        """Update hash in index."""
        if self.hash_index:
            self.hash_index.update(str(path), calculate_hash(path))
    
    def _update_index(self, db_path: Path, output_dir: Path) -> None:
        """Update disassembly index."""
        if self.index is None:
            return
        
        self.index.add(
            str(db_path),
            str(output_dir),
            self.hash_index.get(str(db_path)) if self.hash_index else None
        )
        self.index.save()
    
    def disassemble_object(
        self,
        db_path: Path,
        obj_type: int,
        name: str,
        output_path: Path
    ) -> bool:
        """Disassemble single object."""
        if not self.fs.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        self.fs.makedirs(output_path.parent, exist_ok=True)
        
        self.access_service.open_database(db_path)
        try:
            return self.access_service.export_object(
                obj_type, name, output_path, self.fs
            )
        finally:
            self.access_service.close()