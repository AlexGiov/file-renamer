"""
Factory for creating file renamer instances with dependency injection.

Centralizes object creation and wiring of dependencies.
Follows Factory pattern and Dependency Injection principle.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional
import re

from .domain.models import OperationStats
from .protocols import FileRenamerProtocol
from .core.hash_strategy import SHA256HashComputer, MD5HashComputer
from .core.sidecar import (
    LocalSidecarWriter,
    RcloneSidecarWriter,
    SidecarManager
)
from .core.sanitizer import FilenameSanitizer
from .operations.local import LocalFileRenamer, LocalFileOperations
from .operations.remote import RemoteFileRenamer, RemoteFileOperations


class FileRenamerFactory:
    """
    Factory for creating FileRenamer instances.
    
    Handles dependency injection and wiring of all components.
    Detects path type (local vs remote) automatically.
    
    Example:
        >>> # Auto-detect path type
        >>> renamer = FileRenamerFactory.create_from_path(
        ...     Path("C:/folder"),
        ...     verbose=True
        ... )
        >>> isinstance(renamer, LocalFileRenamer)
        True
        
        >>> renamer = FileRenamerFactory.create_from_path(
        ...     Path("agdrive:folder"),
        ...     verbose=True
        ... )
        >>> isinstance(renamer, RemoteFileRenamer)
        True
    """
    
    @staticmethod
    def is_remote_path(path: Path | str) -> bool:
        """
        Detect if path is remote (contains ':' pattern).
        
        Remote paths: 'agdrive:', 's3:', 'dropbox:', etc.
        Local paths: 'C:\\folder', '/home/user', '\\\\server\\share'
        
        Args:
            path: Path to check
        
        Returns:
            True if remote path (contains ':' in remote format)
        
        Example:
            >>> FileRenamerFactory.is_remote_path(Path("agdrive:folder"))
            True
            >>> FileRenamerFactory.is_remote_path(Path("C:\\folder"))
            False
            >>> FileRenamerFactory.is_remote_path(Path("\\\\server\\share"))
            False
        """
        path_str = str(path)
        
        # Pattern: word characters followed by colon, NOT followed by backslash
        # Matches: "agdrive:", "s3:", "dropbox:"
        # Excludes: "C:\", "D:\"
        remote_pattern = r'^[a-zA-Z][\w-]*:(?![\\\/])'
        
        return bool(re.match(remote_pattern, path_str))
    
    @staticmethod
    def create_local_renamer(
        verbose: bool = False,
        sanitizer: Optional[FilenameSanitizer] = None
    ) -> LocalFileRenamer:
        """
        Create renamer for local filesystem.
        
        Wires up:
        - SHA256HashComputer (recommended for local)
        - LocalSidecarWriter
        - LocalFileOperations
        - FilenameSanitizer
        
        Args:
            verbose: Enable verbose logging
            sanitizer: Custom sanitizer (creates default if None)
        
        Returns:
            Configured LocalFileRenamer instance
        
        Example:
            >>> renamer = FileRenamerFactory.create_local_renamer(verbose=True)
            >>> result = renamer.rename_file(Path("My File.TXT"))
        """
        # Create dependencies
        hasher = SHA256HashComputer()
        sidecar_writer = LocalSidecarWriter()
        file_ops = LocalFileOperations()
        sanitizer = sanitizer or FilenameSanitizer()
        
        # Wire up renamer with dependency injection
        return LocalFileRenamer(
            hasher=hasher,
            sidecar_writer=sidecar_writer,
            file_operations=file_ops,
            sanitizer=sanitizer,
            verbose=verbose
        )
    
    @staticmethod
    def create_remote_renamer(
        rclone_path: Optional[Path] = None,
        verbose: bool = False,
        sanitizer: Optional[FilenameSanitizer] = None
    ) -> RemoteFileRenamer:
        """
        Create renamer for remote filesystem via rclone.
        
        Wires up:
        - MD5HashComputer (what rclone returns)
        - RcloneSidecarWriter
        - RemoteFileOperations
        - FilenameSanitizer
        
        Args:
            rclone_path: Path to rclone executable (uses 'rclone' if None)
            verbose: Enable verbose logging
            sanitizer: Custom sanitizer (creates default if None)
        
        Returns:
            Configured RemoteFileRenamer instance
        
        Example:
            >>> renamer = FileRenamerFactory.create_remote_renamer(verbose=True)
            >>> result = renamer.rename_file(Path("agdrive:folder/My File.TXT"))
        """
        # Create dependencies
        hasher = MD5HashComputer(rclone_path=rclone_path)
        sidecar_writer = RcloneSidecarWriter(rclone_path=rclone_path)
        file_ops = RemoteFileOperations(rclone_path=rclone_path)
        sanitizer = sanitizer or FilenameSanitizer()
        
        # Wire up renamer with dependency injection
        return RemoteFileRenamer(
            hasher=hasher,
            sidecar_writer=sidecar_writer,
            file_operations=file_ops,
            sanitizer=sanitizer,
            verbose=verbose,
            rclone_path=rclone_path
        )
    
    @staticmethod
    def create_from_path(
        path: Path | str,
        rclone_path: Optional[Path] = None,
        verbose: bool = False,
        sanitizer: Optional[FilenameSanitizer] = None
    ) -> FileRenamerProtocol:
        """
        Create renamer by auto-detecting path type.
        
        Convenience method that chooses local or remote based on path.
        
        Args:
            path: Path to analyze (local or remote)
            rclone_path: Path to rclone executable (for remote only)
            verbose: Enable verbose logging
            sanitizer: Custom sanitizer (creates default if None)
        
        Returns:
            LocalFileRenamer or RemoteFileRenamer based on path type
        
        Example:
            >>> # Auto-detects local
            >>> renamer = FileRenamerFactory.create_from_path(
            ...     Path("C:/folder"),
            ...     verbose=True
            ... )
            
            >>> # Auto-detects remote
            >>> renamer = FileRenamerFactory.create_from_path(
            ...     Path("agdrive:folder"),
            ...     verbose=True
            ... )
        """
        if FileRenamerFactory.is_remote_path(path):
            return FileRenamerFactory.create_remote_renamer(
                rclone_path=rclone_path,
                verbose=verbose,
                sanitizer=sanitizer
            )
        else:
            return FileRenamerFactory.create_local_renamer(
                verbose=verbose,
                sanitizer=sanitizer
            )


def print_stats(stats: OperationStats) -> None:
    """
    Print operation statistics to console.
    
    Extracted common function (DRY principle).
    
    Args:
        stats: Operation statistics to print
    """
    print(f"\n{'=' * 60}")
    print(f"Operation Summary")
    print(f"{'=' * 60}")
    print(f"Total files:    {stats.total_files}")
    print(f"Renamed:        {stats.renamed}")
    print(f"Skipped:        {stats.skipped}")
    print(f"Errors:         {stats.errors}")
    
    if stats.total_files > 0:
        success_rate = stats.success_rate * 100
        print(f"Success rate:   {success_rate:.1f}%")
    
    print(f"{'=' * 60}\n")
