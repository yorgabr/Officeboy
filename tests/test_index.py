"""
Unit tests for index module - target 100% coverage.
"""
import pytest
from pathlib import Path
import json

from officeboy.core.index import IndexManager, IndexEntry


class TestIndexEntry:
    """Tests for IndexEntry dataclass."""
    
    def test_index_entry_creation(self):
        """Test creating IndexEntry."""
        entry = IndexEntry(
            path="test.txt",
            hash="abc123",
            size=100,
            modified=1234567890.0,
            object_type="table"
        )
        
        assert entry.path == "test.txt"
        assert entry.hash == "abc123"
        assert entry.size == 100
        assert entry.modified == 1234567890.0
        assert entry.object_type == "table"
    
    def test_index_entry_to_dict(self):
        """Test converting to dictionary."""
        entry = IndexEntry(
            path="test.txt",
            hash="abc123",
            size=100,
            modified=1234567890.0,
            object_type="table"
        )
        
        d = entry.to_dict()
        
        assert d == {
            "path": "test.txt",
            "hash": "abc123",
            "size": 100,
            "modified": 1234567890.0,
            "object_type": "table"
        }
    
    def test_index_entry_from_dict(self):
        """Test creating from dictionary."""
        d = {
            "path": "test.txt",
            "hash": "abc123",
            "size": 100,
            "modified": 1234567890.0,
            "object_type": "table"
        }
        
        entry = IndexEntry.from_dict(d)
        
        assert entry.path == "test.txt"
        assert entry.hash == "abc123"


class TestIndexManager:
    """Tests for IndexManager class."""
    
    def test_index_manager_initialization(self, tmp_path):
        """Test IndexManager initialization."""
        index_file = tmp_path / "index.json"
        
        manager = IndexManager(index_file)
        
        assert manager.index_file == index_file
        assert manager.entries == {}
    
    def test_index_manager_add_entry(self, tmp_path):
        """Test adding entry."""
        manager = IndexManager(tmp_path / "index.json")
        
        manager.add("test.txt", "hash123", 100, 1234567890.0, "table")
        
        assert "test.txt" in manager.entries
        entry = manager.entries["test.txt"]
        assert entry.hash == "hash123"
        assert entry.size == 100
    
    def test_index_manager_get_entry(self, tmp_path):
        """Test getting entry."""
        manager = IndexManager(tmp_path / "index.json")
        manager.add("test.txt", "hash123", 100, 1234567890.0, "table")
        
        entry = manager.get("test.txt")
        
        assert entry is not None
        assert entry.hash == "hash123"
    
    def test_index_manager_get_missing(self, tmp_path):
        """Test getting non-existent entry."""
        manager = IndexManager(tmp_path / "index.json")
        
        entry = manager.get("missing.txt")
        
        assert entry is None
    
    def test_index_manager_remove_entry(self, tmp_path):
        """Test removing entry."""
        manager = IndexManager(tmp_path / "index.json")
        manager.add("test.txt", "hash123", 100, 1234567890.0, "table")
        
        manager.remove("test.txt")
        
        assert "test.txt" not in manager.entries
    
    def test_index_manager_has_changed_true(self, tmp_path):
        """Test detecting changed file."""
        manager = IndexManager(tmp_path / "index.json")
        manager.add("test.txt", "old_hash", 100, 1234567890.0, "table")
        
        changed = manager.has_changed("test.txt", "new_hash")
        
        assert changed is True
    
    def test_index_manager_has_changed_false(self, tmp_path):
        """Test detecting unchanged file."""
        manager = IndexManager(tmp_path / "index.json")
        manager.add("test.txt", "same_hash", 100, 1234567890.0, "table")
        
        changed = manager.has_changed("test.txt", "same_hash")
        
        assert changed is False
    
    def test_index_manager_has_changed_new_file(self, tmp_path):
        """Test detecting new file."""
        manager = IndexManager(tmp_path / "index.json")
        
        changed = manager.has_changed("new.txt", "hash")
        
        assert changed is True
    
    def test_index_manager_save_load(self, tmp_path):
        """Test saving and loading index."""
        index_file = tmp_path / "index.json"
        manager = IndexManager(index_file)
        manager.add("test.txt", "hash123", 100, 1234567890.0, "table")
        
        manager.save()
        
        # Load in new manager
        new_manager = IndexManager(index_file)
        new_manager.load()
        
        assert "test.txt" in new_manager.entries
        assert new_manager.entries["test.txt"].hash == "hash123"
    
    def test_index_manager_load_nonexistent(self, tmp_path):
        """Test loading non-existent file."""
        manager = IndexManager(tmp_path / "nonexistent.json")
        
        manager.load()  # Should not raise
        
        assert manager.entries == {}
    
    def test_index_manager_get_all_paths(self, tmp_path):
        """Test getting all paths."""
        manager = IndexManager(tmp_path / "index.json")
        manager.add("a.txt", "hash1", 100, 1.0, "table")
        manager.add("b.txt", "hash2", 200, 2.0, "form")
        
        paths = manager.get_all_paths()
        
        assert sorted(paths) == ["a.txt", "b.txt"]
    
    def test_index_manager_clear(self, tmp_path):
        """Test clearing index."""
        manager = IndexManager(tmp_path / "index.json")
        manager.add("test.txt", "hash123", 100, 1234567890.0, "table")
        
        manager.clear()
        
        assert manager.entries == {}
    
    def test_index_manager_get_stats(self, tmp_path):
        """Test getting statistics."""
        manager = IndexManager(tmp_path / "index.json")
        manager.add("a.txt", "hash1", 100, 1.0, "table")
        manager.add("b.txt", "hash2", 200, 2.0, "form")
        
        stats = manager.get_stats()
        
        assert stats["total_entries"] == 2
        assert stats["total_size"] == 300
        assert "index_file" in stats