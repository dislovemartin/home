"""FastAPI server for SRT Model Quantizing."""

import logging
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .auth.security import setup_auth, requires_role, User
from .catalog import setup_catalog
from .config.settings import get_settings
from .monitoring.logging import setup_logging
from .monitoring.metrics import setup_metrics
from .monitoring.storage_metrics import setup_storage_metrics
from .monitoring.telemetry import setup_telemetry
from .storage.cleanup import setup_cleanup_manager

# Initialize settings
settings = get_settings()

# Set up logging
logger = setup_logging(
    service_name="srt-model-quantizing",
    log_level=settings.monitoring.log_level
)

# Create FastAPI app
app = FastAPI(
    title="SRT Model Quantizing",
    description="Enterprise-grade model optimization and serving platform",
    version="1.0.0"
)

# Set up CORS
if settings.security.allow_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Set up monitoring
metrics = setup_metrics()
tracer = setup_telemetry(app)
storage_metrics = setup_storage_metrics()

# Set up authentication
auth = setup_auth(app)

# Set up model catalog
catalog = setup_catalog()

# Set up storage cleanup
cleanup_manager = setup_cleanup_manager()

# Mount metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/storage/info")
async def get_storage_info():
    """Get storage information."""
    try:
        return storage_metrics.get_storage_info()
    except Exception as e:
        logger.error(f"Failed to get storage info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get storage information")

@app.post("/storage/collect")
async def collect_storage_metrics():
    """Manually trigger storage metrics collection."""
    try:
        storage_metrics.collect_metrics()
        return {"status": "success", "message": "Storage metrics collected"}
    except Exception as e:
        logger.error(f"Failed to collect storage metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect storage metrics")

@app.post("/storage/cleanup")
async def run_storage_cleanup(
    dry_run: bool = False,
    current_user: User = Depends(requires_role("admin"))
) -> Dict:
    """Run storage cleanup with configured policies."""
    try:
        results = cleanup_manager.run_cleanup(dry_run=dry_run)
        return {
            "status": "success",
            "dry_run": dry_run,
            "results": results
        }
    except Exception as e:
        logger.error(f"Failed to run storage cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to run storage cleanup")

@app.get("/storage/cleanup/policies")
async def list_cleanup_policies(
    current_user: User = Depends(requires_role("admin"))
) -> Dict:
    """List configured cleanup policies."""
    return {
        "policies": [
            {
                "name": policy.name,
                "description": policy.description
            }
            for policy in cleanup_manager.policies
        ]
    } 