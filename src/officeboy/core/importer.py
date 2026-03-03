"""MS Access database importer."""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from officeboy.access.application import AccessApplication
from officeboy.access.objects import AccessObjectType, ObjectInfo
from officeboy.i18n import get_text as _

logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    """Statistics for import operation."""
    
    forms: int = 0
    reports: int = 0
    modules: int = 0
    queries: int = 0
    macros: int = 0
    tables: int = 0
    errors: int = 0
    total_imported: int = 0
    
    def increment(self, object_type: AccessObjectType) -> None:
        """Increment counter for object type."""
        self.total_imported += 1
        
        if object_type == AccessObjectType.FORM:
            self.forms += 1
        elif object_type == AccessObjectType.REPORT:
            self.reports += 1
        elif object_type == AccessObjectType.MODULE:
            self.modules += 1
        elif object_type == AccessObjectType.QUERY:
            self.queries += 1
        elif object_type == AccessObjectType.MACRO:
            self.macros += 1
        elif object_type == AccessObjectType.TABLE:
            self.tables += 1


class AccessImporter:
    """Imports MS Access database objects from source files."""
    
    # Mapping of file extensions to object types
    EXTENSION_MAP = {
        ".form.vba": AccessObjectType.FORM,
        ".report.vba": AccessObjectType.REPORT,
        ".bas": AccessObjectType.MODULE,
        ".cls": AccessObjectType.CLASS,
        ".sql": AccessObjectType.QUERY,
        ".macro": AccessObjectType.MACRO,
        ".json": AccessObjectType.TABLE,
        ".csv": AccessObjectType.TABLE_DATA,
    }
    
    def __init__(
        self,
        source_dir: Path,
        access_file: Path,
        template: Optional[Path] = None,
        encoding: str = "utf-8",
    ) -> None:
        """Initialize importer.
        
        Args:
            source_dir: Directory containing source files.
            access_file: Path for output database.
            template: Optional template database.
            encoding: Text encoding for source files.
        """
        self.source_dir = Path(source_dir)
        self.access_file = Path(access_file)
        self.template = template
        self.encoding = encoding
        
        self.app = AccessApplication()
        self.stats = ImportStats()
        
    def _get_object_type_from_extension(self, file_path: Path) -> Optional[AccessObjectType]:
        """Determine object type from file extension.
        
        Args:
            file_path: Path to source file.
            
        Returns:
            Object type if recognized, None otherwise.
        """
        name = file_path.name.lower()
        
        for ext, obj_type in self.EXTENSION_MAP.items():
            if name.endswith(ext):
                return obj_type
        
        return None
    
    def _get_object_name_from_filename(self, file_path: Path) -> str:
        """Extract object name from filename.
        
        Args:
            file_path: Path to source file.
            
        Returns:
            Object name without extension.
        """
        name = file_path.stem
        
        # Handle compound extensions like .form.vba
        for ext in [".form", ".report", ".vba"]:
            if name.lower().endswith(ext):
                name = name[:-len(ext)]
        
        return name
    
    def _import_object(self, file_path: Path, 
                       obj_type: AccessObjectType) -> bool:
        """Import single object from file.
        
        Args:
            file_path: Path to source file.
            obj_type: Type of object.
            
        Returns:
            True if imported successfully, False otherwise.
        """
        try:
            obj_name = self._get_object_name_from_filename(file_path)
            
            # Read content
            if obj_type in (AccessObjectType.TABLE_DATA,):
                with open(file_path, "rb") as f:
                    content = f.read()
            else:
                with open(file_path, "r", encoding=self.encoding) as f:
                    content = f.read()
            
            # Create ObjectInfo
            obj_info = ObjectInfo(
                name=obj_name,
                object_type=obj_type,
                path=file_path,
            )
            
            # Import via Access
            success = self.app.import_object(obj_info, content)
            
            if success:
                self.stats.increment(obj_type)
                logger.info(
                    _("Imported {type}: {name}").format(
                        type=obj_type.value,
                        name=obj_name,
                    )
                )
                return True
            else:
                logger.error(
                    _("Failed to import {name}").format(name=obj_name)
                )
                self.stats.errors += 1
                return False
                
        except Exception as e:
            logger.exception(
                _("Error importing {file}: {error}").format(
                    file=file_path,
                    error=e,
                )
            )
            self.stats.errors += 1
            return False
    
    def _import_references(self) -> None:
        """Import VBA references."""
        refs_path = self.source_dir / "references.refs"
        if not refs_path.exists():
            return
        
        try:
            with open(refs_path, "r", encoding=self.encoding) as f:
                content = f.read()
            
            refs = []
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("Reference:"):
                    # Parse: Reference: Name=GUID;Major.Minor
                    match = re.match(
                        r"Reference:\s*([^=]+)=([^;]+);(\d+)\.(\d+)",
                        line
                    )
                    if match:
                        refs.append({
                            "name": match.group(1),
                            "guid": match.group(2),
                            "major": int(match.group(3)),
                            "minor": int(match.group(4)),
                        })
            
            self.app.set_references(refs)
            logger.info(_("Imported {count} references").format(count=len(refs)))
            
        except Exception as e:
            logger.exception(
                _("Failed to import references: {error}").format(error=e)
            )
    
    def _import_properties(self) -> None:
        """Import database properties."""
        props_path = self.source_dir / "database.properties"
        if not props_path.exists():
            return
        
        try:
            with open(props_path, "r", encoding=self.encoding) as f:
                content = f.read()
            
            props = {}
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("'") and "=" in line:
                    key, value = line.split("=", 1)
                    props[key.strip()] = value.strip()
            
            self.app.set_database_properties(props)
            logger.info(_("Imported database properties"))
            
        except Exception as e:
            logger.exception(
                _("Failed to import properties: {error}").format(error=e)
            )
    
    def import_all(self) -> ImportStats:
        """Import all objects from source directory.
        
        Returns:
            Import statistics.
        """
        try:
            # Create or open database
            if self.template:
                self.app.create_from_template(self.access_file, self.template)
            else:
                self.app.create_database(self.access_file)
            
            logger.info(
                _("Created database: {file}").format(file=self.access_file)
            )
            
            # Import tables first (for relationships)
            self._import_type(AccessObjectType.TABLE)
            
            # Import queries
            self._import_type(AccessObjectType.QUERY)
            
            # Import forms
            self._import_type(AccessObjectType.FORM)
            
            # Import reports
            self._import_type(AccessObjectType.REPORT)
            
            # Import modules and classes
            self._import_type(AccessObjectType.MODULE)
            self._import_type(AccessObjectType.CLASS)
            
            # Import macros
            self._import_type(AccessObjectType.MACRO)
            
            # Import references
            self._import_references()
            
            # Import properties
            self._import_properties()
            
            # Compile VBA
            self.app.compile_vba()
            
            return self.stats
            
        finally:
            self.app.close_database()
    
    def _import_type(self, obj_type: AccessObjectType) -> None:
        """Import all objects of a specific type.
        
        Args:
            obj_type: Type of objects to import.
        """
        type_dir = self.source_dir / obj_type.value
        if not type_dir.exists():
            return
        
        files = list(type_dir.iterdir())
        logger.info(
            _("Found {count} {type} files to import").format(
                count=len(files),
                type=obj_type.value,
            )
        )
        
        for file_path in files:
            if file_path.is_file():
                detected_type = self._get_object_type_from_extension(file_path)
                if detected_type == obj_type:
                    self._import_object(file_path, obj_type)