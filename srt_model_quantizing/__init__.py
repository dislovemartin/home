"""SRT Model Quantizing - Enterprise Model Optimization Platform."""

__version__ = "1.0.0"
__author__ = "SolidRusT Networks"
__email__ = "info@soln.ai"
__description__ = "Enterprise-grade model optimization and serving platform"

from .catalog import ModelCatalog, ModelCatalogEntry
from .monitoring import setup_logging, setup_telemetry
from .nemo import ModelOptimizer, OptimizationConfig
from .versioning import ModelVersionManager

__all__ = [
    "ModelCatalog",
    "ModelCatalogEntry",
    "ModelOptimizer",
    "OptimizationConfig",
    "ModelVersionManager",
    "setup_logging",
    "setup_telemetry",
] 