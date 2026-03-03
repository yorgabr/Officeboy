"""Index management for tracking exported objects."""

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Optional

from officeboy.core.hasher import ContentHasher

logger = logging.getLogger(__name__)


@dataclass
class ObjectEntry:
    """Entry for a single exported object."""
    
    name: str
    object_type: str
    file_path: str
    hash: str
    last_modified: str
    size: int


@dataclass
class ExportIndex:
    """Index of all exported objects."""
    
    version: str = "1.0"
    database_path: str = ""
    entries: Dict[str, ObjectEntry] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert index to dictionary."""
        return {
            "version": self.version,
            "database_path": self.database_path,
            "entries": {
                k: asdict(v) for k, v in self.entries.items()
            },
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExportIndex":
        """Create index from dictionary."""
        entries = {
            k: ObjectEntry(**v) for k, v in data.get("entries", {}).items()
        }
        return cls(
            version=data.get("version", "1.0"),
            database_path=data.get("database_path", ""),
            entries=entries,
        )


class IndexManager:
    """Manages the export index file."""
    
    INDEX_FILENAME = "officeboy.index.json"
    
    def __init__(self, source_dir: Path) -> None:
        """Initialize index manager.
        
        Args:
            source_dir: Directory containing exported sources.
        """
        self.source_dir = Path(source_dir)
        self.index_path = self.source_dir / self.INDEX_FILENAME
        self.index: ExportIndex = ExportIndex()
        self.hasher = ContentHasher()
        self._load_index()
    
    def _load_index(self) -> None:
        """Load existing index if present."""
        if self.index_path.exists():
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.index = ExportIndex.from_dict(data)
                logger.debug(_("Loaded existing index with {count} entries").format(
                    count=len(self.index.entries)
                ))
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(_("Failed to load index: {error}").format(error=e))
                self.index = ExportIndex()
    
    def save_index(self) -> None:
        """Save current index to disk."""
        self.source_dir.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self.index.to_dict(), f, indent=2)
        logger.debug(_("Saved index with {count} entries").format(
            count=len(self.index.entries)
        ))
    
    def get_entry(self, object_name: str, object_type: str) -> Optional[ObjectEntry]:
        """Get index entry for an object.
        
        Args:
            object_name: Name of the object.
            object_type: Type of the object (Form, Module, etc.).
            
        Returns:
            ObjectEntry if found, None otherwise.
        """
        key = f"{object_type}:{object_name}"
        return self.index.entries.get(key)
    
    def has_changed(self, object_name: str, object_type: str, 
                    content: str) -> bool:
        """Check if object content has changed from indexed version.
        
        Args:
            object_name: Name of the object.
            object_type: Type of the object.
            content: Current content of the object.
            
        Returns:
            True if content has changed or not indexed, False otherwise.
        """
        entry = self.get_entry(object_name, object_type)
        if entry is None:
            return True
        
        current_hash = self.hasher.hash_string(content)
        return current_hash != entry.hash
    
    def update_entry(self, object_name: str, object_type: str,
                     file_path: Path, content: str) -> None:
        """Update or add index entry for an object.
        
        Args:
            object_name: Name of the object.
            object_type: Type of the object.
            file_path: Path where object is exported.
            content: Content of the object.
        """
        from datetime import datetime
        
        key = f"{object_type}:{object_name}"
        hash_value = self.hasher.hash_string(content)
        
        self.index.entries[key] = ObjectEntry(
            name=object_name,
            object_type=object_type,
            file_path=str(file_path.relative_to(self.source_dir)),
            hash=hash_value,
            last_modified=datetime.now().isoformat(),
            size=len(content.encode("utf-8")),
        )
    
    def remove_entry(self, object_name: str, object_type: str) -> None:
        """Remove entry from index.
        
        Args:
            object_name: Name of the object.
            object_type: Type of the object.
        """
        key = f"{object_type}:{object_name}"
        if key in self.index.entries:
            del self.index.entries[key]
    
    def get_all_entries(self) -> Dict[str, ObjectEntry]:
        """Get all index entries.
        
        Returns:
            Dictionary of all entries keyed by type:name.
        """
        return self.index.entries.copy()