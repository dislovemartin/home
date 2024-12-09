"""Integration tests for the API endpoints."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from srt_model_quantizing.catalog.models import Framework, ModelMetadata, Precision, Task

def test_login(test_client: TestClient):
    """Test login endpoint."""
    # Test successful login
    response = test_client.post(
        "/token",
        data={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    
    # Test failed login
    response = test_client.post(
        "/token",
        data={"username": "wrong", "password": "wrong"}
    )
    assert response.status_code == 401

def test_list_models(test_client: TestClient, admin_token: str):
    """Test listing models endpoint."""
    # Test without authentication
    response = test_client.get("/v2/catalog/models")
    assert response.status_code == 401
    
    # Test with authentication
    response = test_client.get(
        "/v2/catalog/models",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_add_model(test_client: TestClient, admin_token: str, tmp_path: Path):
    """Test adding a model endpoint."""
    # Create test model data
    model_data = {
        "metadata": {
            "name": "test-model",
            "version": "1.0.0",
            "framework": "pytorch",
            "task": "nlp",
            "precision": "fp16",
            "tags": ["transformer", "bert"]
        }
    }
    
    # Test without authentication
    response = test_client.post(
        "/v2/catalog/models",
        json=model_data
    )
    assert response.status_code == 401
    
    # Test with authentication
    response = test_client.post(
        "/v2/catalog/models",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=model_data
    )
    assert response.status_code == 200
    assert response.json()["metadata"]["name"] == "test-model"
    
    # Test adding duplicate model
    response = test_client.post(
        "/v2/catalog/models",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=model_data
    )
    assert response.status_code == 400

def test_get_model(test_client: TestClient, admin_token: str):
    """Test getting a model endpoint."""
    # Add test model first
    model_data = {
        "metadata": {
            "name": "test-model",
            "version": "1.0.0",
            "framework": "pytorch",
            "task": "nlp",
            "precision": "fp16",
            "tags": ["transformer", "bert"]
        }
    }
    test_client.post(
        "/v2/catalog/models",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=model_data
    )
    
    # Test without authentication
    response = test_client.get("/v2/catalog/models/test-model/1.0.0")
    assert response.status_code == 401
    
    # Test with authentication
    response = test_client.get(
        "/v2/catalog/models/test-model/1.0.0",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["metadata"]["name"] == "test-model"
    
    # Test non-existent model
    response = test_client.get(
        "/v2/catalog/models/non-existent/1.0.0",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404

def test_delete_model(test_client: TestClient, admin_token: str):
    """Test deleting a model endpoint."""
    # Add test model first
    model_data = {
        "metadata": {
            "name": "test-model",
            "version": "1.0.0",
            "framework": "pytorch",
            "task": "nlp",
            "precision": "fp16",
            "tags": ["transformer", "bert"]
        }
    }
    test_client.post(
        "/v2/catalog/models",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=model_data
    )
    
    # Test without authentication
    response = test_client.delete("/v2/catalog/models/test-model/1.0.0")
    assert response.status_code == 401
    
    # Test with authentication
    response = test_client.delete(
        "/v2/catalog/models/test-model/1.0.0",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Verify model was deleted
    response = test_client.get(
        "/v2/catalog/models/test-model/1.0.0",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
    
    # Test deleting non-existent model
    response = test_client.delete(
        "/v2/catalog/models/non-existent/1.0.0",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404

def test_optimize_model(test_client: TestClient, admin_token: str, tmp_path: Path):
    """Test model optimization endpoint."""
    # Add test model first
    model_data = {
        "metadata": {
            "name": "test-model",
            "version": "1.0.0",
            "framework": "pytorch",
            "task": "nlp",
            "precision": "fp16",
            "tags": ["transformer", "bert"]
        }
    }
    test_client.post(
        "/v2/catalog/models",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=model_data
    )
    
    # Create optimization config
    config = {
        "precision": "fp16",
        "use_transformer_engine": True,
        "fp8_hybrid": True,
        "gradient_checkpointing": True,
        "max_batch_size": 128
    }
    
    # Test without authentication
    response = test_client.post(
        "/v2/models/test-model/optimize",
        json=config
    )
    assert response.status_code == 401
    
    # Test with authentication
    response = test_client.post(
        "/v2/models/test-model/optimize",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=config
    )
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "success"
    
    # Test optimizing non-existent model
    response = test_client.post(
        "/v2/models/non-existent/optimize",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=config
    )
    assert response.status_code == 404

def test_filter_models(test_client: TestClient, admin_token: str):
    """Test model filtering endpoint."""
    # Add test models
    models = [
        {
            "metadata": {
                "name": f"model-{i}",
                "version": "1.0.0",
                "framework": "pytorch",
                "task": "nlp" if i % 2 == 0 else "cv",
                "precision": "fp16",
                "tags": ["transformer"] if i % 2 == 0 else ["cnn"]
            }
        }
        for i in range(4)
    ]
    
    for model in models:
        test_client.post(
            "/v2/catalog/models",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=model
        )
    
    # Test filtering by framework
    response = test_client.get(
        "/v2/catalog/models?framework=pytorch",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 4
    
    # Test filtering by task
    response = test_client.get(
        "/v2/catalog/models?task=nlp",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 2
    
    # Test filtering by precision
    response = test_client.get(
        "/v2/catalog/models?precision=fp16",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 4
    
    # Test filtering by tags
    response = test_client.get(
        "/v2/catalog/models?tags=transformer",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 2 