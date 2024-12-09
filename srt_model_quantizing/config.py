"""Configuration settings for the application."""

import os
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field, validator

class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    log_level: str = Field("INFO", description="Logging level")
    json_format: bool = Field(True, description="Use JSON format for logs")
    jaeger_host: str = Field("jaeger", description="Jaeger host")
    jaeger_port: int = Field(6831, description="Jaeger port")
    prometheus_port: int = Field(8889, description="Prometheus metrics port")

class SecurityConfig(BaseModel):
    """Security configuration."""
    secret_key: str = Field(
        os.getenv("SECRET_KEY", "your-secret-key-stored-in-env"),
        description="JWT secret key"
    )
    algorithm: str = Field("HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(30, description="Token expiration time in minutes")
    admin_username: str = Field("admin", description="Admin username")
    admin_password: str = Field("admin", description="Admin password")

class StorageConfig(BaseModel):
    """Storage configuration."""
    model_repository: Path = Field(
        Path(os.getenv("MODEL_REPOSITORY", "/models")),
        description="Model repository path"
    )
    catalog_path: Path = Field(
        Path(os.getenv("CATALOG_PATH", "/models/catalog")),
        description="Model catalog path"
    )
    max_backup_files: int = Field(5, description="Maximum number of backup files to keep")

    @validator("model_repository", "catalog_path")
    def create_directory(cls, v):
        """Create directory if it doesn't exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

class TritonConfig(BaseModel):
    """Triton server configuration."""
    url: str = Field("localhost:8000", description="Triton server URL")
    http_port: int = Field(8000, description="HTTP port")
    grpc_port: int = Field(8001, description="gRPC port")
    metrics_port: int = Field(8002, description="Metrics port")
    model_control_mode: str = Field("explicit", description="Model control mode")
    strict_model_config: bool = Field(True, description="Strict model configuration")
    rate_limit: Optional[float] = Field(None, description="Rate limit in requests per second")

class MLFlowConfig(BaseModel):
    """MLflow configuration."""
    tracking_uri: str = Field(
        os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow/mlflow.db"),
        description="MLflow tracking URI"
    )
    artifact_root: str = Field(
        os.getenv("MLFLOW_ARTIFACT_ROOT", "/mlflow/artifacts"),
        description="MLflow artifact root"
    )
    experiment_name: str = Field(
        "srt-model-quantizing",
        description="MLflow experiment name"
    )

class NeMoConfig(BaseModel):
    """NeMo framework configuration."""
    default_precision: str = Field("fp16", description="Default precision for optimization")
    use_transformer_engine: bool = Field(True, description="Use Transformer Engine")
    fp8_hybrid: bool = Field(True, description="Use FP8 hybrid mode")
    gradient_checkpointing: bool = Field(True, description="Use gradient checkpointing")
    max_batch_size: int = Field(128, description="Maximum batch size")

class Config(BaseModel):
    """Main application configuration."""
    env: str = Field(os.getenv("ENV", "development"), description="Environment")
    debug: bool = Field(os.getenv("DEBUG", "false").lower() == "true", description="Debug mode")
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    workers: int = Field(4, description="Number of worker processes")
    reload: bool = Field(True, description="Enable auto-reload")
    ssl_keyfile: Optional[str] = Field(None, description="SSL key file")
    ssl_certfile: Optional[str] = Field(None, description="SSL certificate file")
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    triton: TritonConfig = Field(default_factory=TritonConfig)
    mlflow: MLFlowConfig = Field(default_factory=MLFlowConfig)
    nemo: NeMoConfig = Field(default_factory=NeMoConfig)
    cors_origins: List[str] = Field(["*"], description="CORS allowed origins")

    class Config:
        """Pydantic config."""
        env_prefix = "SRT_"
        case_sensitive = False

def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config()

# Global configuration instance
config = load_config() 