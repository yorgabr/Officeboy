"""
Index management for tracking database objects.
"""
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime


@dataclass
class IndexEntry:
    """Entry in the database index."""
    path: str
    hash: str
    size: int
    modified: float
    object_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndexEntry':
        """Create from dictionary."""
        return cls(**data)


class IndexManager:
    """Manages index of exported database objects."""
    
    def __init__(self, index_file: Optional[Path] = None):
        self.index_file = index_file or Path(".officeboy/index.json")
        self.entries: Dict[str, IndexEntry] = {}
        self.load()
    
    def load(self) -> None:
        """Load index from file."""
        if not self.index_file.exists():
            self.entries = {}
            return
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.entries = {
                    k: IndexEntry.fromdict(v) if isinstance(v, dict) else v
                    for k, v in data.items()
                }
        except (json.JSONDecodeError, IOError):
            self.entries = {}
    
    def save(self) -> None:
        """Save index to file."""
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(
                {k: v.to_dict() if hasattr(v, 'to_dict') else v 
                 for k, v in self.entries.items()},
                f,
                indent=2
            )
    
    def add(self, path: str, output_dir: str, hash_value: Optional[str] = None) -> None:
        """Add entry to index."""
        from officeboy.core.hasher import calculate_hash
        
        path_obj = Path(path)
        
        if path_obj.exists():
            size = path_obj.stat().st_size
            modified = path_obj.stat().st_mtime
            hash_val = hash_value or calculate_hash(path_obj)
        else:
            size = 0
            modified = datetime.now().timestamp()
            hash_val = hash_value or ""
        
        self.entries[path] = IndexEntry(
            path=path,
            hash=hash_val,
            size=size,
            modified=modified,
            object_type="database"
        )
    
    def get(self, path: str) -> Optional[IndexEntry]:
        """Get entry by path."""
        return self.entries.get(path)
    
    def remove(self, path: str) -> None:
        """Remove entry."""
        if path in self.entries:
            del self.entries[path]
    
    def has_changed(self, path: str, current_hash: str) -> bool:
        """Check if path has different hash."""
        entry = self.get(path)
        if entry is None:
            return True
        return entry.hash != current_hash
    
    def get_all_paths(self) -> List[str]:
        """Get all tracked paths."""
        return list(self.entries.keys())
    
    def clear(self) -> None:
        """Clear all entries."""
        self.entries.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        total_size = sum(e.size for e in self.entries.values())
        return {
            "total_entries": len(self.entries),
            "total_size": total_size,
            "index_file": str(self.index_file)
        }