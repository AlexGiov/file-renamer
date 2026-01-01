"""
Remote file operations via rclone.

Handles file renaming on remote filesystems (Google Drive, etc.) using rclone.
Implements copy+verify+delete strategy for reliability.
"""

from __future__ import annotations
from pathlib import Path
import subprocess
from typing import Optional
import logging

from ..protocols import FileOperationsProtocol
from .base import BaseFileRenamer


class RemoteFileOperations:
    """
    File operations for remote filesystem via rclone.
    
    Implements FileOperationsProtocol using rclone commands.
    Thread-safe and stateless.
    
    Example:
        >>> ops = RemoteFileOperations()
        >>> ops.rename_file(Path("agdrive:old.txt"), Path("agdrive:new.txt"))
    """
    
    def __init__(self, rclone_path: Optional[Path] = None):
        """
        Initialize remote file operations.
        
        Args:
            rclone_path: Path to rclone executable (uses 'rclone' if None)
        """
        self._rclone = str(rclone_path) if rclone_path else 'rclone'
        self._logger = logging.getLogger(__name__)
    
    def _run_rclone(
        self,
        args: list[str],
        input_data: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """
        Run rclone command with UTF-8 encoding.
        
        Args:
            args: rclone command arguments
            input_data: Optional stdin input
        
        Returns:
            Completed process
        
        Raises:
            subprocess.CalledProcessError: If command fails
        """
        cmd = [self._rclone] + args
        
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )
        
        return result
    
    def rename_file(self, old_path: Path, new_path: Path) -> None:
        """
        Rename file on remote via rclone using copy+verify+delete.
        
        Strategy (more reliable than moveto):
        1. copyto old_path new_path
        2. Verify new_path exists
        3. deletefile old_path
        
        Args:
            old_path: Current remote path
            new_path: Target remote path
        
        Raises:
            IOError: If rename fails
        """
        try:
            # Step 1: Copy to new location
            self._run_rclone(['copyto', str(old_path), str(new_path)])
            
            # Step 2: Verify new file exists
            if not self.file_exists(new_path):
                raise IOError(f"Copy verification failed: {new_path} not found")
            
            # Step 3: Delete old file
            self._run_rclone(['deletefile', str(old_path)])
            
            self._logger.debug(f"Renamed (copy+delete): {old_path} -> {new_path}")
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            self._logger.error(f"rclone rename failed for {old_path}: {error_msg}")
            raise IOError(f"Remote rename failed: {error_msg}") from e
    
    def file_exists(self, file_path: Path) -> bool:
        """
        Check if file exists on remote.
        
        Uses rclone lsf with --files-only.
        
        Args:
            file_path: Remote path to check
        
        Returns:
            True if file exists
        """
        try:
            result = self._run_rclone(['lsf', '--files-only', str(file_path)])
            # If file exists, lsf returns the filename
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False
    
    def get_file_size(self, file_path: Path) -> int:
        """
        Get file size in bytes via rclone size.
        
        Args:
            file_path: Remote file path
        
        Returns:
            File size in bytes
        
        Raises:
            IOError: If file doesn't exist or size can't be determined
        """
        try:
            result = self._run_rclone(['size', '--json', str(file_path)])
            
            import json
            data = json.loads(result.stdout)
            size = data.get('bytes', 0)
            
            return size
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            raise IOError(f"Failed to get file size: {e}") from e
    
    def list_files(self, directory: Path, recursive: bool = False) -> list[Path]:
        """
        List files in remote directory.
        
        Uses rclone lsf with --files-only.
        
        Args:
            directory: Remote directory path
            recursive: Whether to recurse into subdirectories
        
        Returns:
            List of remote file paths
        """
        files = []
        
        try:
            args = ['lsf', '--files-only']
            if recursive:
                args.append('--recursive')
            args.append(str(directory))
            
            result = self._run_rclone(args)
            
            # Parse output - one file per line
            for line in result.stdout.strip().split('\n'):
                if line:
                    file_path = Path(str(directory)) / line
                    files.append(file_path)
                    
        except subprocess.CalledProcessError as e:
            self._logger.error(f"Failed to list directory {directory}: {e}")
        
        return files


class RemoteFileRenamer(BaseFileRenamer):
    """
    File renamer for remote filesystem via rclone.
    
    Extends BaseFileRenamer with rclone-specific implementations.
    Uses MD5 for hashing (what rclone returns for most remotes).
    
    Example:
        >>> from ..factory import FileRenamerFactory
        >>> renamer = FileRenamerFactory.create_remote_renamer(verbose=True)
        >>> result = renamer.rename_file(Path("agdrive:folder/My File.TXT"))
        >>> if result.success:
        ...     print(f"Renamed to {result.new_path}")
    """
    
    def __init__(self, *args, rclone_path: Optional[Path] = None, **kwargs):
        """
        Initialize remote file renamer.
        
        Args:
            rclone_path: Path to rclone executable
            *args, **kwargs: Passed to BaseFileRenamer
        """
        super().__init__(*args, **kwargs)
        self._rclone_path = rclone_path
        self._rclone = str(rclone_path) if rclone_path else 'rclone'
    
    def _run_rclone(
        self,
        args: list[str],
        input_data: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """Run rclone command with UTF-8 encoding."""
        cmd = [self._rclone] + args
        
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )
        
        return result
    
    def _perform_rename(self, old_path: Path, new_path: Path) -> None:
        """
        Perform rename on remote via rclone.
        
        Uses copy+verify+delete strategy for reliability.
        
        Args:
            old_path: Current remote path
            new_path: Target remote path
        
        Raises:
            IOError: If rename fails
        """
        try:
            # Step 1: Copy to new location
            self._run_rclone(['copyto', str(old_path), str(new_path)])
            
            # Step 2: Verify new file exists
            result = self._run_rclone(['lsf', '--files-only', str(new_path)])
            if not result.stdout.strip():
                raise IOError(f"Copy verification failed: {new_path} not found")
            
            # Step 3: Delete old file
            self._run_rclone(['deletefile', str(old_path)])
            
            self._logger.debug(f"Renamed via rclone: {old_path} -> {new_path}")
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            self._logger.error(f"rclone rename failed for {old_path}: {error_msg}")
            raise IOError(f"Remote rename failed: {error_msg}") from e
    
    def _get_file_size(self, file_path: Path) -> int:
        """
        Get file size from remote via rclone size.
        
        Args:
            file_path: Remote file path
        
        Returns:
            File size in bytes
        
        Raises:
            IOError: If size can't be determined
        """
        try:
            result = self._run_rclone(['size', '--json', str(file_path)])
            
            import json
            data = json.loads(result.stdout)
            size = data.get('bytes', 0)
            
            return size
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            raise IOError(f"Failed to get file size: {e}") from e
