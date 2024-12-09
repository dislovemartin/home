"""Model versioning and rollback functionality."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import mlflow
from pydantic import BaseModel

from ..monitoring.logging import get_logger

logger = get_logger(__name__)

class ModelVersion(BaseModel):
    """Model version information."""
    version: int
    model_name: str
    created_at: datetime
    metrics: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, str]] = None
    is_active: bool = False

class ModelVersionManager:
    """Manages model versions and rollbacks."""
    
    def __init__(self, base_path: Union[str, Path]):
        """Initialize version manager.
        
        Args:
            base_path: Base path for model storage
        """
        self.base_path = Path(base_path)
        self.versions_file = self.base_path / "versions.json"
        self._initialize_storage()

    def _initialize_storage(self):
        """Initialize storage directory and version tracking."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        if not self.versions_file.exists():
            self._save_versions([])

    def _load_versions(self) -> List[ModelVersion]:
        """Load version information from storage."""
        if not self.versions_file.exists():
            return []
        with open(self.versions_file, "r") as f:
            versions_data = json.load(f)
            return [ModelVersion(**v) for v in versions_data]

    def _save_versions(self, versions: List[ModelVersion]):
        """Save version information to storage."""
        with open(self.versions_file, "w") as f:
            json.dump([v.dict() for v in versions], f, default=str)

    def get_latest_version(self, model_name: str) -> Optional[ModelVersion]:
        """Get the latest version of a model.
        
        Args:
            model_name: Name of the model
        
        Returns:
            Latest version information or None if no versions exist
        """
        versions = self._load_versions()
        model_versions = [v for v in versions if v.model_name == model_name]
        return max(model_versions, key=lambda x: x.version) if model_versions else None

    def get_active_version(self, model_name: str) -> Optional[ModelVersion]:
        """Get the currently active version of a model.
        
        Args:
            model_name: Name of the model
        
        Returns:
            Active version information or None if no active version exists
        """
        versions = self._load_versions()
        active_versions = [v for v in versions if v.model_name == model_name and v.is_active]
        return active_versions[0] if active_versions else None

    def add_version(
        self,
        model_name: str,
        model_path: Union[str, Path],
        metrics: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> ModelVersion:
        """Add a new model version.
        
        Args:
            model_name: Name of the model
            model_path: Path to the model files
            metrics: Model performance metrics
            metadata: Additional metadata
        
        Returns:
            Created version information
        """
        versions = self._load_versions()
        current_versions = [v.version for v in versions if v.model_name == model_name]
        new_version = max(current_versions, default=0) + 1

        # Create version directory
        version_dir = self.base_path / model_name / str(new_version)
        version_dir.mkdir(parents=True, exist_ok=True)

        # Copy model files
        shutil.copytree(model_path, version_dir, dirs_exist_ok=True)

        # Log to MLflow
        with mlflow.start_run():
            mlflow.log_params(metadata or {})
            mlflow.log_metrics(metrics or {})
            mlflow.log_artifacts(str(model_path))

        # Create version info
        version_info = ModelVersion(
            version=new_version,
            model_name=model_name,
            created_at=datetime.utcnow(),
            metrics=metrics,
            metadata=metadata,
            is_active=False
        )

        versions.append(version_info)
        self._save_versions(versions)
        logger.info(f"Added version {new_version} for model {model_name}")

        return version_info

    def activate_version(self, model_name: str, version: int) -> ModelVersion:
        """Activate a specific model version.
        
        Args:
            model_name: Name of the model
            version: Version number to activate
        
        Returns:
            Activated version information
        
        Raises:
            ValueError: If version does not exist
        """
        versions = self._load_versions()
        
        # Deactivate current active version
        for v in versions:
            if v.model_name == model_name:
                v.is_active = False

        # Activate requested version
        target_version = next(
            (v for v in versions if v.model_name == model_name and v.version == version),
            None
        )
        if not target_version:
            raise ValueError(f"Version {version} not found for model {model_name}")

        target_version.is_active = True
        self._save_versions(versions)

        # Create symlink for active version
        active_link = self.base_path / model_name / "active"
        if active_link.exists():
            active_link.unlink()
        active_link.symlink_to(self.base_path / model_name / str(version))

        logger.info(f"Activated version {version} for model {model_name}")
        return target_version

    def rollback(self, model_name: str, to_version: Optional[int] = None) -> ModelVersion:
        """Rollback to a previous version.
        
        Args:
            model_name: Name of the model
            to_version: Version to rollback to (defaults to previous version)
        
        Returns:
            Version information after rollback
        
        Raises:
            ValueError: If rollback is not possible
        """
        versions = self._load_versions()
        model_versions = [v for v in versions if v.model_name == model_name]
        
        if not model_versions:
            raise ValueError(f"No versions found for model {model_name}")

        if to_version is None:
            # Get previous version
            active_version = self.get_active_version(model_name)
            if not active_version:
                raise ValueError(f"No active version found for model {model_name}")
            
            available_versions = sorted([v.version for v in model_versions])
            current_idx = available_versions.index(active_version.version)
            if current_idx == 0:
                raise ValueError("Cannot rollback: no earlier version available")
            
            to_version = available_versions[current_idx - 1]

        return self.activate_version(model_name, to_version)

    def list_versions(self, model_name: str) -> List[ModelVersion]:
        """List all versions of a model.
        
        Args:
            model_name: Name of the model
        
        Returns:
            List of version information
        """
        versions = self._load_versions()
        return [v for v in versions if v.model_name == model_name]

    def get_version_path(self, model_name: str, version: Optional[int] = None) -> Path:
        """Get path to model version.
        
        Args:
            model_name: Name of the model
            version: Version number (defaults to active version)
        
        Returns:
            Path to model version
        
        Raises:
            ValueError: If version does not exist
        """
        if version is None:
            active_version = self.get_active_version(model_name)
            if not active_version:
                raise ValueError(f"No active version found for model {model_name}")
            version = active_version.version

        version_path = self.base_path / model_name / str(version)
        if not version_path.exists():
            raise ValueError(f"Version {version} not found for model {model_name}")

        return version_path 