"""
Filename sanitization logic.

Extracted from renamer_lib.py to maintain Single Responsibility.
Pure functions with no side effects.
"""

from __future__ import annotations
import re
import hashlib
import unicodedata
from pathlib import Path
from typing import Tuple


# System files to exclude
SYSTEM_FILES = {
    '.DS_Store', 'Thumbs.db', 'desktop.ini', '.localized',
    'thumbs.db', 'Desktop.ini', '$RECYCLE.BIN', 'System Volume Information'
}

# Windows reserved names (case-insensitive)
RESERVED_NAMES = {
    'con', 'prn', 'aux', 'nul',
    'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
    'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
}

# Transliteration map for accented characters
TRANSLITERATION_MAP = str.maketrans({
    'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a', 'æ': 'ae',
    'ç': 'c', 'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
    'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
    'ñ': 'n', 'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o', 'ø': 'o',
    'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
    'ý': 'y', 'ÿ': 'y', 'ß': 'ss',
})


class FilenameSanitizer:
    """
    Sanitize filenames to cross-platform safe format.
    
    Implements RENAMER.md specification:
    - Unicode NFKC normalization
    - Transliteration to ASCII
    - Lowercase conversion
    - Whitelist: a-z, 0-9, -, _, .
    - No consecutive separators
    - 180 character limit
    - Collision handling with --<hash> suffix
    
    Stateless utility class.
    
    Example:
        >>> sanitizer = FilenameSanitizer()
        >>> safe = sanitizer.sanitize("My File (2023).TXT")
        >>> safe
        'my-file-2023.txt'
    """
    
    MAX_FILENAME_LENGTH = 180
    
    @staticmethod
    def is_system_file(filename: str) -> bool:
        """Check if filename is a system file to skip."""
        return filename in SYSTEM_FILES
    
    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """
        Check if filename already meets safe naming requirements.
        
        Args:
            filename: Filename to check
        
        Returns:
            True if filename is already safe
        """
        # Must be lowercase
        if filename != filename.lower():
            return False
        
        # Split into base and extension
        base, ext = FilenameSanitizer.split_filename(filename)
        
        # Extension must be lowercase alphanumeric with dot
        if ext and not re.match(r'^\.[a-z0-9]+(\.[a-z0-9]+)?$', ext):
            return False
        
        # Base must be lowercase alphanumeric with hyphens/underscores
        if not re.match(r'^[a-z0-9][a-z0-9_-]*[a-z0-9]$|^[a-z0-9]$', base):
            return False
        
        # No consecutive separators
        if '--' in base or '__' in base or '-_' in base or '_-' in base:
            return False
        
        # Check length
        if len(filename) > FilenameSanitizer.MAX_FILENAME_LENGTH:
            return False
        
        return True
    
    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Normalize Unicode to NFKC form."""
        return unicodedata.normalize('NFKC', text)
    
    @staticmethod
    def transliterate(text: str) -> str:
        """Convert accented characters to ASCII equivalents."""
        return text.translate(TRANSLITERATION_MAP)
    
    @staticmethod
    def split_filename(filename: str) -> Tuple[str, str]:
        """
        Split filename into base name and extension(s).
        
        Supports 1-2 extensions (e.g., .tar.gz).
        
        Args:
            filename: Filename to split
        
        Returns:
            Tuple of (base_name, extension)
        
        Example:
            >>> FilenameSanitizer.split_filename("file.tar.gz")
            ('file', '.tar.gz')
            >>> FilenameSanitizer.split_filename("file.txt")
            ('file', '.txt')
        """
        parts = filename.rsplit('.', 2)
        
        if len(parts) == 3 and parts[1] in ['tar', 'backup']:
            # Double extension like .tar.gz
            return parts[0], f'.{parts[1]}.{parts[2]}'
        elif len(parts) >= 2:
            # Single extension
            return '.'.join(parts[:-1]), f'.{parts[-1]}'
        else:
            # No extension
            return filename, ''
    
    @staticmethod
    def sanitize_base_name(name: str) -> str:
        """
        Sanitize base name (without extension) according to spec.
        
        Rules:
        - Lowercase
        - Only a-z0-9-_
        - No consecutive separators
        - Must start with [a-z0-9]
        - No leading/trailing separators
        
        Args:
            name: Base name to sanitize
        
        Returns:
            Sanitized base name
        """
        # Normalize and lowercase
        name = FilenameSanitizer.normalize_unicode(name).lower()
        
        # Transliterate
        name = FilenameSanitizer.transliterate(name)
        
        # Replace whitespace and non-allowed chars with separator
        result = []
        prev_sep = False
        
        for char in name:
            if char in 'abcdefghijklmnopqrstuvwxyz0123456789':
                result.append(char)
                prev_sep = False
            elif char in '-_':
                if not prev_sep and result:
                    result.append('-')
                    prev_sep = True
            elif char in ' \t\n\r':
                if not prev_sep and result:
                    result.append('-')
                    prev_sep = True
        
        sanitized = ''.join(result)
        
        # Remove trailing separators
        sanitized = sanitized.rstrip('-_')
        
        # Ensure starts with alphanumeric
        sanitized = re.sub(r'^[^a-z0-9]+', '', sanitized)
        
        # Collapse consecutive separators
        sanitized = re.sub(r'[-_]+', '-', sanitized)
        
        # If empty, use fallback
        if not sanitized:
            sanitized = 'file'
        
        return sanitized
    
    @staticmethod
    def sanitize_extension(ext: str) -> str:
        """
        Sanitize extension (e.g., '.MP4' -> '.mp4').
        
        Args:
            ext: Extension with or without leading dot
        
        Returns:
            Sanitized extension with leading dot
        """
        if not ext:
            return ''
        
        ext = ext.lstrip('.')
        ext = ext.lower()
        ext = ''.join(c for c in ext if c in 'abcdefghijklmnopqrstuvwxyz0123456789')
        
        return f'.{ext}' if ext else ''
    
    @staticmethod
    def check_reserved_name(base_name: str) -> str:
        """
        Check if base name is Windows reserved, prefix if needed.
        
        Args:
            base_name: Base name to check
        
        Returns:
            Original name or 'file_' + name if reserved
        """
        if base_name.lower() in RESERVED_NAMES:
            return f'file_{base_name}'
        return base_name
    
    @staticmethod
    def truncate_if_needed(base_name: str, extension: str) -> str:
        """
        Truncate base name if total length exceeds limit.
        
        Args:
            base_name: Base name
            extension: Extension (with dot)
        
        Returns:
            Truncated base name if needed
        """
        max_base_len = FilenameSanitizer.MAX_FILENAME_LENGTH - len(extension)
        if len(base_name) > max_base_len:
            return base_name[:max_base_len].rstrip('-_')
        return base_name
    
    @staticmethod
    def add_collision_suffix(base_name: str, extension: str, original_name: str) -> str:
        """
        Add unique hash suffix for collision handling.
        
        Format: base-name--<8-char-hash>.ext
        
        Args:
            base_name: Sanitized base name
            extension: Extension
            original_name: Original filename for hash generation
        
        Returns:
            Filename with collision suffix
        """
        # Generate 8-character hash from original name
        hash_obj = hashlib.sha256(original_name.encode('utf-8'))
        hash_suffix = hash_obj.hexdigest()[:8]
        
        # Calculate max base length with suffix
        suffix_part = f'--{hash_suffix}'
        max_base_len = FilenameSanitizer.MAX_FILENAME_LENGTH - len(extension) - len(suffix_part)
        
        # Truncate base if needed
        if len(base_name) > max_base_len:
            base_name = base_name[:max_base_len].rstrip('-_')
        
        return f'{base_name}{suffix_part}{extension}'
    
    def sanitize(self, filename: str) -> str:
        """
        Sanitize a filename to cross-platform safe format.
        
        Main entry point for sanitization.
        
        Args:
            filename: Original filename
        
        Returns:
            Sanitized filename
        
        Example:
            >>> sanitizer = FilenameSanitizer()
            >>> sanitizer.sanitize("My File (2023).TXT")
            'my-file-2023.txt'
        """
        # Split into base and extension
        base, ext = self.split_filename(filename)
        
        # Sanitize each part
        safe_base = self.sanitize_base_name(base)
        safe_ext = self.sanitize_extension(ext)
        
        # Check for reserved names
        safe_base = self.check_reserved_name(safe_base)
        
        # Truncate if needed
        safe_base = self.truncate_if_needed(safe_base, safe_ext)
        
        return f'{safe_base}{safe_ext}'
