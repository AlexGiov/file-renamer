"""
Example: Remote Renaming (Google Drive)

Shows how to rename files on Google Drive using rclone integration.

Prerequisites:
- rclone configured with a remote called 'gdrive'
- Run: rclone config
"""

from pathlib import Path
from renamer.factory import FileRenamerFactory, print_stats

def main():
    # Remote path (format: remote:path)
    remote_path = Path("gdrive:Photos/2024")
    
    print(f"Renaming files on remote: {remote_path}\n")
    
    # Create remote renamer (auto-detected from path)
    renamer = FileRenamerFactory.create_from_path(
        path=remote_path,
        rclone_path=None,  # Uses 'rclone' from PATH
        verbose=True
    )
    
    # Dry-run to preview
    print("=== DRY RUN ===")
    dry_results = renamer.rename_directory(
        directory=remote_path,
        recursive=True,
        dry_run=True
    )
    
    # Show what would be renamed
    renamed = [r for r in dry_results if r.renamed]
    if renamed:
        print(f"\n{len(renamed)} files would be renamed")
        
        # Show first 10
        for result in renamed[:10]:
            print(f"  {result.original_name} → {result.new_name}")
        
        if len(renamed) > 10:
            print(f"  ... and {len(renamed) - 10} more")
    
    # Ask for confirmation
    response = input("\nProceed with remote renaming? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return
    
    # Actual rename
    print("\n=== RENAMING ON REMOTE ===")
    results = renamer.rename_directory(
        directory=remote_path,
        recursive=True,
        dry_run=False
    )
    
    # Show statistics
    stats = renamer.get_stats(results)
    print_stats(stats)

if __name__ == '__main__':
    main()
