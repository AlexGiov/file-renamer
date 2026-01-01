"""
Local file operations implementation.

Handles file renaming on local filesystem (including UNC paths).
Uses native Python file operations.
"""

from __future__ import annotations
from pathlib import Path
import shutil
from typing import Optional
import logging

from ..protocols import FileOperationsProtocol
from .base import BaseFileRenamer


class LocalFileOperations:
    """
    File operations for local filesystem.
    
    Implements FileOperationsProtocol using native Python Path operations.
    Works with local paths and UNC paths (\\\\server\\share).
    
    Thread-safe and stateless.
    """
    
    def __init__(self):
        """Initialize local file operations."""
        self._logger = logging.getLogger(__name__)
    
    def rename_file(self, old_path: Path, new_path: Path) -> None:
        """
        Rename file on local filesystem.
        
        Args:
            old_path: Current file path
            new_path: Target file path
        
        Raises:
            IOError: If rename fails
        """
        try:
            old_path.rename(new_path)
        except OSError as e:
            self._logger.error(f"Failed to rename {old_path} to {new_path}: {e}")
            raise IOError(f"Rename failed: {e}") from e
    
    def file_exists(self, file_path: Path) -> bool:
        """Check if file exists on local filesystem."""
        return file_path.exists()
    
    def get_file_size(self, file_path: Path) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to file
        
        Returns:
            File size in bytes
        
        Raises:
            IOError: If file doesn't exist
        """
        try:
            return file_path.stat().st_size
        except OSError as e:
            raise IOError(f"Failed to get file size: {e}") from e
    
    def list_files(self, directory: Path, recursive: bool = False) -> list[Path]:
        """
        List files in directory (local filesystem).
        
        Args:
            directory: Directory to list
            recursive: Whether to recurse into subdirectories
        
        Returns:
            List of file paths (excluding directories)
        """
        files = []
        
        try:
            if recursive:
                # Use rglob for recursive listing
                for item in directory.rglob('*'):
                    if item.is_file():
                        files.append(item)
            else:
                # Use iterdir for non-recursive
                for item in directory.iterdir():
                    if item.is_file():
                        files.append(item)
        except OSError as e:
            self._logger.error(f"Failed to list directory {directory}: {e}")
        
        return files


class LocalFileRenamer(BaseFileRenamer):
    """
    File renamer for local filesystem.
    
    Extends BaseFileRenamer with local-specific implementations.
    Uses SHA256 for hashing (recommended for local files).
    
    Example:
        >>> from ..factory import FileRenamerFactory
        >>> renamer = FileRenamerFactory.create_local_renamer(verbose=True)
        >>> result = renamer.rename_file(Path("My File.TXT"))
        >>> if result.success:
        ...     print(f"Renamed to {result.new_path}")
    """
    
    def _perform_rename(self, old_path: Path, new_path: Path) -> None:
        """
        Perform rename on local filesystem.
        
        Uses native Path.rename() which works for local and UNC paths.
        
        Args:
            old_path: Current file path
            new_path: Target file path
        
        Raises:
            IOError: If rename fails
        """
        try:
            old_path.rename(new_path)
        except OSError as e:
            self._logger.error(f"Failed to rename {old_path} to {new_path}: {e}")
            raise IOError(f"Local rename failed: {e}") from e
    
    def _get_file_size(self, file_path: Path) -> int:
        """
        Get file size from local filesystem.
        
        Args:
            file_path: Local file path
        
        Returns:
            File size in bytes
        
        Raises:
            IOError: If file doesn't exist
        """
        try:
            return file_path.stat().st_size
        except OSError as e:
            raise IOError(f"Failed to get file size: {e}") from e
