"""Storage backend for model catalog."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .models import ModelCatalogEntry

class CatalogStorage:
    """Storage backend for model catalog."""
    
    def __init__(self, storage_path: str):
        """Initialize storage backend.
        
        Args:
            storage_path: Path to store catalog data
        """
        self.storage_path = Path(storage_path)
        self.catalog_file = self.storage_path / "catalog.json"
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _serialize_datetime(self, obj):
        """JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def _deserialize_datetime(self, obj: Dict) -> Dict:
        """Convert ISO format datetime strings back to datetime objects."""
        for key in ["created_at", "updated_at"]:
            if key in obj and isinstance(obj[key], str):
                obj[key] = datetime.fromisoformat(obj[key])
        return obj
    
    def load(self) -> Dict[str, ModelCatalogEntry]:
        """Load catalog data from storage.
        
        Returns:
            Dictionary mapping model IDs to catalog entries
        """
        if not self.catalog_file.exists():
            return {}
        
        try:
            with open(self.catalog_file, "r") as f:
                data = json.load(f)
                # Convert stored data back to ModelCatalogEntry objects
                return {
                    model_id: ModelCatalogEntry.parse_obj(
                        self._deserialize_datetime(entry)
                    )
                    for model_id, entry in data.items()
                }
        except Exception as e:
            raise RuntimeError(f"Failed to load catalog: {str(e)}")
    
    def save(self, models: Dict[str, ModelCatalogEntry]) -> None:
        """Save catalog data to storage.
        
        Args:
            models: Dictionary mapping model IDs to catalog entries
        """
        try:
            # Create backup of existing catalog
            if self.catalog_file.exists():
                backup_path = self.storage_path / f"catalog.backup.{int(datetime.now().timestamp())}.json"
                os.rename(self.catalog_file, backup_path)
            
            # Save new catalog data
            with open(self.catalog_file, "w") as f:
                json.dump(
                    {
                        model_id: entry.dict()
                        for model_id, entry in models.items()
                    },
                    f,
                    indent=2,
                    default=self._serialize_datetime
                )
        except Exception as e:
            raise RuntimeError(f"Failed to save catalog: {str(e)}")
    
    def get_model_files_path(self, name: str, version: str) -> Path:
        """Get path for model files.
        
        Args:
            name: Model name
            version: Model version
        
        Returns:
            Path to model files directory
        """
        model_path = self.storage_path / "models" / name / version
        model_path.mkdir(parents=True, exist_ok=True)
        return model_path
    
    def save_model_files(self, name: str, version: str, files: Dict[str, bytes]) -> None:
        """Save model files to storage.
        
        Args:
            name: Model name
            version: Model version
            files: Dictionary mapping file names to contents
        """
        model_path = self.get_model_files_path(name, version)
        
        try:
            for filename, content in files.items():
                file_path = model_path / filename
                with open(file_path, "wb") as f:
                    f.write(content)
        except Exception as e:
            raise RuntimeError(f"Failed to save model files: {str(e)}")
    
    def get_model_file(self, name: str, version: str, filename: str) -> Optional[bytes]:
        """Get contents of a model file.
        
        Args:
            name: Model name
            version: Model version
            filename: Name of the file to retrieve
        
        Returns:
            File contents if found, None otherwise
        """
        file_path = self.get_model_files_path(name, version) / filename
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read model file: {str(e)}")
    
    def delete_model_files(self, name: str, version: str) -> None:
        """Delete all files for a model version.
        
        Args:
            name: Model name
            version: Model version
        """
        model_path = self.get_model_files_path(name, version)
        
        try:
            if model_path.exists():
                for file_path in model_path.iterdir():
                    file_path.unlink()
                model_path.rmdir()
        except Exception as e:
            raise RuntimeError(f"Failed to delete model files: {str(e)}")
    
    def list_model_files(self, name: str, version: str) -> Dict[str, int]:
        """List files for a model version.
        
        Args:
            name: Model name
            version: Model version
        
        Returns:
            Dictionary mapping file names to sizes in bytes
        """
        model_path = self.get_model_files_path(name, version)
        
        if not model_path.exists():
            return {}
        
        try:
            return {
                file_path.name: file_path.stat().st_size
                for file_path in model_path.iterdir()
                if file_path.is_file()
            }
        except Exception as e:
            raise RuntimeError(f"Failed to list model files: {str(e)}")
    
    def cleanup_old_backups(self, max_backups: int = 5) -> None:
        """Clean up old catalog backup files.
        
        Args:
            max_backups: Maximum number of backup files to keep
        """
        try:
            backup_files = sorted([
                f for f in self.storage_path.iterdir()
                if f.name.startswith("catalog.backup.")
            ], key=lambda x: x.stat().st_mtime, reverse=True)
            
            for backup_file in backup_files[max_backups:]:
                backup_file.unlink()
        except Exception as e:
            raise RuntimeError(f"Failed to cleanup old backups: {str(e)}") 