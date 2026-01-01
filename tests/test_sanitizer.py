"""
Basic tests for file-renamer package.

Run with: pytest tests/ -v
"""

import pytest
from pathlib import Path
from renamer.core.sanitizer import FilenameSanitizer


class TestFilenameSanitizer:
    """Tests for filename sanitization"""
    
    def setup_method(self):
        """Setup for each test"""
        self.sanitizer = FilenameSanitizer()
    
    def test_simple_clean_filename(self):
        """Test already clean filename passes through"""
        assert self.sanitizer.sanitize("valid_file.txt") == "valid_file.txt"
    
    def test_remove_special_characters(self):
        """Test removal of special characters"""
        assert self.sanitizer.sanitize("file@2024#.txt") == "file_2024_.txt"
    
    def test_windows_forbidden_chars(self):
        """Test Windows forbidden characters are replaced"""
        assert self.sanitizer.sanitize('file<>:"|?*.txt') == "file_______.txt"
    
    def test_spaces_to_underscores(self):
        """Test spaces converted to underscores"""
        assert self.sanitizer.sanitize("my file name.txt") == "my_file_name.txt"
    
    def test_multiple_spaces(self):
        """Test multiple spaces become single underscore"""
        assert self.sanitizer.sanitize("file   name.txt") == "file_name.txt"
    
    def test_trim_whitespace(self):
        """Test leading/trailing whitespace removed"""
        assert self.sanitizer.sanitize("  file.txt  ") == "file.txt"
    
    def test_brackets_removed(self):
        """Test brackets are replaced"""
        assert self.sanitizer.sanitize("file[1](2){3}.txt") == "file_1__2__3_.txt"
    
    def test_preserve_extension(self):
        """Test file extension is preserved"""
        assert self.sanitizer.sanitize("My File!.PDF") == "My_File_.PDF"
    
    def test_needs_rename_true(self):
        """Test needs_rename returns True for problematic names"""
        assert self.sanitizer.needs_rename("file@2024.txt") is True
    
    def test_needs_rename_false(self):
        """Test needs_rename returns False for clean names"""
        assert self.sanitizer.needs_rename("clean_file.txt") is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
