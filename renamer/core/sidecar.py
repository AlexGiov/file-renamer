"""
Sidecar (.meta.json) file management.

Single Responsibility: Handle reading/writing sidecar metadata files.
Eliminates duplication between Local and Remote renamer classes.
"""

from __future__ import annotations
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional

from ..domain.models import SidecarContent, FileMetadata
from ..protocols import SidecarWriterProtocol


class LocalSidecarWriter:
    """
    Write sidecar files to local filesystem.
    
    Implements SidecarWriterProtocol for local file operations.
    Thread-safe and stateless.
    
    Example:
        >>> writer = LocalSidecarWriter()
        >>> metadata = FileMetadata(...)
        >>> content = SidecarContent.from_metadata(metadata)
        >>> sidecar_path = writer.write_sidecar(Path("file.txt"), content)
    """
    
    def __init__(self):
        """Initialize local sidecar writer."""
        self._logger = logging.getLogger(__name__)
    
    def write_sidecar(
        self,
        file_path: Path,
        content: SidecarContent
    ) -> Path:
        """
        Write sidecar .meta.json file to local filesystem.
        
        Args:
            file_path: Path to renamed file
            content: Sidecar content to write
        
        Returns:
            Path to created sidecar file
        
        Raises:
            IOError: If write fails
        """
        sidecar_path = Path(str(file_path) + '.meta.json')
        
        try:
            with open(sidecar_path, 'w', encoding='utf-8') as f:
                json.dump(content.to_dict(), f, indent=2, ensure_ascii=False)
            
            self._logger.debug(f"Sidecar written: {sidecar_path}")
            return sidecar_path
            
        except IOError as e:
            self._logger.error(f"Failed to write sidecar {sidecar_path}: {e}")
            raise
    
    def read_sidecar(self, file_path: Path) -> Optional[SidecarContent]:
        """
        Read existing sidecar .meta.json file.
        
        Args:
            file_path: Path to check for sidecar
        
        Returns:
            SidecarContent if valid sidecar exists, None otherwise
        """
        sidecar_path = Path(str(file_path) + '.meta.json')
        
        if not sidecar_path.exists():
            return None
        
        try:
            with open(sidecar_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate schema
            if data.get('schema') != 'it.infrastructures.filemeta.v1':
                self._logger.warning(f"Invalid schema in {sidecar_path}")
                return None
            
            return SidecarContent(
                schema=data['schema'],
                original_filename=data.get('original_filename', ''),
                safe_filename=data.get('safe_filename', ''),
                file_size_bytes=data.get('file_size_bytes', 0),
                hash=data.get('hash', ''),
                hash_algorithm=data.get('hash_algorithm', 'sha256'),
                renamed_at=data.get('renamed_at', '')
            )
            
        except (IOError, json.JSONDecodeError, KeyError) as e:
            self._logger.warning(f"Failed to read sidecar {sidecar_path}: {e}")
            return None


class RcloneSidecarWriter:
    """
    Write sidecar files to remote via rclone.
    
    Implements SidecarWriterProtocol for remote file operations.
    Thread-safe and stateless.
    
    Example:
        >>> writer = RcloneSidecarWriter()
        >>> metadata = FileMetadata(...)
        >>> content = SidecarContent.from_metadata(metadata)
        >>> sidecar_path = writer.write_sidecar(Path("agdrive:file.txt"), content)
    """
    
    def __init__(self, rclone_path: Optional[Path] = None):
        """
        Initialize rclone sidecar writer.
        
        Args:
            rclone_path: Path to rclone executable (uses 'rclone' if None)
        """
        self._rclone = str(rclone_path) if rclone_path else 'rclone'
        self._logger = logging.getLogger(__name__)
    
    def write_sidecar(
        self,
        file_path: Path,
        content: SidecarContent
    ) -> Path:
        """
        Write sidecar .meta.json via rclone rcat.
        
        Args:
            file_path: Remote path to renamed file
            content: Sidecar content to write
        
        Returns:
            Path to created sidecar file
        
        Raises:
            IOError: If rclone write fails
        """
        sidecar_path = Path(str(file_path) + '.meta.json')
        json_content = json.dumps(content.to_dict(), indent=2, ensure_ascii=False)
        
        cmd = [self._rclone, 'rcat', str(sidecar_path)]
        
        try:
            result = subprocess.run(
                cmd,
                input=json_content,
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )
            
            self._logger.debug(f"Sidecar written via rclone: {sidecar_path}")
            return sidecar_path
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            self._logger.error(f"rclone rcat failed for {sidecar_path}: {error_msg}")
            raise IOError(f"Failed to write sidecar: {error_msg}") from e
    
    def read_sidecar(self, file_path: Path) -> Optional[SidecarContent]:
        """
        Read existing sidecar via rclone cat.
        
        Args:
            file_path: Remote path to check for sidecar
        
        Returns:
            SidecarContent if valid sidecar exists, None otherwise
        """
        sidecar_path = Path(str(file_path) + '.meta.json')
        cmd = [self._rclone, 'cat', str(sidecar_path)]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )
            
            data = json.loads(result.stdout)
            
            # Validate schema
            if data.get('schema') != 'it.infrastructures.filemeta.v1':
                self._logger.warning(f"Invalid schema in {sidecar_path}")
                return None
            
            return SidecarContent(
                schema=data['schema'],
                original_filename=data.get('original_filename', ''),
                safe_filename=data.get('safe_filename', ''),
                file_size_bytes=data.get('file_size_bytes', 0),
                hash=data.get('hash', ''),
                hash_algorithm=data.get('hash_algorithm', 'md5'),
                renamed_at=data.get('renamed_at', '')
            )
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            # File doesn't exist or invalid JSON
            return None


class SidecarManager:
    """
    High-level sidecar management with business logic.
    
    Delegates to appropriate writer based on path type.
    Handles collision detection via existing sidecars.
    
    Example:
        >>> manager = SidecarManager(
        ...     local_writer=LocalSidecarWriter(),
        ...     remote_writer=RcloneSidecarWriter()
        ... )
        >>> # Auto-detects writer based on path
        >>> sidecar = manager.write(Path("file.txt"), content, is_remote=False)
    """
    
    def __init__(
        self,
        local_writer: SidecarWriterProtocol,
        remote_writer: SidecarWriterProtocol
    ):
        """
        Initialize sidecar manager with injected writers.
        
        Args:
            local_writer: Writer for local filesystem
            remote_writer: Writer for remote via rclone
        """
        self._local_writer = local_writer
        self._remote_writer = remote_writer
        self._logger = logging.getLogger(__name__)
    
    def write(
        self,
        file_path: Path,
        content: SidecarContent,
        is_remote: bool
    ) -> Path:
        """
        Write sidecar using appropriate writer.
        
        Args:
            file_path: File path (local or remote)
            content: Sidecar content
            is_remote: True for remote paths
        
        Returns:
            Path to created sidecar
        """
        writer = self._remote_writer if is_remote else self._local_writer
        return writer.write_sidecar(file_path, content)
    
    def read(
        self,
        file_path: Path,
        is_remote: bool
    ) -> Optional[SidecarContent]:
        """
        Read existing sidecar if present.
        
        Args:
            file_path: File path to check
            is_remote: True for remote paths
        
        Returns:
            SidecarContent if exists, None otherwise
        """
        writer = self._remote_writer if is_remote else self._local_writer
        return writer.read_sidecar(file_path)
    
    def check_already_renamed(
        self,
        file_path: Path,
        is_remote: bool
    ) -> bool:
        """
        Check if file was already renamed (has valid sidecar).
        
        Args:
            file_path: File path to check
            is_remote: True for remote paths
        
        Returns:
            True if file has valid sidecar indicating prior rename
        """
        sidecar = self.read(file_path, is_remote)
        return sidecar is not None
