#!/usr/bin/env python3
"""
File Renamer CLI - Cross-platform safe file renaming tool.

Rename files to safe format compatible with Windows, macOS, Linux, and cloud storage.

Usage:
    python renamer_cli.py <path> [--dry-run] [--verbose]
    
Examples:
    # Local path
    python renamer_cli.py "C:/folder" --verbose
    
    # UNC path
    python renamer_cli.py "\\\\server\\share\\folder" --dry-run
    
    # Remote path (Google Drive via rclone)
    python renamer_cli.py "gdrive:folder/subfolder" --verbose
"""

from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from renamer.factory import FileRenamerFactory, print_stats
from renamer.domain.models import OperationTiming


def setup_logging(verbose: bool, log_dir: Optional[Path] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
        log_dir: Directory for log files (creates default if None)
    """
    # Create log directory
    if log_dir is None:
        log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'renamer_{timestamp}.log'
    
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Log file: {log_file}")
    logger.info(f"Verbose mode: {verbose}")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Rename files to cross-platform safe format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "C:/my files"                    # Rename local folder
  %(prog)s "\\\\server\\share\\folder"      # Rename UNC path
  %(prog)s "gdrive:backups" --dry-run       # Preview remote renames
  %(prog)s "gdrive:photos" --verbose        # Verbose remote rename
        """
    )
    
    parser.add_argument(
        'path',
        type=str,
        help='Path to directory (local, UNC, or remote like gdrive:folder)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without actually renaming files'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--rclone-path',
        type=Path,
        default=None,
        help='Path to rclone executable (default: use system rclone)'
    )
    
    parser.add_argument(
        '--log-dir',
        type=Path,
        default=None,
        help='Directory for log files (default: ./logs/)'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for file renamer CLI.
    
    Returns:
        Exit code (0 for success, 1 for errors)
    """
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(verbose=args.verbose, log_dir=args.log_dir)
    logger = logging.getLogger(__name__)
    
    try:
        # Resolve path
        target_path = Path(args.path)
        
        # Log operation details
        logger.info(f"Target path: {target_path}")
        logger.info(f"Dry run: {args.dry_run}")
        logger.info(f"Path type: {'Remote' if FileRenamerFactory.is_remote_path(target_path) else 'Local'}")
        
        # Create renamer using factory (auto-detects local vs remote)
        renamer = FileRenamerFactory.create_from_path(
            path=target_path,
            rclone_path=args.rclone_path,
            verbose=args.verbose
        )
        
        logger.info(f"Using renamer: {renamer.__class__.__name__}")
        
        # Start timing
        timing = OperationTiming.start_now()
        
        # Execute rename operation
        print(f"\n{'=' * 60}")
        print(f"Renaming files in: {target_path}")
        print(f"Mode: {'DRY RUN (preview only)' if args.dry_run else 'LIVE (actual rename)'}")
        print(f"{'=' * 60}\n")
        
        results = renamer.rename_directory(
            directory=target_path,
            recursive=True,
            dry_run=args.dry_run
        )
        
        # Finish timing
        timing = timing.finish_now()
        
        # Calculate and display statistics
        stats = renamer.get_stats(results)
        print_stats(stats)
        
        # Log summary
        logger.info(f"Operation completed in {timing.duration_seconds:.2f}s")
        logger.info(f"Stats: {stats.total_files} total, {stats.renamed} renamed, "
                   f"{stats.skipped} skipped, {stats.errors} errors")
        
        # Display errors if any
        errors = [r for r in results if not r.success]
        if errors:
            print("\nErrors encountered:")
            print(f"{'=' * 60}")
            for result in errors:
                print(f"  {result.original_path}")
                print(f"    Error: {result.error}")
            print(f"{'=' * 60}\n")
        
        # Exit code based on success
        if stats.errors > 0:
            logger.warning(f"Completed with {stats.errors} errors")
            return 1
        else:
            logger.info("Completed successfully")
            return 0
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\n\nOperation cancelled by user")
        return 130
    
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        print(f"\nFATAL ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
