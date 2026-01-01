"""
Domain models for file renaming operations.

All models are immutable value objects (frozen dataclasses) following DDD principles.
These represent pure domain concepts with no infrastructure dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class OperationTiming:
    """
    Value object representing timing information for an operation.
    
    Immutable and self-contained.
    
    Attributes:
        start: Operation start timestamp
        end: Operation end timestamp
    
    Example:
        >>> timing = OperationTiming(
        ...     start=datetime(2025, 1, 1, 10, 0, 0),
        ...     end=datetime(2025, 1, 1, 10, 5, 30)
        ... )
        >>> timing.duration_seconds
        330.0
    """
    start: datetime
    end: datetime
    
    @property
    def duration_seconds(self) -> float:
        """Calculate operation duration in seconds."""
        return (self.end - self.start).total_seconds()
    
    @staticmethod
    def start_now() -> OperationTiming:
        """Create timing starting now (end will be same as start initially)."""
        now = datetime.now()
        return OperationTiming(start=now, end=now)
    
    def finish_now(self) -> OperationTiming:
        """Return new timing with end set to current time."""
        return OperationTiming(start=self.start, end=datetime.now())


@dataclass(frozen=True)
class OperationStats:
    """
    Statistics for a batch rename operation.
    
    Immutable value object for tracking operation metrics.
    
    Attributes:
        total_files: Total files encountered
        renamed: Successfully renamed files
        skipped: Files skipped (already safe, excluded, etc.)
        errors: Files that failed to rename
    
    Example:
        >>> stats = OperationStats(total_files=100, renamed=85, skipped=10, errors=5)
        >>> stats.success_rate
        0.85
    """
    total_files: int = 0
    renamed: int = 0
    skipped: int = 0
    errors: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.total_files == 0:
            return 0.0
        return self.renamed / self.total_files
    
    def increment_total(self) -> OperationStats:
        """Return new stats with total_files incremented."""
        return OperationStats(
            total_files=self.total_files + 1,
            renamed=self.renamed,
            skipped=self.skipped,
            errors=self.errors
        )
    
    def increment_renamed(self) -> OperationStats:
        """Return new stats with renamed incremented."""
        return OperationStats(
            total_files=self.total_files,
            renamed=self.renamed + 1,
            skipped=self.skipped,
            errors=self.errors
        )
    
    def increment_skipped(self) -> OperationStats:
        """Return new stats with skipped incremented."""
        return OperationStats(
            total_files=self.total_files,
            renamed=self.renamed,
            skipped=self.skipped + 1,
            errors=self.errors
        )
    
    def increment_errors(self) -> OperationStats:
        """Return new stats with errors incremented."""
        return OperationStats(
            total_files=self.total_files,
            renamed=self.renamed,
            skipped=self.skipped,
            errors=self.errors + 1
        )


@dataclass(frozen=True)
class FileMetadata:
    """
    Metadata about a file for sidecar JSON generation.
    
    Value object containing file information.
    
    Attributes:
        original_name: Original filename before sanitization
        safe_name: Sanitized filename
        size_bytes: File size in bytes
        hash_value: File content hash
        hash_algorithm: Algorithm used for hash ('sha256' or 'md5')
        timestamp: ISO format timestamp of metadata generation
    """
    original_name: str
    safe_name: str
    size_bytes: int
    hash_value: str
    hash_algorithm: str  # 'sha256' or 'md5'
    timestamp: str  # ISO format
    
    def __post_init__(self):
        """Validate hash algorithm."""
        if self.hash_algorithm not in ('sha256', 'md5'):
            raise ValueError(f"Invalid hash algorithm: {self.hash_algorithm}. Must be 'sha256' or 'md5'")


@dataclass(frozen=True)
class SidecarContent:
    """
    Content for .meta.json sidecar file.
    
    Immutable structure following it.infrastructures.filemeta.v1 schema.
    
    Attributes:
        schema: Schema identifier
        original_filename: Original filename
        safe_filename: Sanitized filename
        file_size_bytes: File size
        hash: File content hash
        hash_algorithm: Hash algorithm used
        renamed_at: ISO timestamp
    """
    schema: str = "it.infrastructures.filemeta.v1"
    original_filename: str = ""
    safe_filename: str = ""
    file_size_bytes: int = 0
    hash: str = ""
    hash_algorithm: str = "sha256"
    renamed_at: str = ""
    
    @staticmethod
    def from_metadata(metadata: FileMetadata) -> SidecarContent:
        """Create sidecar content from file metadata."""
        return SidecarContent(
            original_filename=metadata.original_name,
            safe_filename=metadata.safe_name,
            file_size_bytes=metadata.size_bytes,
            hash=metadata.hash_value,
            hash_algorithm=metadata.hash_algorithm,
            renamed_at=metadata.timestamp
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema": self.schema,
            "original_filename": self.original_filename,
            "safe_filename": self.safe_filename,
            "file_size_bytes": self.file_size_bytes,
            "hash": self.hash,
            "hash_algorithm": self.hash_algorithm,
            "renamed_at": self.renamed_at
        }


@dataclass(frozen=True)
class RenameResult:
    """
    Result of a single file rename operation.
    
    Immutable value object representing the outcome.
    
    Attributes:
        original_path: Original file path
        success: Whether operation succeeded
        new_path: New file path (None if failed)
        sidecar_path: Path to .meta.json sidecar (None if failed)
        error: Error message (None if succeeded)
        skipped: Whether file was skipped (already safe)
    
    Example:
        >>> result = RenameResult.success(
        ...     original_path=Path("old.TXT"),
        ...     new_path=Path("old.txt"),
        ...     sidecar_path=Path("old.txt.meta.json")
        ... )
        >>> result.success
        True
    """
    original_path: Path
    success: bool
    new_path: Optional[Path] = None
    sidecar_path: Optional[Path] = None
    error: Optional[str] = None
    skipped: bool = False
    
    @staticmethod
    def success(
        original_path: Path,
        new_path: Path,
        sidecar_path: Path
    ) -> RenameResult:
        """Create successful result."""
        return RenameResult(
            original_path=original_path,
            success=True,
            new_path=new_path,
            sidecar_path=sidecar_path,
            skipped=False
        )
    
    @staticmethod
    def skipped(original_path: Path, reason: str) -> RenameResult:
        """Create skipped result."""
        return RenameResult(
            original_path=original_path,
            success=True,
            new_path=None,
            sidecar_path=None,
            error=reason,
            skipped=True
        )
    
    @staticmethod
    def failure(original_path: Path, error: str) -> RenameResult:
        """Create failed result."""
        return RenameResult(
            original_path=original_path,
            success=False,
            new_path=None,
            sidecar_path=None,
            error=error,
            skipped=False
        )
