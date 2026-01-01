"""
Protocol interfaces for file renaming operations.

Following PEP 544 (Protocol - Structural Subtyping), these define contracts
without inheritance, enabling flexible dependency injection and testing.

All protocols use @runtime_checkable for isinstance() checks.
"""

from __future__ import annotations
from pathlib import Path
from typing import Protocol, runtime_checkable, Optional

from .domain.models import RenameResult, FileMetadata, SidecarContent


@runtime_checkable
class HashComputerProtocol(Protocol):
    """
    Protocol for computing file hashes.
    
    Strategy pattern interface for different hash algorithms (SHA256, MD5).
    Implementations must be stateless and thread-safe.
    
    Example:
        >>> class SHA256HashComputer:
        ...     def compute_hash(self, file_path: Path) -> str:
        ...         # ... implementation
        ...
        >>> hasher: HashComputerProtocol = SHA256HashComputer()
    """
    
    def compute_hash(self, file_path: Path) -> str:
        """
        Compute hash of file contents.
        
        Args:
            file_path: Path to file (local path or remote path string)
        
        Returns:
            Hexadecimal hash string
        
        Raises:
            IOError: If file cannot be read
        """
        ...
    
    @property
    def algorithm_name(self) -> str:
        """
        Return hash algorithm name ('sha256' or 'md5').
        
        Returns:
            Lowercase algorithm name for sidecar metadata
        """
        ...


@runtime_checkable
class SidecarWriterProtocol(Protocol):
    """
    Protocol for writing sidecar .meta.json files.
    
    Abstracts the persistence mechanism (local filesystem, rclone, etc.).
    
    Example:
        >>> class LocalSidecarWriter:
        ...     def write_sidecar(self, file_path: Path, content: SidecarContent) -> Path:
        ...         # ... implementation
        ...
        >>> writer: SidecarWriterProtocol = LocalSidecarWriter()
    """
    
    def write_sidecar(
        self,
        file_path: Path,
        content: SidecarContent
    ) -> Path:
        """
        Write sidecar .meta.json file for a renamed file.
        
        Args:
            file_path: Path to the renamed file
            content: Sidecar content to write
        
        Returns:
            Path to created sidecar file
        
        Raises:
            IOError: If sidecar cannot be written
        """
        ...
    
    def read_sidecar(self, file_path: Path) -> Optional[SidecarContent]:
        """
        Read existing sidecar .meta.json file if it exists.
        
        Args:
            file_path: Path to check for sidecar
        
        Returns:
            SidecarContent if sidecar exists and is valid, None otherwise
        """
        ...


@runtime_checkable
class FileOperationsProtocol(Protocol):
    """
    Protocol for file operations (rename, copy, delete).
    
    Abstracts local vs remote file operations, enabling polymorphic behavior.
    
    Example:
        >>> class LocalFileOperations:
        ...     def rename_file(self, old_path: Path, new_path: Path) -> None:
        ...         # ... implementation
        ...
        >>> ops: FileOperationsProtocol = LocalFileOperations()
    """
    
    def rename_file(self, old_path: Path, new_path: Path) -> None:
        """
        Rename/move a file.
        
        Args:
            old_path: Current file path
            new_path: Target file path
        
        Raises:
            IOError: If rename fails
        """
        ...
    
    def file_exists(self, file_path: Path) -> bool:
        """
        Check if file exists.
        
        Args:
            file_path: Path to check
        
        Returns:
            True if file exists
        """
        ...
    
    def get_file_size(self, file_path: Path) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to file
        
        Returns:
            File size in bytes
        
        Raises:
            IOError: If file doesn't exist or can't be accessed
        """
        ...
    
    def list_files(self, directory: Path, recursive: bool = False) -> list[Path]:
        """
        List files in directory.
        
        Args:
            directory: Directory to list
            recursive: Whether to recurse into subdirectories
        
        Returns:
            List of file paths (excluding directories)
        """
        ...


@runtime_checkable
class FileRenamerProtocol(Protocol):
    """
    Protocol for file renaming operations.
    
    High-level interface for renaming files according to safe naming rules.
    Implementations handle local or remote filesystems.
    
    Example:
        >>> renamer: FileRenamerProtocol = LocalFileRenamer(...)
        >>> result = renamer.rename_file(Path("Unsafe File.TXT"))
        >>> if result.success:
        ...     print(f"Renamed to {result.new_path}")
    """
    
    def rename_file(
        self,
        file_path: Path,
        dry_run: bool = False
    ) -> RenameResult:
        """
        Rename a single file to safe name.
        
        Args:
            file_path: Path to file to rename
            dry_run: If True, don't actually rename, just simulate
        
        Returns:
            RenameResult with operation outcome
        """
        ...
    
    def rename_directory(
        self,
        directory: Path,
        recursive: bool = True,
        dry_run: bool = False
    ) -> list[RenameResult]:
        """
        Rename all files in directory.
        
        Args:
            directory: Directory to process
            recursive: Whether to recurse into subdirectories
            dry_run: If True, don't actually rename, just simulate
        
        Returns:
            List of RenameResult for each file processed
        """
        ...
