"""MS Access database exporter."""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from officeboy.core.hasher import ContentHasher
from officeboy.core.index import IndexManager
from officeboy.access.application import AccessApplication
from officeboy.access.objects import AccessObjectType, ObjectInfo
from officeboy.i18n import get_text as _

logger = logging.getLogger(__name__)


@dataclass
class ExportStats:
    """Statistics for export operation."""
    
    forms: int = 0
    reports: int = 0
    modules: int = 0
    queries: int = 0
    macros: int = 0
    tables: int = 0
    skipped: int = 0
    errors: int = 0
    total_exported: int = 0
    
    def increment(self, object_type: AccessObjectType, 
                  skipped: bool = False) -> None:
        """Increment counter for object type."""
        if skipped:
            self.skipped += 1
            return
            
        self.total_exported += 1
        
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


class AccessExporter:
    """Exports MS Access database objects to source files."""
    
    # File extensions for different object types
    EXTENSIONS = {
        AccessObjectType.FORM: ".form.vba",
        AccessObjectType.REPORT: ".report.vba",
        AccessObjectType.MODULE: ".bas",
        AccessObjectType.CLASS: ".cls",
        AccessObjectType.QUERY: ".sql",
        AccessObjectType.MACRO: ".macro",
        AccessObjectType.TABLE: ".json",
        AccessObjectType.TABLE_DATA: ".csv",
        AccessObjectType.REFERENCE: ".refs",
    }
    
    def __init__(
        self,
        access_file: Path,
        source_dir: Path,
        encoding: str = "utf-8",
        force_export: bool = False,
        include_table_data: Optional[List[str]] = None,
    ) -> None:
        """Initialize exporter.
        
        Args:
            access_file: Path to Access database file.
            source_dir: Directory for exported sources.
            encoding: Text encoding for exported files.
            force_export: Export all objects regardless of changes.
            include_table_data: List of table names to export data for.
        """
        self.access_file = Path(access_file)
        self.source_dir = Path(source_dir)
        self.encoding = encoding
        self.force_export = force_export
        self.include_table_data = include_table_data or []
        
        self.app = AccessApplication()
        self.index = IndexManager(self.source_dir)
        self.hasher = ContentHasher()
        self.stats = ExportStats()
        
        # Sanitize filename for directory creation
        self.db_name = self.access_file.stem
        
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize object name for use as filename.
        
        Args:
            name: Original object name.
            
        Returns:
            Sanitized filename-safe string.
        """
        # Replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, "_", name)
        return sanitized.strip()
    
    def _get_output_path(self, obj_info: ObjectInfo) -> Path:
        """Determine output path for object.
        
        Args:
            obj_info: Object information.
            
        Returns:
            Path for output file.
        """
        ext = self.EXTENSIONS.get(obj_info.object_type, ".txt")
        sanitized_name = self._sanitize_filename(obj_info.name)
        
        # Organize by type in subdirectories
        type_dir = self.source_dir / obj_info.object_type.value
        type_dir.mkdir(parents=True, exist_ok=True)
        
        return type_dir / f"{sanitized_name}{ext}"
    
    def _export_object(self, obj_info: ObjectInfo) -> bool:
        """Export single object to file.
        
        Args:
            obj_info: Object to export.
            
        Returns:
            True if exported/skipped successfully, False on error.
        """
        try:
            output_path = self._get_output_path(obj_info)
            
            # Get content from Access
            content = self.app.export_object(obj_info)
            
            if content is None:
                logger.warning(
                    _("No content returned for {name}").format(
                        name=obj_info.name
                    )
                )
                return False
            
            # Check if changed
            if not self.force_export:
                if not self.index.has_changed(
                    obj_info.name, 
                    obj_info.object_type.value, 
                    content
                ):
                    logger.debug(
                        _("Skipping unchanged object: {name}").format(
                            name=obj_info.name
                        )
                    )
                    self.stats.increment(obj_info.object_type, skipped=True)
                    return True
            
            # Write file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle binary vs text content
            if isinstance(content, bytes):
                with open(output_path, "wb") as f:
                    f.write(content)
            else:
                # Convert UCS-2 to UTF-8 if needed (Access exports)
                if content.startswith("\ufeff"):
                    content = content[1:]
                
                with open(output_path, "w", encoding=self.encoding) as f:
                    f.write(content)
            
            # Update index
            self.index.update_entry(
                obj_info.name,
                obj_info.object_type.value,
                output_path,
                content if isinstance(content, str) else content.decode(
                    self.encoding, errors="replace"
                ),
            )
            
            self.stats.increment(obj_info.object_type)
            logger.info(
                _("Exported {type}: {name}").format(
                    type=obj_info.object_type.value,
                    name=obj_info.name,
                )
            )
            return True
            
        except Exception as e:
            logger.exception(
                _("Failed to export {name}: {error}").format(
                    name=obj_info.name,
                    error=e,
                )
            )
            self.stats.errors += 1
            return False
    
    def export_all(self) -> ExportStats:
        """Export all objects from database.
        
        Returns:
            Export statistics.
        """
        try:
            # Open database
            self.app.open_database(self.access_file)
            logger.info(
                _("Opened database: {file}").format(file=self.access_file)
            )
            
            # Export each object type
            object_types = [
                AccessObjectType.QUERY,
                AccessObjectType.FORM,
                AccessObjectType.REPORT,
                AccessObjectType.MODULE,
                AccessObjectType.CLASS,
                AccessObjectType.MACRO,
                AccessObjectType.TABLE,
            ]
            
            for obj_type in object_types:
                objects = self.app.get_objects(obj_type)
                logger.info(
                    _("Found {count} {type} objects").format(
                        count=len(objects),
                        type=obj_type.value,
                    )
                )
                
                for obj_info in objects:
                    self._export_object(obj_info)
            
            # Export references
            self._export_references()
            
            # Export project properties
            self._export_properties()
            
            # Save index
            self.index.save_index()
            
            return self.stats
            
        finally:
            self.app.close_database()
    
    def _export_references(self) -> None:
        """Export VBA references."""
        try:
            refs = self.app.get_references()
            if not refs:
                return
            
            content_lines = ["' VBA References", ""]
            for ref in refs:
                content_lines.append(
                    f"Reference: {ref.name}={ref.guid};{ref.major}.{ref.minor}"
                )
            
            content = "\n".join(content_lines)
            refs_path = self.source_dir / "references.refs"
            
            with open(refs_path, "w", encoding=self.encoding) as f:
                f.write(content)
            
            self.index.update_entry(
                "References", "Project", refs_path, content
            )
            logger.info(_("Exported references"))
            
        except Exception as e:
            logger.exception(
                _("Failed to export references: {error}").format(error=e)
            )
    
    def _export_properties(self) -> None:
        """Export database properties."""
        try:
            props = self.app.get_database_properties()
            
            content_lines = ["' Database Properties", ""]
            for prop_name, prop_value in props.items():
                content_lines.append(f"{prop_name}={prop_value}")
            
            content = "\n".join(content_lines)
            props_path = self.source_dir / "database.properties"
            
            with open(props_path, "w", encoding=self.encoding) as f:
                f.write(content)
            
            self.index.update_entry(
                "Properties", "Project", props_path, content
            )
            logger.info(_("Exported database properties"))
            
        except Exception as e:
            logger.exception(
                _("Failed to export properties: {error}").format(error=e)
            )