"""MS Access application automation using pywin32."""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from officeboy.access.objects import (
    AccessObjectType,
    FormControl,
    FormInfo,
    ObjectInfo,
    ReferenceInfo,
)
from officeboy.i18n import get_text as _

logger = logging.getLogger(__name__)


class AccessApplication:
    """Wrapper for MS Access COM automation."""
    
    # Access object type constants
    AC_FORM = 2
    AC_MODULE = 5
    AC_MACRO = 4
    AC_REPORT = 3
    AC_QUERY = 1
    AC_TABLE = 0
    
    def __init__(self) -> None:
        """Initialize Access application interface."""
        self.app: Optional[Any] = None
        self.db: Optional[Any] = None
        self._is_open = False
        
    def _ensure_com_initialized(self) -> None:
        """Initialize COM for current thread."""
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass
    
    def _get_access_constant(self, obj_type: AccessObjectType) -> int:
        """Map AccessObjectType to Access constant.
        
        Args:
            obj_type: Internal object type.
            
        Returns:
            Access AcObjectType constant.
        """
        mapping = {
            AccessObjectType.FORM: self.AC_FORM,
            AccessObjectType.REPORT: self.AC_REPORT,
            AccessObjectType.MODULE: self.AC_MODULE,
            AccessObjectType.MACRO: self.AC_MACRO,
            AccessObjectType.QUERY: self.AC_QUERY,
            AccessObjectType.TABLE: self.AC_TABLE,
        }
        return mapping.get(obj_type, 0)
    
    def open_database(self, db_path: Union[str, Path]) -> None:
        """Open existing Access database.
        
        Args:
            db_path: Path to .accdb or .mdb file.
            
        Raises:
            RuntimeError: If Access is not available or cannot open file.
        """
        self._ensure_com_initialized()
        
        try:
            import win32com.client
            
            self.app = win32com.client.Dispatch("Access.Application")
            self.app.Visible = False
            self.app.DisplayAlerts = False
            
            db_path = Path(db_path).resolve()
            self.app.OpenCurrentDatabase(str(db_path))
            self.db = self.app.CurrentDb()
            self._is_open = True
            
            logger.debug(_("Opened database: {path}").format(path=db_path))
            
        except Exception as e:
            logger.exception(_("Failed to open Access database"))
            raise RuntimeError(
                _("Cannot open database {path}: {error}").format(
                    path=db_path,
                    error=e,
                )
            ) from e
    
    def create_database(self, db_path: Union[str, Path]) -> None:
        """Create new blank Access database.
        
        Args:
            db_path: Path for new database.
        """
        self._ensure_com_initialized()
        
        try:
            import win32com.client
            
            self.app = win32com.client.Dispatch("Access.Application")
            self.app.Visible = False
            self.app.DisplayAlerts = False
            
            db_path = Path(db_path).resolve()
            
            # Create new database
            # Access 2010+ format (accdb)
            self.app.NewCurrentDatabase(str(db_path))
            self.db = self.app.CurrentDb()
            self._is_open = True
            
            logger.debug(_("Created database: {path}").format(path=db_path))
            
        except Exception as e:
            logger.exception(_("Failed to create database"))
            raise RuntimeError(
                _("Cannot create database {path}: {error}").format(
                    path=db_path,
                    error=e,
                )
            ) from e
    
    def create_from_template(self, db_path: Union[str, Path], 
                             template: Union[str, Path]) -> None:
        """Create database from template.
        
        Args:
            db_path: Path for new database.
            template: Path to template database.
        """
        import shutil
        
        template_path = Path(template)
        db_path = Path(db_path)
        
        if not template_path.exists():
            raise FileNotFoundError(
                _("Template not found: {path}").format(path=template)
            )
        
        # Copy template
        shutil.copy2(template_path, db_path)
        
        # Open copy
        self.open_database(db_path)
    
    def close_database(self) -> None:
        """Close database and quit Access."""
        if self.app:
            try:
                self.app.CloseCurrentDatabase()
                self.app.Quit()
            except Exception as e:
                logger.warning(_("Error closing Access: {error}").format(error=e))
            finally:
                self.app = None
                self.db = None
                self._is_open = False
    
    def get_objects(self, obj_type: AccessObjectType) -> List[ObjectInfo]:
        """Get list of objects from database.
        
        Args:
            obj_type: Type of objects to retrieve.
            
        Returns:
            List of object information.
        """
        if not self._is_open:
            raise RuntimeError(_("Database not open"))
        
        objects = []
        
        try:
            if obj_type == AccessObjectType.QUERY:
                # QueryDefs
                for qd in self.db.QueryDefs:
                    if not qd.Name.startswith("~"):  # Skip system queries
                        objects.append(ObjectInfo(
                            name=qd.Name,
                            object_type=obj_type,
                        ))
                        
            elif obj_type == AccessObjectType.TABLE:
                # TableDefs (non-system)
                for td in self.db.TableDefs:
                    if not td.Name.startswith("MSys"):
                        objects.append(ObjectInfo(
                            name=td.Name,
                            object_type=obj_type,
                        ))
                        
            elif obj_type in (AccessObjectType.FORM, AccessObjectType.REPORT,
                             AccessObjectType.MODULE, AccessObjectType.MACRO):
                # Containers
                container_name = obj_type.value
                try:
                    container = self.db.Containers(container_name)
                    for doc in container.Documents:
                        if not doc.Name.startswith("~"):
                            objects.append(ObjectInfo(
                                name=doc.Name,
                                object_type=obj_type,
                            ))
                except Exception as e:
                    logger.warning(
                        _("Cannot access {type}: {error}").format(
                            type=container_name,
                            error=e,
                        )
                    )
                    
            elif obj_type == AccessObjectType.CLASS:
                # Class modules are in Modules container but need filtering
                try:
                    container = self.db.Containers("Modules")
                    for doc in container.Documents:
                        if not doc.Name.startswith("~"):
                            # Check if it's a class module
                            # This is a heuristic - in practice, we'd need
                            # to inspect the module
                            objects.append(ObjectInfo(
                                name=doc.Name,
                                object_type=obj_type,
                            ))
                except Exception as e:
                    logger.warning(
                        _("Cannot access classes: {error}").format(error=e)
                    )
                    
        except Exception as e:
            logger.exception(
                _("Error getting objects of type {type}").format(
                    type=obj_type.value
                )
            )
        
        return objects
    
    def export_object(self, obj_info: ObjectInfo) -> Optional[str]:
        """Export object to text.
        
        Args:
            obj_info: Object to export.
            
        Returns:
            Text content of object, or None if failed.
        """
        if not self._is_open:
            raise RuntimeError(_("Database not open"))
        
        try:
            ac_type = self._get_access_constant(obj_info.object_type)
            
            if ac_type == 0:
                # Handle special cases
                if obj_info.object_type == AccessObjectType.TABLE:
                    return self._export_table_schema(obj_info.name)
                return None
            
            # Use SaveAsText for most objects
            import tempfile
            import os
            
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                delete=False,
                encoding="utf-8",
            )
            temp_path = temp_file.name
            temp_file.close()
            
            try:
                self.app.SaveAsText(
                    ac_type,
                    obj_info.name,
                    temp_path,
                )
                
                # Read content
                with open(temp_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                return content
                
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.exception(
                _("Error exporting {name}").format(name=obj_info.name)
            )
            return None
    
    def _export_table_schema(self, table_name: str) -> str:
        """Export table schema as JSON-like structure.
        
        Args:
            table_name: Name of table.
            
        Returns:
            JSON string with table structure.
        """
        import json
        
        td = self.db.TableDefs(table_name)
        
        schema = {
            "name": table_name,
            "columns": [],
            "indexes": [],
            "properties": {},
        }
        
        # Columns
        for field in td.Fields:
            col = {
                "name": field.Name,
                "type": field.Type,
                "size": field.Size,
                "required": field.Required,
                "allow_zero_length": getattr(field, "AllowZeroLength", False),
            }
            schema["columns"].append(col)
        
        # Indexes
        for idx in td.Indexes:
            index = {
                "name": idx.Name,
                "fields": [f.Name for f in idx.Fields],
                "primary": idx.Primary,
                "unique": idx.Unique,
            }
            schema["indexes"].append(index)
        
        return json.dumps(schema, indent=2)
    
    def import_object(self, obj_info: ObjectInfo, content: str) -> bool:
        """Import object from text.
        
        Args:
            obj_info: Object information.
            content: Text content to import.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self._is_open:
            raise RuntimeError(_("Database not open"))
        
        try:
            ac_type = self._get_access_constant(obj_info.object_type)
            
            if ac_type == 0:
                if obj_info.object_type == AccessObjectType.TABLE:
                    return self._import_table_schema(obj_info.name, content)
                return False
            
            # Write to temp file
            import tempfile
            import os
            
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                delete=False,
                encoding="utf-8",
            )
            temp_file.write(content)
            temp_path = temp_file.name
            temp_file.close()
            
            try:
                # Delete existing object if present
                try:
                    self.app.DoCmd.DeleteObject(ac_type, obj_info.name)
                except:
                    pass  # Object didn't exist
                
                # Import
                self.app.LoadFromText(
                    ac_type,
                    obj_info.name,
                    temp_path,
                )
                
                return True
                
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.exception(
                _("Error importing {name}").format(name=obj_info.name)
            )
            return False
    
    def _import_table_schema(self, table_name: str, content: str) -> bool:
        """Import table schema from JSON.
        
        Args:
            table_name: Name of table.
            content: JSON content.
            
        Returns:
            True if successful.
        """
        import json
        
        try:
            schema = json.loads(content)
            
            # Create table
            td = self.db.CreateTableDef(table_name)
            
            # Add fields
            for col in schema.get("columns", []):
                field = td.CreateField(
                    col["name"],
                    col["type"],
                    col.get("size", 0),
                )
                field.Required = col.get("required", False)
                if hasattr(field, "AllowZeroLength"):
                    field.AllowZeroLength = col.get("allow_zero_length", False)
                td.Fields.Append(field)
            
            self.db.TableDefs.Append(td)
            
            # Add indexes
            for idx_data in schema.get("indexes", []):
                idx = td.CreateIndex(idx_data["name"])
                idx.Primary = idx_data.get("primary", False)
                idx.Unique = idx_data.get("unique", False)
                
                for field_name in idx_data.get("fields", []):
                    idx.Fields.Append(field_name)
                
                td.Indexes.Append(idx)
            
            return True
            
        except Exception as e:
            logger.exception(
                _("Error importing table {name}").format(name=table_name)
            )
            return False
    
    def get_references(self) -> List[ReferenceInfo]:
        """Get VBA references.
        
        Returns:
            List of reference information.
        """
        if not self._is_open:
            return []
        
        refs = []
        try:
            vb_proj = self.app.VBE.ActiveVBProject
            for ref in vb_proj.References:
                refs.append(ReferenceInfo(
                    name=ref.Name,
                    guid=ref.Guid if hasattr(ref, "Guid") else "",
                    major=ref.Major,
                    minor=ref.Minor,
                    full_path=getattr(ref, "FullPath", None),
                    is_broken=ref.IsBroken,
                ))
        except Exception as e:
            logger.warning(_("Cannot get references: {error}").format(error=e))
        
        return refs
    
    def set_references(self, refs: List[Dict[str, Any]]) -> None:
        """Set VBA references.
        
        Args:
            refs: List of reference dictionaries.
        """
        if not self._is_open:
            return
        
        try:
            vb_proj = self.app.VBE.ActiveVBProject
            
            # Remove existing non-built-in references
            for ref in list(vb_proj.References):
                if not ref.BuiltIn:
                    try:
                        vb_proj.References.Remove(ref)
                    except:
                        pass
            
            # Add new references
            for ref_data in refs:
                try:
                    if ref_data.get("guid"):
                        vb_proj.References.AddFromGuid(
                            ref_data["guid"],
                            ref_data["major"],
                            ref_data["minor"],
                        )
                    elif ref_data.get("path"):
                        vb_proj.References.AddFromFile(ref_data["path"])
                except Exception as e:
                    logger.warning(
                        _("Cannot add reference {name}: {error}").format(
                            name=ref_data.get("name", "unknown"),
                            error=e,
                        )
                    )
                    
        except Exception as e:
            logger.exception(_("Error setting references: {error}").format(error=e))
    
    def get_database_properties(self) -> Dict[str, Any]:
        """Get database properties.
        
        Returns:
            Dictionary of properties.
        """
        if not self._is_open:
            return {}
        
        props = {}
        try:
            for prop in self.db.Properties:
                try:
                    props[prop.Name] = prop.Value
                except:
                    props[prop.Name] = None
        except Exception as e:
            logger.warning(
                _("Cannot get properties: {error}").format(error=e)
            )
        
        return props
    
    def set_database_properties(self, props: Dict[str, Any]) -> None:
        """Set database properties.
        
        Args:
            props: Dictionary of properties.
        """
        if not self._is_open:
            return
        
        for name, value in props.items():
            try:
                try:
                    self.db.Properties[name].Value = value
                except KeyError:
                    # Property doesn't exist, create it
                    from win32com.client import constants
                    prop = self.db.CreateProperty(
                        name,
                        constants.dbText,
                        value,
                    )
                    self.db.Properties.Append(prop)
            except Exception as e:
                logger.warning(
                    _("Cannot set property {name}: {error}").format(
                        name=name,
                        error=e,
                    )
                )
    
    def compile_vba(self) -> None:
        """Compile all VBA code."""
        if not self._is_open:
            return
        
        try:
            # RunCommand acCmdCompileAllModules = 7
            self.app.RunCommand(7)
            logger.info(_("Compiled VBA code"))
        except Exception as e:
            logger.warning(_("Cannot compile VBA: {error}").format(error=e))
    
    def get_form_info(self, form_name: str) -> Optional[FormInfo]:
        """Get detailed form information including controls.
        
        Args:
            form_name: Name of form.
            
        Returns:
            FormInfo with controls, or None.
        """
        if not self._is_open:
            return None
        
        try:
            # Open form in design view
            self.app.DoCmd.OpenForm(
                form_name,
                View=1,  # Design view
                WindowMode=2,  # Hidden
            )
            
            form = self.app.Forms(form_name)
            
            controls = []
            for ctl in form.Controls:
                events = {}
                
                # Get event handlers
                for event_name in ["OnClick", "OnDblClick", "OnLoad", 
                                  "OnOpen", "OnClose", "AfterUpdate"]:
                    try:
                        handler = getattr(ctl, event_name, None)
                        if handler and str(handler).startswith("="):
                            # Macro or expression
                            events[event_name] = str(handler)
                        elif handler:
                            # VBA procedure
                            events[event_name] = str(handler)
                    except:
                        pass
                
                controls.append(FormControl(
                    name=ctl.Name,
                    control_type=ctl.ControlType,
                    properties={},  # Could expand to include relevant props
                    event_handlers=events,
                ))
            
            self.app.DoCmd.Close(2, form_name)  # acForm = 2
            
            return FormInfo(
                name=form_name,
                object_type=AccessObjectType.FORM,
                controls=controls,
                record_source=getattr(form, "RecordSource", None),
            )
            
        except Exception as e:
            logger.exception(
                _("Error getting form info for {name}").format(name=form_name)
            )
            return None
    
    def __enter__(self) -> "AccessApplication":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close_database()