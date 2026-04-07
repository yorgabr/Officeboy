"""
Unit tests for hasher module - target 100% coverage.
"""
import pytest
from pathlib import Path
import hashlib

from officeboy.core.hasher import calculate_hash, HashIndex


class TestCalculateHash:
    """Tests for calculate_hash function."""
    
    def test_calculate_hash_sha256(self, tmp_path):
        """Test SHA-256 hash calculation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        result = calculate_hash(test_file)
        
        expected = hashlib.sha256(test_content).hexdigest()
        assert result == expected
        assert len(result) == 64  # SHA-256 hex length
    
    def test_calculate_hash_empty_file(self, tmp_path):
        """Test hash of empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        result = calculate_hash(test_file)
        expected = hashlib.sha256(b"").hexdigest()
        
        assert result == expected
    
    def test_calculate_hash_large_file(self, tmp_path):
        """Test hash of large file (chunked reading)."""
        test_file = tmp_path / "large.bin"
        # Create file larger than 8192 bytes (chunk size)
        content = b"x" * 10000
        test_file.write_bytes(content)
        
        result = calculate_hash(test_file)
        expected = hashlib.sha256(content).hexdigest()
        
        assert result == expected
    
    def test_calculate_hash_binary_content(self, tmp_path):
        """Test hash with binary content."""
        test_file = tmp_path / "binary.dat"
        content = bytes(range(256))
        test_file.write_bytes(content)
        
        result = calculate_hash(test_file)
        expected = hashlib.sha256(content).hexdigest()
        
        assert result == expected
    
    def test_calculate_hash_nonexistent_file(self, tmp_path):
        """Test hash calculation for non-existent file raises error."""
        nonexistent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            calculate_hash(nonexistent)


class TestHashIndex:
    """Tests for HashIndex class."""
    
    def test_hash_index_initialization(self, tmp_path):
        """Test HashIndex initialization."""
        index_file = tmp_path / "index.json"
        
        index = HashIndex(index_file)
        
        assert index.index_file == index_file
        assert index.data == {}
    
    def test_hash_index_load_existing(self, tmp_path):
        """Test loading existing index."""
        index_file = tmp_path / "index.json"
        index_file.write_text('{"file1.txt": "hash1"}')
        
        index = HashIndex(index_file)
        index.load()
        
        assert index.data == {"file1.txt": "hash1"}
    
    def test_hash_index_load_nonexistent(self, tmp_path):
        """Test loading non-existent index creates empty."""
        index_file = tmp_path / "nonexistent" / "index.json"
        
        index = HashIndex(index_file)
        index.load()  # Should not raise
        
        assert index.data == {}
    
    def test_hash_index_save(self, tmp_path):
        """Test saving index."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        index.data = {"file1.txt": "hash1", "file2.txt": "hash2"}
        
        index.save()
        
        assert index_file.exists()
        content = index_file.read_text()
        assert "file1.txt" in content
        assert "hash1" in content
    
    def test_hash_index_save_creates_directory(self, tmp_path):
        """Test saving creates parent directories."""
        index_file = tmp_path / "nested" / "dir" / "index.json"
        index = HashIndex(index_file)
        index.data = {"test": "value"}
        
        index.save()
        
        assert index_file.exists()
    
    def test_hash_index_update(self, tmp_path):
        """Test updating hash for file."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        
        index.update("file1.txt", "abc123")
        
        assert index.data["file1.txt"] == "abc123"
    
    def test_hash_index_get(self, tmp_path):
        """Test getting hash for file."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        index.data = {"file1.txt": "hash123"}
        
        result = index.get("file1.txt")
        
        assert result == "hash123"
    
    def test_hash_index_get_missing(self, tmp_path):
        """Test getting hash for non-existent file."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        
        result = index.get("missing.txt")
        
        assert result is None
    
    def test_hash_index_remove(self, tmp_path):
        """Test removing file from index."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        index.data = {"file1.txt": "hash1", "file2.txt": "hash2"}
        
        index.remove("file1.txt")
        
        assert "file1.txt" not in index.data
        assert "file2.txt" in index.data
    
    def test_hash_index_remove_missing(self, tmp_path):
        """Test removing non-existent file doesn't raise."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        index.data = {"file1.txt": "hash1"}
        
        index.remove("missing.txt")  # Should not raise
        
        assert index.data == {"file1.txt": "hash1"}
    
    def test_hash_index_clear(self, tmp_path):
        """Test clearing all entries."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        index.data = {"file1.txt": "hash1", "file2.txt": "hash2"}
        
        index.clear()
        
        assert index.data == {}
    
    def test_hash_index_contains(self, tmp_path):
        """Test checking if file is in index."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        index.data = {"file1.txt": "hash1"}
        
        assert "file1.txt" in index
        assert "file2.txt" not in index
    
    def test_hash_index_iter(self, tmp_path):
        """Test iterating over index."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        index.data = {"a.txt": "1", "b.txt": "2"}
        
        keys = list(index)
        
        assert sorted(keys) == ["a.txt", "b.txt"]
    
    def test_hash_index_len(self, tmp_path):
        """Test getting index size."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        index.data = {"a.txt": "1", "b.txt": "2", "c.txt": "3"}
        
        assert len(index) == 3
    
    def test_hash_index_is_changed_true(self, tmp_path):
        """Test detecting changed file."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        index.data = {"file.txt": "old_hash"}
        
        is_changed = index.is_changed("file.txt", "new_hash")
        
        assert is_changed is True
    
    def test_hash_index_is_changed_false(self, tmp_path):
        """Test detecting unchanged file."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        index.data = {"file.txt": "same_hash"}
        
        is_changed = index.is_changed("file.txt", "same_hash")
        
        assert is_changed is False
    
    def test_hash_index_is_changed_new_file(self, tmp_path):
        """Test detecting new file (not in index)."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        
        is_changed = index.is_changed("new_file.txt", "any_hash")
        
        assert is_changed is True
    
    def test_hash_index_get_stats(self, tmp_path):
        """Test getting index statistics."""
        index_file = tmp_path / "index.json"
        index = HashIndex(index_file)
        index.data = {"a.txt": "1", "b.txt": "2"}
        
        stats = index.get_stats()
        
        assert stats["total_files"] == 2
        assert "index_file" in stats