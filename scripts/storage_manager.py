#!/usr/bin/env python3
"""Storage management utilities for SRT Model Quantizing."""

import argparse
import logging
import shutil
from pathlib import Path
from typing import Optional

from srt_model_quantizing.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("storage_manager")

class StorageManager:
    """Manage storage directories and files."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize storage manager."""
        self.settings = get_settings()
        self.base_path = Path(base_path) if base_path else self.settings.storage.base_path
        self.setup_directories()

    def setup_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.base_path / self.settings.storage.raw_dir,
            self.base_path / self.settings.storage.quantized_dir,
            self.base_path / self.settings.storage.repository_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")

    def cleanup_directory(self, directory: Path, pattern: str = "*"):
        """Clean up files in a directory matching a pattern."""
        count = 0
        for item in directory.glob(pattern):
            if item.is_file():
                item.unlink()
                count += 1
            elif item.is_dir():
                shutil.rmtree(item)
                count += 1
        logger.info(f"Cleaned up {count} items in {directory}")

    def get_storage_info(self) -> dict:
        """Get storage usage information."""
        info = {}
        for name, path in [
            ("raw", self.settings.storage.raw_dir),
            ("quantized", self.settings.storage.quantized_dir),
            ("repository", self.settings.storage.repository_dir),
        ]:
            full_path = self.base_path / path
            size = sum(f.stat().st_size for f in full_path.rglob("*") if f.is_file())
            count = sum(1 for _ in full_path.rglob("*") if _.is_file())
            info[name] = {
                "size_bytes": size,
                "file_count": count,
                "path": str(full_path),
            }
        return info

    def move_model(self, model_id: str, source: str, target: str):
        """Move a model between directories."""
        source_dir = self.base_path / getattr(self.settings.storage, f"{source}_dir")
        target_dir = self.base_path / getattr(self.settings.storage, f"{target}_dir")
        
        source_path = source_dir / model_id
        target_path = target_dir / model_id

        if not source_path.exists():
            raise FileNotFoundError(f"Model not found: {source_path}")

        shutil.move(str(source_path), str(target_path))
        logger.info(f"Moved model from {source_path} to {target_path}")

    def backup_storage(self, backup_dir: Path):
        """Create a backup of all storage directories."""
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"storage_backup_{timestamp}"

        shutil.copytree(self.base_path, backup_path)
        logger.info(f"Created backup at: {backup_path}")
        return backup_path

def main():
    """Command-line interface for storage management."""
    parser = argparse.ArgumentParser(description="Storage management utilities")
    parser.add_argument("--base-path", type=Path, help="Base storage path")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Info command
    subparsers.add_parser("info", help="Show storage information")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up directories")
    cleanup_parser.add_argument(
        "--directory",
        choices=["raw", "quantized", "repository"],
        help="Directory to clean"
    )
    cleanup_parser.add_argument(
        "--pattern",
        default="*",
        help="File pattern to match for cleanup"
    )

    # Move command
    move_parser = subparsers.add_parser("move", help="Move a model")
    move_parser.add_argument("model_id", help="Model ID to move")
    move_parser.add_argument(
        "--source",
        choices=["raw", "quantized", "repository"],
        required=True,
        help="Source directory"
    )
    move_parser.add_argument(
        "--target",
        choices=["raw", "quantized", "repository"],
        required=True,
        help="Target directory"
    )

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a backup")
    backup_parser.add_argument(
        "--backup-dir",
        type=Path,
        required=True,
        help="Backup directory"
    )

    args = parser.parse_args()
    manager = StorageManager(args.base_path)

    if args.command == "info":
        info = manager.get_storage_info()
        for name, data in info.items():
            print(f"\n{name.upper()} Storage:")
            print(f"  Path: {data['path']}")
            print(f"  Files: {data['file_count']}")
            print(f"  Size: {data['size_bytes'] / 1024 / 1024:.2f} MB")

    elif args.command == "cleanup":
        if args.directory:
            directory = manager.base_path / getattr(
                manager.settings.storage,
                f"{args.directory}_dir"
            )
            manager.cleanup_directory(directory, args.pattern)
        else:
            for directory in [
                manager.settings.storage.raw_dir,
                manager.settings.storage.quantized_dir,
                manager.settings.storage.repository_dir,
            ]:
                manager.cleanup_directory(
                    manager.base_path / directory,
                    args.pattern
                )

    elif args.command == "move":
        manager.move_model(args.model_id, args.source, args.target)

    elif args.command == "backup":
        backup_path = manager.backup_storage(args.backup_dir)
        print(f"Backup created at: {backup_path}")

if __name__ == "__main__":
    main() 