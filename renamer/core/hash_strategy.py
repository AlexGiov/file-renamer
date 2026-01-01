"""
Hash computation strategies.

Strategy pattern implementation for different hash algorithms.
Fixes the algorithm inconsistency: allows choosing SHA256 or MD5 explicitly.
"""

from __future__ import annotations
import hashlib
import subprocess
from pathlib import Path
from typing import Optional
import logging


class SHA256HashComputer:
    """
    Compute SHA256 hashes for local files.
    
    Used for local filesystem operations where SHA256 is preferred
    for better collision resistance.
    
    Thread-safe and stateless.
    
    Example:
        >>> computer = SHA256HashComputer()
        >>> hash_value = computer.compute_hash(Path("file.txt"))
        >>> computer.algorithm_name
        'sha256'
    """
    
    def __init__(self, chunk_size: int = 8192):
        """
        Initialize SHA256 hash computer.
        
        Args:
            chunk_size: Bytes to read per iteration (default 8KB)
        """
        self._chunk_size = chunk_size
        self._logger = logging.getLogger(__name__)
    
    def compute_hash(self, file_path: Path) -> str:
        """
        Compute SHA256 hash of file contents.
        
        Args:
            file_path: Path to local file
        
        Returns:
            Hexadecimal SHA256 hash string
        
        Raises:
            IOError: If file cannot be read
        """
        sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(self._chunk_size):
                    sha256.update(chunk)
            
            hash_value = sha256.hexdigest()
            self._logger.debug(f"SHA256 hash computed for {file_path}: {hash_value}")
            return hash_value
            
        except IOError as e:
            self._logger.error(f"Failed to compute SHA256 hash for {file_path}: {e}")
            raise
    
    @property
    def algorithm_name(self) -> str:
        """Return algorithm name for sidecar metadata."""
        return 'sha256'


class MD5HashComputer:
    """
    Compute MD5 hashes for remote files via rclone.
    
    Used for Google Drive and other remotes where rclone provides MD5.
    While MD5 is cryptographically weak, it's sufficient for file integrity
    verification and is what rclone returns for most cloud providers.
    
    Thread-safe and stateless.
    
    Example:
        >>> computer = MD5HashComputer()
        >>> hash_value = computer.compute_hash(Path("agdrive:folder/file.txt"))
        >>> computer.algorithm_name
        'md5'
    """
    
    def __init__(self, rclone_path: Optional[Path] = None):
        """
        Initialize MD5 hash computer.
        
        Args:
            rclone_path: Path to rclone executable (uses 'rclone' if None)
        """
        self._rclone = str(rclone_path) if rclone_path else 'rclone'
        self._logger = logging.getLogger(__name__)
    
    def compute_hash(self, file_path: Path) -> str:
        """
        Compute MD5 hash via rclone md5sum.
        
        Args:
            file_path: Remote path (e.g., 'agdrive:folder/file.txt')
        
        Returns:
            Hexadecimal MD5 hash string
        
        Raises:
            IOError: If rclone fails or file doesn't exist
        """
        cmd = [self._rclone, 'md5sum', str(file_path)]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )
            
            # Parse output: "hash  filename"
            output = result.stdout.strip()
            if output:
                hash_value = output.split()[0]
                self._logger.debug(f"MD5 hash computed for {file_path}: {hash_value}")
                return hash_value
            else:
                raise IOError(f"No MD5 hash returned for {file_path}")
                
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            self._logger.error(f"rclone md5sum failed for {file_path}: {error_msg}")
            raise IOError(f"Failed to compute MD5 hash: {error_msg}") from e
        except Exception as e:
            self._logger.error(f"Unexpected error computing MD5 for {file_path}: {e}")
            raise IOError(f"Failed to compute MD5 hash: {e}") from e
    
    @property
    def algorithm_name(self) -> str:
        """Return algorithm name for sidecar metadata."""
        return 'md5'


# Convenience function to choose hasher based on path type
def get_hash_computer(
    is_remote: bool,
    rclone_path: Optional[Path] = None
) -> SHA256HashComputer | MD5HashComputer:
    """
    Factory function to get appropriate hash computer.
    
    Args:
        is_remote: True for remote paths, False for local
        rclone_path: Path to rclone (for remote only)
    
    Returns:
        SHA256HashComputer for local, MD5HashComputer for remote
    
    Example:
        >>> hasher = get_hash_computer(is_remote=False)
        >>> isinstance(hasher, SHA256HashComputer)
        True
        >>> hasher = get_hash_computer(is_remote=True)
        >>> isinstance(hasher, MD5HashComputer)
        True
    """
    if is_remote:
        return MD5HashComputer(rclone_path=rclone_path)
    else:
        return SHA256HashComputer()
