"""Configuration management for SRT Model Quantizing."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, BaseSettings, Field


class StorageConfig(BaseModel):
    """Storage configuration."""
    base_path: Path = Field(default=Path("./storage"))
    raw_dir: Path = Field(default=Path("models/raw"))
    quantized_dir: Path = Field(default=Path("models/quantized"))
    repository_dir: Path = Field(default=Path("models/repository"))

class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    log_level: str = "INFO"
    telemetry_enabled: bool = True
    metrics_enabled: bool = True
    tracing_enabled: bool = True

class SecurityConfig(BaseModel):
    """Security configuration."""
    jwt_secret: str
    token_expiry: int = 3600
    allow_cors: bool = False
    cors_origins: list[str] = Field(default_factory=list)

class ServiceConfig(BaseModel):
    """Service configuration."""
    host: str = "localhost"
    port: int
    workers: int = 1
    reload: bool = False

class ServicesConfig(BaseModel):
    """Services configuration."""
    api: ServiceConfig
    frontend: ServiceConfig

class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: str
    path: Optional[str] = None
    url: Optional[str] = None

class CacheConfig(BaseModel):
    """Cache configuration."""
    type: str
    url: str
    ttl: int = 3600

class ModelOptimizationConfig(BaseModel):
    """Model optimization configuration."""
    default_precision: str = "fp16"
    batch_size: int = 32
    num_workers: int = 4
    use_cuda: bool = True

class DevelopmentConfig(BaseModel):
    """Development configuration."""
    debug: bool = False
    profiling: bool = False
    auto_reload: bool = False
    test_data_path: Optional[Path] = None

class Settings(BaseSettings):
    """Main settings class."""
    storage: StorageConfig
    monitoring: MonitoringConfig
    security: SecurityConfig
    services: ServicesConfig
    database: DatabaseConfig
    cache: CacheConfig
    model_optimization: ModelOptimizationConfig
    development: DevelopmentConfig

    class Config:
        """Pydantic config."""
        env_prefix = "SRT_"
        case_sensitive = False

def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def get_settings(config_path: Optional[Path] = None) -> Settings:
    """Get application settings."""
    # Default configuration
    config_dict = {
        "storage": {
            "base_path": "./storage",
            "raw_dir": "models/raw",
            "quantized_dir": "models/quantized",
            "repository_dir": "models/repository",
        },
        "monitoring": {
            "log_level": "INFO",
            "telemetry_enabled": True,
            "metrics_enabled": True,
            "tracing_enabled": True,
        },
        "security": {
            "jwt_secret": os.getenv("SRT_JWT_SECRET", "default_secret"),
            "token_expiry": 3600,
            "allow_cors": False,
            "cors_origins": [],
        },
        "services": {
            "api": {
                "host": "localhost",
                "port": 8000,
                "workers": 1,
                "reload": False,
            },
            "frontend": {
                "host": "localhost",
                "port": 3000,
                "workers": 1,
                "reload": False,
            },
        },
        "database": {
            "type": "sqlite",
            "path": "./storage/app.db",
        },
        "cache": {
            "type": "memory",
            "url": "memory://",
            "ttl": 3600,
        },
        "model_optimization": {
            "default_precision": "fp16",
            "batch_size": 32,
            "num_workers": 4,
            "use_cuda": True,
        },
        "development": {
            "debug": False,
            "profiling": False,
            "auto_reload": False,
        },
    }

    # Load configuration from file if provided
    if config_path:
        yaml_config = load_yaml_config(config_path)
        config_dict.update(yaml_config)

    # Create settings object
    settings = Settings(**config_dict)

    # Ensure storage directories exist
    os.makedirs(settings.storage.base_path, exist_ok=True)
    for dir_path in [
        settings.storage.raw_dir,
        settings.storage.quantized_dir,
        settings.storage.repository_dir,
    ]:
        os.makedirs(settings.storage.base_path / dir_path, exist_ok=True)

    return settings

# Global settings instance
settings = get_settings() 