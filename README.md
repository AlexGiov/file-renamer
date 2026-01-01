# File Renamer

**Cross-platform safe file renaming tool with local and remote support**

Rename files to cross-platform safe format, removing special characters, normalizing Unicode, and ensuring compatibility across Windows, macOS, Linux, and cloud storage services.

## ✨ Features

- **Cross-Platform Safe**: Removes/replaces problematic characters for Windows, macOS, Linux
- **Cloud-Ready**: Safe naming for Google Drive, OneDrive, Dropbox, etc.
- **Local & Remote**: Direct filesystem operations or remote via rclone
- **Collision Detection**: MD5 hash-based duplicate detection
- **Sidecar JSON**: Tracks original → renamed mappings for audit trail
- **Dry-Run Mode**: Preview changes before applying
- **Recursive**: Process entire directory trees
- **Type-Safe**: Full type hints with Python protocols
- **Clean Architecture**: SOLID principles, dependency injection

## 📋 Requirements

- **Python**: 3.11+
- **rclone**: Required only for remote operations ([download](https://rclone.org/downloads/))

## 🚀 Installation

```bash
# Clone repository
git clone https://github.com/yourusername/file-renamer.git
cd file-renamer

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## 🎯 Quick Start

### Local Filesystem

```bash
# Preview changes (dry-run)
python renamer_cli.py "/path/to/folder" --dry-run

# Apply renames
python renamer_cli.py "/path/to/folder"

# Verbose output
python renamer_cli.py "/path/to/folder" --verbose
```

### Remote Storage (via rclone)

```bash
# Google Drive
python renamer_cli.py "gdrive:Photos/2024" --verbose

# OneDrive
python renamer_cli.py "onedrive:Documents" --dry-run

# Custom rclone path
python renamer_cli.py "remote:path" --rclone-path "/usr/local/bin/rclone"
```

### UNC Paths (Windows)

```bash
python renamer_cli.py "\\\\server\\share\\folder"
```

## 📖 Usage Examples

### Example 1: Clean Downloads Folder

```bash
# Preview changes
python renamer_cli.py "C:/Users/Me/Downloads" --dry-run

# Apply changes
python renamer_cli.py "C:/Users/Me/Downloads"
```

**Before:**
```
My Document (final) v2.docx
photo#2024@beach!.jpg
report [DRAFT].pdf
```

**After:**
```
My_Document_final_v2.docx
photo_2024_beach.jpg
report_DRAFT.pdf
```

### Example 2: Sync to Cloud Storage

```bash
# Rename before uploading to Google Drive
python renamer_cli.py "D:/ToUpload" --verbose
```

### Example 3: Remote Google Drive Cleanup

```bash
# Rename files directly on Google Drive
python renamer_cli.py "gdrive:Archive/OldFiles" --dry-run
python renamer_cli.py "gdrive:Archive/OldFiles"
```

## 🔧 Advanced Usage

### Python API

```python
from pathlib import Path
from renamer.factory import FileRenamerFactory

# Auto-detect local vs remote
path = Path("C:/my folder")
renamer = FileRenamerFactory.create_from_path(path)

# Rename directory
results = renamer.rename_directory(
    directory=path,
    recursive=True,
    dry_run=False
)

# Check results
for result in results:
    if result.success and result.renamed:
        print(f"{result.original_name} → {result.new_name}")
    elif not result.success:
        print(f"Error: {result.error}")
```

### Custom Sanitization

```python
from renamer.core.sanitizer import FilenameSanitizer

sanitizer = FilenameSanitizer()

# Sanitize individual filename
clean_name = sanitizer.sanitize("My File [2024].txt")
# Output: "My_File_2024.txt"

# Check if needs renaming
needs_rename = sanitizer.needs_rename("valid_file.txt")  # False
needs_rename = sanitizer.needs_rename("file@2024.txt")    # True
```

## 🛡️ Safety Features

1. **Collision Detection**: Detects when renamed file would overwrite existing file
2. **MD5 Verification**: Compares file hashes to prevent accidental overwrites
3. **Sidecar JSON**: Creates `.renamer_sidecar.json` with original → renamed mappings
4. **Dry-Run Mode**: Preview all changes before applying
5. **Detailed Logging**: Comprehensive logs with timestamps

## 📁 Sidecar JSON Format

When renaming, a sidecar file is created in each directory:

```json
{
  "timestamp": "2026-01-01T12:34:56.789",
  "mappings": [
    {
      "original": "My File (1).txt",
      "renamed": "My_File_1.txt",
      "md5_hash": "d41d8cd98f00b204e9800998ecf8427e"
    }
  ]
}
```

## 🔍 Character Replacements

| Original | Replacement | Reason |
|----------|-------------|--------|
| `<>:"\|?*` | `_` | Windows forbidden |
| `/` | `_` | Path separator |
| `#` | `_` | URL issues |
| `@` | `_` | Email confusion |
| `!` | `_` | Shell special |
| `,;` | `_` | Parsing issues |
| `[](){}` | `_` | Bracket normalization |
| `'` | (removed) | Quote normalization |
| Multiple spaces | Single `_` | Whitespace normalization |
| Leading/trailing spaces | (removed) | Trim whitespace |

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=renamer --cov-report=html

# Specific test
pytest tests/test_sanitizer.py -v
```

## 📊 Statistics Output

```
════════════════════════════════════════════════════════
Renaming Summary
════════════════════════════════════════════════════════
Total files:      150
Renamed:          23
Skipped:          125
  Already safe:   120
  Collisions:     2
  Errors:         3
Errors:           3
Success rate:     98.0%
════════════════════════════════════════════════════════
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built with Clean Architecture principles
- Follows [The Zen of Python](https://www.python.org/dev/peps/pep-0020/)
- Inspired by cross-platform filesystem challenges

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/file-renamer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/file-renamer/discussions)

---

**Made with ❤️ for cross-platform file management**
