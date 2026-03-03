"""MS Access object definitions."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class AccessObjectType(Enum):
    """Types of MS Access objects."""
    
    FORM = "Forms"
    REPORT = "Reports"
    MODULE = "Modules"
    CLASS = "Classes"
    QUERY = "Queries"
    MACRO = "Macros"
    TABLE = "Tables"
    TABLE_DATA = "TableData"
    REFERENCE = "References"


@dataclass
class ObjectInfo:
    """Information about an Access object."""
    
    name: str
    object_type: AccessObjectType
    path: Optional[Path] = None
    date_modified: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


@dataclass
class ReferenceInfo:
    """Information about a VBA reference."""
    
    name: str
    guid: str
    major: int
    minor: int
    full_path: Optional[str] = None
    is_broken: bool = False


@dataclass
class FormControl:
    """Information about a form control."""
    
    name: str
    control_type: str
    properties: Dict[str, Any]
    event_handlers: Dict[str, str]


@dataclass
class FormInfo(ObjectInfo):
    """Extended information for forms."""
    
    controls: Optional[list] = None
    record_source: Optional[str] = None
    module_code: Optional[str] = None