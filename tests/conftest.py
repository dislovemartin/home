"""Test configuration and fixtures."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from srt_model_quantizing.catalog import ModelCatalog
from srt_model_quantizing.config import Config, config
from srt_model_quantizing.server import app
from srt_model_quantizing.versioning import ModelVersionManager

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_config(temp_dir: Path) -> Config:
    """Create a test configuration."""
    config.storage.model_repository = temp_dir / "models"
    config.storage.catalog_path = temp_dir / "catalog"
    config.storage.model_repository.mkdir(parents=True)
    config.storage.catalog_path.mkdir(parents=True)
    return config

@pytest.fixture
def test_catalog(test_config: Config) -> ModelCatalog:
    """Create a test model catalog."""
    return ModelCatalog(test_config.storage.catalog_path)

@pytest.fixture
def test_version_manager(test_config: Config) -> ModelVersionManager:
    """Create a test version manager."""
    return ModelVersionManager(test_config.storage.model_repository)

@pytest.fixture
def test_client(test_config: Config) -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def admin_token(test_client: TestClient) -> str:
    """Get an admin token for testing."""
    response = test_client.post(
        "/token",
        data={"username": "admin", "password": "admin"}
    )
    return response.json()["access_token"] 