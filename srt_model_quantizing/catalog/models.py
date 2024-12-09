"""Model catalog system with tagging and metadata support."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field, validator

class ModelFramework(str, Enum):
    """Supported model frameworks."""
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    ONNX = "onnx"
    TENSORRT = "tensorrt"

class ModelTask(str, Enum):
    """Supported model tasks."""
    CLASSIFICATION = "classification"
    DETECTION = "detection"
    SEGMENTATION = "segmentation"
    NLP = "nlp"
    SPEECH = "speech"
    VISION = "vision"
    MULTIMODAL = "multimodal"
    OTHER = "other"

class ModelPrecision(str, Enum):
    """Supported model precisions."""
    FP32 = "fp32"
    FP16 = "fp16"
    INT8 = "int8"
    FP8 = "fp8"

class ModelMetadata(BaseModel):
    """Model metadata information."""
    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    framework: ModelFramework = Field(..., description="Model framework")
    task: ModelTask = Field(..., description="Model task/domain")
    precision: ModelPrecision = Field(..., description="Model precision")
    description: str = Field(..., description="Model description")
    tags: Set[str] = Field(default_set(), description="Model tags")
    inputs: Dict[str, Dict] = Field(..., description="Model input specifications")
    outputs: Dict[str, Dict] = Field(..., description="Model output specifications")
    performance_metrics: Optional[Dict[str, float]] = Field(None, description="Model performance metrics")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    author: str = Field(..., description="Model author/owner")
    license: str = Field(..., description="Model license")
    homepage: Optional[str] = Field(None, description="Model homepage/repository URL")
    paper: Optional[str] = Field(None, description="Reference paper URL")
    min_gpu_memory: Optional[int] = Field(None, description="Minimum GPU memory required in MB")
    recommended_batch_size: Optional[int] = Field(None, description="Recommended batch size")
    triton_platform: str = Field("pytorch", description="Triton platform/backend to use")
    triton_max_batch_size: int = Field(1, description="Maximum batch size for Triton")
    
    @validator("tags", pre=True)
    def ensure_unique_tags(cls, v):
        """Ensure tags are unique and lowercase."""
        return {tag.lower() for tag in v}

class ModelExample(BaseModel):
    """Model usage example."""
    name: str = Field(..., description="Example name")
    description: str = Field(..., description="Example description")
    code: str = Field(..., description="Example code snippet")
    inputs: Dict[str, Dict] = Field(..., description="Example input data")
    outputs: Dict[str, Dict] = Field(..., description="Expected outputs")

class ModelDocumentation(BaseModel):
    """Model documentation."""
    overview: str = Field(..., description="Model overview")
    architecture: str = Field(..., description="Model architecture description")
    performance: str = Field(..., description="Performance characteristics")
    limitations: str = Field(..., description="Known limitations")
    examples: List[ModelExample] = Field(default_factory=list, description="Usage examples")
    preprocessing: Optional[str] = Field(None, description="Input preprocessing steps")
    postprocessing: Optional[str] = Field(None, description="Output postprocessing steps")
    references: List[str] = Field(default_factory=list, description="Reference links")

class ModelCatalogEntry(BaseModel):
    """Complete model catalog entry."""
    metadata: ModelMetadata
    documentation: ModelDocumentation
    deployment_config: Optional[Dict] = Field(None, description="Deployment-specific configuration")
    triton_config: Optional[Dict] = Field(None, description="Triton server configuration")

class ModelCatalog:
    """Model catalog manager."""
    
    def __init__(self, storage_path: str):
        """Initialize catalog manager.
        
        Args:
            storage_path: Path to store catalog data
        """
        self.storage_path = storage_path
        self._models: Dict[str, ModelCatalogEntry] = {}
        self._load_catalog()
    
    def _load_catalog(self):
        """Load catalog data from storage."""
        # TODO: Implement catalog loading from storage
        pass
    
    def _save_catalog(self):
        """Save catalog data to storage."""
        # TODO: Implement catalog saving to storage
        pass
    
    def add_model(self, entry: ModelCatalogEntry) -> None:
        """Add a model to the catalog.
        
        Args:
            entry: Model catalog entry
        """
        model_id = f"{entry.metadata.name}:{entry.metadata.version}"
        self._models[model_id] = entry
        self._save_catalog()
    
    def get_model(self, name: str, version: str) -> Optional[ModelCatalogEntry]:
        """Get a model from the catalog.
        
        Args:
            name: Model name
            version: Model version
        
        Returns:
            Model catalog entry if found, None otherwise
        """
        model_id = f"{name}:{version}"
        return self._models.get(model_id)
    
    def list_models(
        self,
        framework: Optional[ModelFramework] = None,
        task: Optional[ModelTask] = None,
        precision: Optional[ModelPrecision] = None,
        tags: Optional[Set[str]] = None
    ) -> List[ModelCatalogEntry]:
        """List models in the catalog with optional filtering.
        
        Args:
            framework: Filter by framework
            task: Filter by task
            precision: Filter by precision
            tags: Filter by tags (all tags must match)
        
        Returns:
            List of matching model catalog entries
        """
        models = self._models.values()
        
        if framework:
            models = [m for m in models if m.metadata.framework == framework]
        if task:
            models = [m for m in models if m.metadata.task == task]
        if precision:
            models = [m for m in models if m.metadata.precision == precision]
        if tags:
            models = [m for m in models if tags.issubset(m.metadata.tags)]
        
        return list(models)
    
    def search_models(self, query: str) -> List[ModelCatalogEntry]:
        """Search models by name, description, or tags.
        
        Args:
            query: Search query
        
        Returns:
            List of matching model catalog entries
        """
        query = query.lower()
        results = []
        
        for model in self._models.values():
            if (query in model.metadata.name.lower() or
                query in model.metadata.description.lower() or
                query in " ".join(model.metadata.tags).lower()):
                results.append(model)
        
        return results
    
    def update_model(self, name: str, version: str, entry: ModelCatalogEntry) -> None:
        """Update a model in the catalog.
        
        Args:
            name: Model name
            version: Model version
            entry: Updated model catalog entry
        """
        model_id = f"{name}:{version}"
        if model_id not in self._models:
            raise KeyError(f"Model {model_id} not found in catalog")
        
        self._models[model_id] = entry
        self._save_catalog()
    
    def delete_model(self, name: str, version: str) -> None:
        """Delete a model from the catalog.
        
        Args:
            name: Model name
            version: Model version
        """
        model_id = f"{name}:{version}"
        if model_id not in self._models:
            raise KeyError(f"Model {model_id} not found in catalog")
        
        del self._models[model_id]
        self._save_catalog()
    
    def get_model_tags(self) -> Set[str]:
        """Get all unique tags in the catalog.
        
        Returns:
            Set of unique tags
        """
        tags = set()
        for model in self._models.values():
            tags.update(model.metadata.tags)
        return tags 