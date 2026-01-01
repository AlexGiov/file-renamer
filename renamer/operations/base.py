"""
Base file renamer using Template Method pattern.

Defines the skeleton algorithm for renaming files, with subclasses
implementing filesystem-specific operations.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from ..domain.models import (
    RenameResult,
    FileMetadata,
    SidecarContent,
    OperationStats
)
from ..protocols import (
    HashComputerProtocol,
    SidecarWriterProtocol,
    FileOperationsProtocol
)
from ..core.sanitizer import FilenameSanitizer


class BaseFileRenamer(ABC):
    """
    Abstract base class for file renaming operations.
    
    Implements Template Method pattern:
    - rename_file() defines the algorithm skeleton
    - Subclasses implement _perform_rename(), _get_file_size()
    
    Uses Dependency Injection for all external dependencies.
    
    Responsibilities (SRP compliant):
    - Orchestrate rename workflow
    - Collision handling
    - Statistics tracking
    - Delegate to injected services (hash, sidecar, operations)
    
    Example:
        >>> class LocalFileRenamer(BaseFileRenamer):
        ...     def _perform_rename(self, old_path, new_path):
        ...         # Local implementation
        ...
        >>> renamer = LocalFileRenamer(hasher=..., sidecar=..., ops=...)
        >>> result = renamer.rename_file(Path("file.txt"))
    """
    
    def __init__(
        self,
        hasher: HashComputerProtocol,
        sidecar_writer: SidecarWriterProtocol,
        file_operations: FileOperationsProtocol,
        sanitizer: Optional[FilenameSanitizer] = None,
        verbose: bool = False
    ):
        """
        Initialize base file renamer.
        
        Args:
            hasher: Hash computer (SHA256 or MD5)
            sidecar_writer: Sidecar file writer
            file_operations: File operations interface
            sanitizer: Filename sanitizer (creates default if None)
            verbose: Enable verbose logging
        """
        self._hasher = hasher
        self._sidecar_writer = sidecar_writer
        self._file_ops = file_operations
        self._sanitizer = sanitizer or FilenameSanitizer()
        self._verbose = verbose
        self._logger = logging.getLogger(self.__class__.__name__)
        
        if verbose:
            self._logger.setLevel(logging.DEBUG)
    
    def rename_file(
        self,
        file_path: Path,
        dry_run: bool = False
    ) -> RenameResult:
        """
        Rename a single file to safe name (Template Method).
        
        Algorithm:
        1. Check if system file -> skip
        2. Check if already safe -> skip
        3. Sanitize filename
        4. Handle collision (check sidecar)
        5. Perform rename (delegated to subclass)
        6. Compute hash
        7. Write sidecar
        
        Args:
            file_path: Path to file to rename
            dry_run: If True, simulate without actual rename
        
        Returns:
            RenameResult with operation outcome
        """
        try:
            filename = file_path.name
            
            # Step 1: Skip system files
            if self._sanitizer.is_system_file(filename):
                self._log_verbose(f"Skipping system file: {filename}")
                return RenameResult.skipped(file_path, "System file")
            
            # Step 2: Check if already safe
            if self._sanitizer.is_safe_filename(filename):
                self._log_verbose(f"Already safe: {filename}")
                return RenameResult.skipped(file_path, "Already safe")
            
            # Step 3: Sanitize filename
            safe_name = self._sanitizer.sanitize(filename)
            self._log_verbose(f"Sanitized: {filename} -> {safe_name}")
            
            # Step 4: Handle collision
            parent = file_path.parent
            new_path = parent / safe_name
            
            if self._file_ops.file_exists(new_path):
                # Collision detected - add hash suffix
                base, ext = self._sanitizer.split_filename(safe_name)
                safe_name = self._sanitizer.add_collision_suffix(base, ext, filename)
                new_path = parent / safe_name
                self._log_verbose(f"Collision handled: {safe_name}")
            
            # Dry run - stop here
            if dry_run:
                self._log_verbose(f"[DRY RUN] Would rename: {filename} -> {safe_name}")
                return RenameResult.success(
                    original_path=file_path,
                    new_path=new_path,
                    sidecar_path=Path(str(new_path) + '.meta.json')
                )
            
            # Step 5: Perform actual rename (delegated to subclass)
            self._perform_rename(file_path, new_path)
            self._log_verbose(f"Renamed: {file_path} -> {new_path}")
            
            # Step 6: Compute hash
            file_hash = self._hasher.compute_hash(new_path)
            file_size = self._get_file_size(new_path)
            
            # Step 7: Write sidecar
            metadata = FileMetadata(
                original_name=filename,
                safe_name=safe_name,
                size_bytes=file_size,
                hash_value=file_hash,
                hash_algorithm=self._hasher.algorithm_name,
                timestamp=datetime.now().isoformat()
            )
            
            sidecar_content = SidecarContent.from_metadata(metadata)
            sidecar_path = self._sidecar_writer.write_sidecar(new_path, sidecar_content)
            
            self._log_verbose(f"Sidecar written: {sidecar_path}")
            
            return RenameResult.success(
                original_path=file_path,
                new_path=new_path,
                sidecar_path=sidecar_path
            )
            
        except Exception as e:
            self._logger.error(f"Failed to rename {file_path}: {e}")
            return RenameResult.failure(file_path, str(e))
    
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
            dry_run: If True, simulate without actual rename
        
        Returns:
            List of RenameResult for each file processed
        """
        results = []
        
        try:
            files = self._file_ops.list_files(directory, recursive=recursive)
            
            for file_path in files:
                result = self.rename_file(file_path, dry_run=dry_run)
                results.append(result)
            
        except Exception as e:
            self._logger.error(f"Failed to process directory {directory}: {e}")
        
        return results
    
    def get_stats(self, results: list[RenameResult]) -> OperationStats:
        """
        Calculate statistics from results.
        
        Args:
            results: List of rename results
        
        Returns:
            OperationStats with aggregated metrics
        """
        stats = OperationStats(
            total_files=len(results),
            renamed=sum(1 for r in results if r.success and not r.skipped),
            skipped=sum(1 for r in results if r.skipped),
            errors=sum(1 for r in results if not r.success)
        )
        return stats
    
    def _log_verbose(self, message: str) -> None:
        """Log message if verbose mode enabled."""
        if self._verbose:
            self._logger.debug(message)
    
    # Abstract methods for subclasses to implement
    
    @abstractmethod
    def _perform_rename(self, old_path: Path, new_path: Path) -> None:
        """
        Perform the actual rename operation.
        
        Subclass-specific implementation for local vs remote.
        
        Args:
            old_path: Current file path
            new_path: Target file path
        
        Raises:
            IOError: If rename fails
        """
        pass
    
    @abstractmethod
    def _get_file_size(self, file_path: Path) -> int:
        """
        Get file size in bytes.
        
        Subclass-specific implementation.
        
        Args:
            file_path: Path to file
        
        Returns:
            File size in bytes
        """
        pass
