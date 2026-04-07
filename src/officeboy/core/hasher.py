"""
Hashing utilities for tracking file changes.
"""
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Iterator


def calculate_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of file contents.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hex digest of SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(8192), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


class HashIndex:
    """
    Index for tracking file hashes to detect changes.
    """
    
    def __init__(self, index_file: Optional[Path] = None):
        self.index_file = index_file
        self.data: Dict[str, str] = {}
        
        if index_file:
            self.load()
    
    def load(self) -> None:
        """Load index from file."""
        if not self.index_file or not self.index_file.exists():
            self.data = {}
            return
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except (json.JSONDecodeError, IOError):
            self.data = {}
    
    def save(self) -> None:
        """Save index to file."""
        if not self.index_file:
            return
        
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)
    
    def update(self, path: str, hash_value: str) -> None:
        """Update hash for path."""
        self.data[path] = hash_value
    
    def get(self, path: str) -> Optional[str]:
        """Get hash for path."""
        return self.data.get(path)
    
    def remove(self, path: str) -> None:
        """Remove path from index."""
        if path in self.data:
            del self.data[path]
    
    def clear(self) -> None:
        """Clear all entries."""
        self.data.clear()
    
    def __contains__(self, path: str) -> bool:
        return path in self.data
    
    def __iter__(self) -> Iterator[str]:
        return iter(self.data.keys())
    
    def __len__(self) -> int:
        return len(self.data)
    
    def is_changed(self, path: str, current_hash: str) -> bool:
        """
        Check if file has changed compared to stored hash.
        
        Returns:
            True if file is new or changed, False if unchanged
        """
        stored_hash = self.get(path)
        if stored_hash is None:
            return True
        return stored_hash != current_hash
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        return {
            "total_files": len(self.data),
            "index_file": str(self.index_file) if self.index_file else None
        }