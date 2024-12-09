"""Storage metrics collection for monitoring."""

import os
from pathlib import Path
from typing import Dict, Optional

from prometheus_client import Gauge

from ..config.settings import get_settings

# Storage metrics
STORAGE_USAGE_BYTES = Gauge(
    "storage_usage_bytes",
    "Storage usage in bytes",
    ["type"]
)

STORAGE_TOTAL_BYTES = Gauge(
    "storage_total_bytes",
    "Total storage capacity in bytes"
)

STORAGE_MODEL_COUNT = Gauge(
    "storage_model_count",
    "Number of models in storage",
    ["type"]
)

class StorageMetricsCollector:
    """Collect and update storage metrics."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize storage metrics collector."""
        self.settings = get_settings()
        self.base_path = Path(base_path) if base_path else self.settings.storage.base_path

    def get_directory_size(self, directory: Path) -> int:
        """Get total size of a directory in bytes."""
        total = 0
        for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                filepath = Path(dirpath) / filename
                total += filepath.stat().st_size
        return total

    def get_model_count(self, directory: Path) -> int:
        """Get number of models in a directory."""
        return sum(1 for _ in directory.glob("*") if _.is_dir())

    def collect_metrics(self):
        """Collect and update all storage metrics."""
        # Get storage metrics for each type
        storage_types = {
            "raw": self.settings.storage.raw_dir,
            "quantized": self.settings.storage.quantized_dir,
            "repository": self.settings.storage.repository_dir,
        }

        total_size = 0
        for storage_type, directory in storage_types.items():
            full_path = self.base_path / directory
            if full_path.exists():
                # Update storage usage
                size = self.get_directory_size(full_path)
                STORAGE_USAGE_BYTES.labels(type=storage_type).set(size)
                total_size += size

                # Update model count
                count = self.get_model_count(full_path)
                STORAGE_MODEL_COUNT.labels(type=storage_type).set(count)

        # Update total storage capacity
        total_capacity = os.statvfs(self.base_path).f_blocks * os.statvfs(self.base_path).f_frsize
        STORAGE_TOTAL_BYTES.set(total_capacity)

    def get_storage_info(self) -> Dict:
        """Get storage information as a dictionary."""
        info = {}
        for storage_type in ["raw", "quantized", "repository"]:
            info[storage_type] = {
                "usage_bytes": STORAGE_USAGE_BYTES.labels(type=storage_type)._value.get(),
                "model_count": STORAGE_MODEL_COUNT.labels(type=storage_type)._value.get(),
            }
        info["total_bytes"] = STORAGE_TOTAL_BYTES._value.get()
        return info

def setup_storage_metrics(base_path: Optional[Path] = None) -> StorageMetricsCollector:
    """Set up storage metrics collection."""
    collector = StorageMetricsCollector(base_path)
    collector.collect_metrics()
    return collector 