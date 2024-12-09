"""API endpoints for model catalog."""

from typing import Dict, List, Optional, Set

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from ..auth.security import User, get_current_active_user, requires_role
from .models import (ModelCatalog, ModelCatalogEntry, ModelDocumentation,
                    ModelFramework, ModelMetadata, ModelPrecision, ModelTask)
from .storage import CatalogStorage

router = APIRouter(prefix="/v2/catalog", tags=["catalog"])

class ModelResponse(BaseModel):
    """Model response with additional metadata."""
    metadata: ModelMetadata
    documentation: ModelDocumentation
    files: Dict[str, int]
    deployment_status: Optional[str] = None

class ModelsResponse(BaseModel):
    """Response for listing models."""
    models: List[ModelResponse]
    total: int
    frameworks: Dict[str, int]
    tasks: Dict[str, int]
    precisions: Dict[str, int]
    tags: Dict[str, int]

def get_catalog():
    """Get model catalog instance."""
    storage = CatalogStorage("/models/catalog")
    return ModelCatalog(storage)

@router.get("/models", response_model=ModelsResponse)
async def list_models(
    framework: Optional[ModelFramework] = None,
    task: Optional[ModelTask] = None,
    precision: Optional[ModelPrecision] = None,
    tags: Optional[Set[str]] = Query(None),
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user)
) -> ModelsResponse:
    """List models in the catalog with filtering and pagination."""
    catalog = get_catalog()
    
    # Get models with filters
    if search:
        models = catalog.search_models(search)
    else:
        models = catalog.list_models(framework, task, precision, tags)
    
    # Calculate statistics
    frameworks = {}
    tasks = {}
    precisions = {}
    all_tags = {}
    
    for model in models:
        # Count frameworks
        fw = model.metadata.framework.value
        frameworks[fw] = frameworks.get(fw, 0) + 1
        
        # Count tasks
        task = model.metadata.task.value
        tasks[task] = tasks.get(task, 0) + 1
        
        # Count precisions
        prec = model.metadata.precision.value
        precisions[prec] = precisions.get(prec, 0) + 1
        
        # Count tags
        for tag in model.metadata.tags:
            all_tags[tag] = all_tags.get(tag, 0) + 1
    
    # Apply pagination
    paginated_models = models[offset:offset + limit]
    
    # Convert to response format
    model_responses = []
    for model in paginated_models:
        files = catalog.storage.list_model_files(
            model.metadata.name,
            model.metadata.version
        )
        model_responses.append(ModelResponse(
            metadata=model.metadata,
            documentation=model.documentation,
            files=files,
            deployment_status="active"  # TODO: Get actual deployment status
        ))
    
    return ModelsResponse(
        models=model_responses,
        total=len(models),
        frameworks=frameworks,
        tasks=tasks,
        precisions=precisions,
        tags=all_tags
    )

@router.get("/models/{name}/{version}", response_model=ModelResponse)
async def get_model(
    name: str,
    version: str,
    current_user: User = Depends(get_current_active_user)
) -> ModelResponse:
    """Get details of a specific model version."""
    catalog = get_catalog()
    model = catalog.get_model(name, version)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {name}:{version} not found"
        )
    
    files = catalog.storage.list_model_files(name, version)
    
    return ModelResponse(
        metadata=model.metadata,
        documentation=model.documentation,
        files=files,
        deployment_status="active"  # TODO: Get actual deployment status
    )

@router.post("/models", response_model=ModelResponse)
async def create_model(
    entry: ModelCatalogEntry,
    current_user: User = Depends(requires_role("admin"))
) -> ModelResponse:
    """Add a new model to the catalog."""
    catalog = get_catalog()
    
    # Check if model already exists
    if catalog.get_model(entry.metadata.name, entry.metadata.version):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Model {entry.metadata.name}:{entry.metadata.version} already exists"
        )
    
    # Add model to catalog
    catalog.add_model(entry)
    
    files = catalog.storage.list_model_files(
        entry.metadata.name,
        entry.metadata.version
    )
    
    return ModelResponse(
        metadata=entry.metadata,
        documentation=entry.documentation,
        files=files
    )

@router.put("/models/{name}/{version}", response_model=ModelResponse)
async def update_model(
    name: str,
    version: str,
    entry: ModelCatalogEntry,
    current_user: User = Depends(requires_role("admin"))
) -> ModelResponse:
    """Update an existing model in the catalog."""
    catalog = get_catalog()
    
    # Check if model exists
    if not catalog.get_model(name, version):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {name}:{version} not found"
        )
    
    # Update model
    catalog.update_model(name, version, entry)
    
    files = catalog.storage.list_model_files(name, version)
    
    return ModelResponse(
        metadata=entry.metadata,
        documentation=entry.documentation,
        files=files
    )

@router.delete("/models/{name}/{version}")
async def delete_model(
    name: str,
    version: str,
    current_user: User = Depends(requires_role("admin"))
):
    """Delete a model from the catalog."""
    catalog = get_catalog()
    
    # Check if model exists
    if not catalog.get_model(name, version):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {name}:{version} not found"
        )
    
    # Delete model
    catalog.delete_model(name, version)
    catalog.storage.delete_model_files(name, version)
    
    return {"status": "success"}

@router.post("/models/{name}/{version}/files")
async def upload_model_files(
    name: str,
    version: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(requires_role("admin"))
):
    """Upload files for a model."""
    catalog = get_catalog()
    
    # Check if model exists
    if not catalog.get_model(name, version):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {name}:{version} not found"
        )
    
    # Save files
    file_dict = {}
    for file in files:
        content = await file.read()
        file_dict[file.filename] = content
    
    catalog.storage.save_model_files(name, version, file_dict)
    
    return {"status": "success", "uploaded_files": [f.filename for f in files]}

@router.get("/models/{name}/{version}/files/{filename}")
async def download_model_file(
    name: str,
    version: str,
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download a model file."""
    catalog = get_catalog()
    
    # Check if model exists
    if not catalog.get_model(name, version):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {name}:{version} not found"
        )
    
    # Get file content
    content = catalog.storage.get_model_file(name, version, filename)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {filename} not found for model {name}:{version}"
        )
    
    return content

@router.get("/tags")
async def list_tags(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, int]:
    """List all tags and their frequencies."""
    catalog = get_catalog()
    tags = {}
    
    for model in catalog.list_models():
        for tag in model.metadata.tags:
            tags[tag] = tags.get(tag, 0) + 1
    
    return tags 