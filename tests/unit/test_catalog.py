"""Unit tests for the catalog module."""

import pytest

from srt_model_quantizing.catalog import ModelCatalog, ModelCatalogEntry
from srt_model_quantizing.catalog.models import Framework, ModelMetadata, Precision, Task

def test_add_model(test_catalog: ModelCatalog):
    """Test adding a model to the catalog."""
    # Create test model entry
    metadata = ModelMetadata(
        name="test-model",
        version="1.0.0",
        framework=Framework.PYTORCH,
        task=Task.NLP,
        precision=Precision.FP16,
        tags={"transformer", "bert"}
    )
    entry = ModelCatalogEntry(metadata=metadata)
    
    # Add model to catalog
    test_catalog.add_model(entry)
    
    # Verify model was added
    stored_model = test_catalog.get_model("test-model", "1.0.0")
    assert stored_model is not None
    assert stored_model.metadata.name == "test-model"
    assert stored_model.metadata.version == "1.0.0"
    assert stored_model.metadata.framework == Framework.PYTORCH
    assert stored_model.metadata.task == Task.NLP
    assert stored_model.metadata.precision == Precision.FP16
    assert stored_model.metadata.tags == {"transformer", "bert"}

def test_list_models(test_catalog: ModelCatalog):
    """Test listing models from the catalog."""
    # Add test models
    models = [
        ModelCatalogEntry(
            metadata=ModelMetadata(
                name=f"model-{i}",
                version="1.0.0",
                framework=Framework.PYTORCH,
                task=Task.NLP if i % 2 == 0 else Task.CV,
                precision=Precision.FP16,
                tags={"transformer"} if i % 2 == 0 else {"cnn"}
            )
        )
        for i in range(4)
    ]
    
    for model in models:
        test_catalog.add_model(model)
    
    # Test listing all models
    all_models = test_catalog.list_models()
    assert len(all_models) == 4
    
    # Test filtering by framework
    pytorch_models = test_catalog.list_models(framework=Framework.PYTORCH)
    assert len(pytorch_models) == 4
    
    # Test filtering by task
    nlp_models = test_catalog.list_models(task=Task.NLP)
    assert len(nlp_models) == 2
    
    # Test filtering by precision
    fp16_models = test_catalog.list_models(precision=Precision.FP16)
    assert len(fp16_models) == 4
    
    # Test filtering by tags
    transformer_models = test_catalog.list_models(tags={"transformer"})
    assert len(transformer_models) == 2

def test_delete_model(test_catalog: ModelCatalog):
    """Test deleting a model from the catalog."""
    # Add test model
    metadata = ModelMetadata(
        name="test-model",
        version="1.0.0",
        framework=Framework.PYTORCH,
        task=Task.NLP,
        precision=Precision.FP16,
        tags={"transformer"}
    )
    entry = ModelCatalogEntry(metadata=metadata)
    test_catalog.add_model(entry)
    
    # Verify model exists
    assert test_catalog.get_model("test-model", "1.0.0") is not None
    
    # Delete model
    test_catalog.delete_model("test-model", "1.0.0")
    
    # Verify model was deleted
    assert test_catalog.get_model("test-model", "1.0.0") is None

def test_update_model(test_catalog: ModelCatalog):
    """Test updating a model in the catalog."""
    # Add test model
    metadata = ModelMetadata(
        name="test-model",
        version="1.0.0",
        framework=Framework.PYTORCH,
        task=Task.NLP,
        precision=Precision.FP16,
        tags={"transformer"}
    )
    entry = ModelCatalogEntry(metadata=metadata)
    test_catalog.add_model(entry)
    
    # Update model
    updated_metadata = ModelMetadata(
        name="test-model",
        version="1.0.0",
        framework=Framework.PYTORCH,
        task=Task.NLP,
        precision=Precision.FP16,
        tags={"transformer", "bert"}  # Add new tag
    )
    updated_entry = ModelCatalogEntry(metadata=updated_metadata)
    test_catalog.update_model(updated_entry)
    
    # Verify update
    stored_model = test_catalog.get_model("test-model", "1.0.0")
    assert stored_model is not None
    assert stored_model.metadata.tags == {"transformer", "bert"}

def test_model_not_found(test_catalog: ModelCatalog):
    """Test handling of non-existent models."""
    # Try to get non-existent model
    model = test_catalog.get_model("non-existent", "1.0.0")
    assert model is None
    
    # Try to delete non-existent model
    with pytest.raises(KeyError):
        test_catalog.delete_model("non-existent", "1.0.0")
    
    # Try to update non-existent model
    metadata = ModelMetadata(
        name="non-existent",
        version="1.0.0",
        framework=Framework.PYTORCH,
        task=Task.NLP,
        precision=Precision.FP16,
        tags={"transformer"}
    )
    entry = ModelCatalogEntry(metadata=metadata)
    with pytest.raises(KeyError):
        test_catalog.update_model(entry)

def test_duplicate_model(test_catalog: ModelCatalog):
    """Test handling of duplicate models."""
    # Add test model
    metadata = ModelMetadata(
        name="test-model",
        version="1.0.0",
        framework=Framework.PYTORCH,
        task=Task.NLP,
        precision=Precision.FP16,
        tags={"transformer"}
    )
    entry = ModelCatalogEntry(metadata=metadata)
    test_catalog.add_model(entry)
    
    # Try to add same model again
    with pytest.raises(ValueError):
        test_catalog.add_model(entry) 