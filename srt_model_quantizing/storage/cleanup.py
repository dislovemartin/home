"""Storage cleanup policy management."""

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ..config.settings import get_settings
from ..monitoring.storage_metrics import StorageMetricsCollector

logger = logging.getLogger(__name__)

class CleanupPolicy:
    """Base class for cleanup policies."""

    def __init__(self, name: str, description: str):
        """Initialize cleanup policy."""
        self.name = name
        self.description = description
        self.settings = get_settings()
        self.metrics = StorageMetricsCollector()

    def should_cleanup(self, path: Path, info: Dict) -> bool:
        """Check if cleanup should be performed."""
        raise NotImplementedError

    def cleanup(self, path: Path) -> bool:
        """Perform cleanup operation."""
        raise NotImplementedError

class AgeBasedCleanup(CleanupPolicy):
    """Cleanup based on model age."""

    def __init__(self, max_age_days: int):
        """Initialize age-based cleanup."""
        super().__init__(
            name="age_based",
            description=f"Remove models older than {max_age_days} days"
        )
        self.max_age_days = max_age_days

    def should_cleanup(self, path: Path, info: Dict) -> bool:
        """Check if model is older than max age."""
        if not path.exists():
            return False
        
        age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
        return age > timedelta(days=self.max_age_days)

    def cleanup(self, path: Path) -> bool:
        """Remove old model."""
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            logger.info(f"Removed old model: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove old model {path}: {e}")
            return False

class UsageBasedCleanup(CleanupPolicy):
    """Cleanup based on model usage."""

    def __init__(self, min_requests: int, timeframe_days: int):
        """Initialize usage-based cleanup."""
        super().__init__(
            name="usage_based",
            description=f"Remove models with less than {min_requests} requests in {timeframe_days} days"
        )
        self.min_requests = min_requests
        self.timeframe_days = timeframe_days

    def should_cleanup(self, path: Path, info: Dict) -> bool:
        """Check if model usage is below threshold."""
        model_id = path.name
        requests = info.get("requests", 0)
        return requests < self.min_requests

    def cleanup(self, path: Path) -> bool:
        """Remove unused model."""
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            logger.info(f"Removed unused model: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove unused model {path}: {e}")
            return False

class SizeBasedCleanup(CleanupPolicy):
    """Cleanup based on storage size."""

    def __init__(self, max_size_mb: int):
        """Initialize size-based cleanup."""
        super().__init__(
            name="size_based",
            description=f"Remove models when total size exceeds {max_size_mb}MB"
        )
        self.max_size_mb = max_size_mb

    def should_cleanup(self, path: Path, info: Dict) -> bool:
        """Check if storage size exceeds threshold."""
        total_size_mb = sum(
            info.get(t, {}).get("usage_bytes", 0) 
            for t in ["raw", "quantized", "repository"]
        ) / (1024 * 1024)
        return total_size_mb > self.max_size_mb

    def cleanup(self, path: Path) -> bool:
        """Remove largest models until under threshold."""
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            logger.info(f"Removed large model: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove large model {path}: {e}")
            return False

class StorageCleanupManager:
    """Manage storage cleanup policies."""

    def __init__(self):
        """Initialize cleanup manager."""
        self.settings = get_settings()
        self.metrics = StorageMetricsCollector()
        self.policies: List[CleanupPolicy] = []

    def add_policy(self, policy: CleanupPolicy):
        """Add a cleanup policy."""
        self.policies.append(policy)
        logger.info(f"Added cleanup policy: {policy.name}")

    def get_model_info(self, model_path: Path) -> Dict:
        """Get model information for cleanup decisions."""
        return {
            "size_bytes": sum(f.stat().st_size for f in model_path.rglob("*") if f.is_file()),
            "last_modified": datetime.fromtimestamp(model_path.stat().st_mtime),
            "requests": 0,  # TODO: Get from metrics
        }

    def run_cleanup(self, dry_run: bool = False) -> Dict:
        """Run all cleanup policies."""
        results = {
            "cleaned_models": [],
            "failed_models": [],
            "skipped_models": [],
            "total_space_freed": 0
        }

        storage_info = self.metrics.get_storage_info()

        for storage_type in ["raw", "quantized", "repository"]:
            storage_path = self.settings.storage.base_path / getattr(
                self.settings.storage,
                f"{storage_type}_dir"
            )

            if not storage_path.exists():
                continue

            for model_path in storage_path.iterdir():
                if not model_path.is_dir():
                    continue

                model_info = self.get_model_info(model_path)
                should_cleanup = any(
                    policy.should_cleanup(model_path, storage_info)
                    for policy in self.policies
                )

                if should_cleanup:
                    if dry_run:
                        results["skipped_models"].append(str(model_path))
                        continue

                    success = any(
                        policy.cleanup(model_path)
                        for policy in self.policies
                        if policy.should_cleanup(model_path, storage_info)
                    )

                    if success:
                        results["cleaned_models"].append(str(model_path))
                        results["total_space_freed"] += model_info["size_bytes"]
                    else:
                        results["failed_models"].append(str(model_path))

        # Update metrics after cleanup
        if not dry_run:
            self.metrics.collect_metrics()

        return results

def setup_cleanup_manager() -> StorageCleanupManager:
    """Set up storage cleanup manager with default policies."""
    manager = StorageCleanupManager()

    # Add default policies
    manager.add_policy(AgeBasedCleanup(max_age_days=30))
    manager.add_policy(UsageBasedCleanup(min_requests=10, timeframe_days=7))
    manager.add_policy(SizeBasedCleanup(max_size_mb=10000))  # 10GB

    return manager 