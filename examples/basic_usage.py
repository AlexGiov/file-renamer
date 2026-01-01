"""
Example: Basic Local Renaming

Simple example showing how to rename files in a local directory.
"""

from pathlib import Path
from renamer.factory import FileRenamerFactory, print_stats

def main():
    # Target directory
    folder = Path("C:/Users/Me/Downloads")
    
    print(f"Renaming files in: {folder}\n")
    
    # Create local renamer
    renamer = FileRenamerFactory.create_from_path(folder)
    
    # Dry-run first to preview changes
    print("=== DRY RUN ===")
    dry_results = renamer.rename_directory(
        directory=folder,
        recursive=True,
        dry_run=True
    )
    
    # Show what would be renamed
    renamed = [r for r in dry_results if r.renamed]
    if renamed:
        print("\nFiles that would be renamed:")
        for result in renamed:
            print(f"  {result.original_name}")
            print(f"  → {result.new_name}\n")
    
    # Ask for confirmation
    response = input("\nProceed with renaming? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return
    
    # Actual rename
    print("\n=== RENAMING ===")
    results = renamer.rename_directory(
        directory=folder,
        recursive=True,
        dry_run=False
    )
    
    # Show statistics
    stats = renamer.get_stats(results)
    print_stats(stats)

if __name__ == '__main__':
    main()
