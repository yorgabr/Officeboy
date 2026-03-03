"""Hashing utilities for tracking object changes."""

import hashlib
from pathlib import Path
from typing import Union


class ContentHasher:
    """SHA-256 hasher for file content verification."""
    
    def __init__(self, block_size: int = 65536) -> None:
        """Initialize hasher with specified block size.
        
        Args:
            block_size: Size of blocks to read for large files.
        """
        self.block_size = block_size
    
    def hash_file(self, file_path: Union[str, Path]) -> str:
        """Calculate SHA-256 hash of file contents.
        
        Args:
            file_path: Path to the file to hash.
            
        Returns:
            Hexadecimal string of the SHA-256 hash.
        """
        sha256 = hashlib.sha256()
        path = Path(file_path)
        
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(self.block_size), b""):
                sha256.update(block)
        
        return sha256.hexdigest()
    
    def hash_string(self, content: str, encoding: str = "utf-8") -> str:
        """Calculate SHA-256 hash of string content.
        
        Args:
            content: String content to hash.
            encoding: Encoding to use for string conversion.
            
        Returns:
            Hexadecimal string of the SHA-256 hash.
        """
        sha256 = hashlib.sha256()
        sha256.update(content.encode(encoding))
        return sha256.hexdigest()
    
    def verify_file(self, file_path: Union[str, Path], expected_hash: str) -> bool:
        """Verify file matches expected hash.
        
        Args:
            file_path: Path to the file to verify.
            expected_hash: Expected SHA-256 hash.
            
        Returns:
            True if hash matches, False otherwise.
        """
        actual_hash = self.hash_file(file_path)
        return actual_hash.lower() == expected_hash.lower()
