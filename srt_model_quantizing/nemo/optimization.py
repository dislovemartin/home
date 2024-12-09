"""NeMo framework integration for model optimization."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import torch
from nemo.core.classes import ModelPT
from nemo.core.config import hydra_runner
from nemo.utils import logging
from omegaconf import DictConfig, OmegaConf

@dataclass
class OptimizationConfig:
    """Configuration for model optimization."""
    precision: str = "fp16"  # One of: fp32, fp16, bf16, int8, fp8
    use_transformer_engine: bool = True
    fp8_hybrid: bool = True
    fp8_margin: int = 0
    fp8_interval: int = 1
    fp8_amax_history_len: int = 32
    fp8_amax_compute_algo: str = "max"
    use_emha: bool = False
    gradient_checkpointing: bool = True

class ModelOptimizer:
    """NeMo model optimization handler."""
    
    def __init__(
        self,
        model_path: Union[str, Path],
        config: Optional[OptimizationConfig] = None
    ):
        """Initialize model optimizer.
        
        Args:
            model_path: Path to the model
            config: Optimization configuration
        """
        self.model_path = Path(model_path)
        self.config = config or OptimizationConfig()
        self.logger = logging.get_logger()

    def _create_nemo_config(self) -> DictConfig:
        """Create NeMo configuration."""
        config = {
            "trainer": {
                "precision": self.config.precision,
                "gradient_clip_val": 1.0,
                "devices": 1,
                "accelerator": "gpu",
                "strategy": "ddp",
                "max_epochs": 1,
            },
            "model": {
                "transformer_engine": self.config.use_transformer_engine,
                "fp8": self.config.precision == "fp8",
                "fp8_hybrid": self.config.fp8_hybrid,
                "fp8_margin": self.config.fp8_margin,
                "fp8_interval": self.config.fp8_interval,
                "fp8_amax_history_len": self.config.fp8_amax_history_len,
                "fp8_amax_compute_algo": self.config.fp8_amax_compute_algo,
                "use_emha": self.config.use_emha,
                "gradient_checkpointing": self.config.gradient_checkpointing,
            }
        }
        return OmegaConf.create(config)

    def optimize(self, output_path: Union[str, Path]) -> Path:
        """Optimize the model using NeMo framework.
        
        Args:
            output_path: Path to save the optimized model
        
        Returns:
            Path to the optimized model
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Load model
            self.logger.info(f"Loading model from {self.model_path}")
            model = ModelPT.restore_from(self.model_path)

            # Apply optimization configuration
            config = self._create_nemo_config()
            model.cfg = config

            # Enable Transformer Engine if specified
            if self.config.use_transformer_engine:
                self.logger.info("Enabling Transformer Engine")
                model.enable_transformer_engine()

            # Enable gradient checkpointing if specified
            if self.config.gradient_checkpointing:
                self.logger.info("Enabling gradient checkpointing")
                model.enable_gradient_checkpointing()

            # Save optimized model
            self.logger.info(f"Saving optimized model to {output_path}")
            model.save_to(output_path)

            return output_path

        except Exception as e:
            self.logger.error(f"Error optimizing model: {str(e)}")
            raise

@hydra_runner(config_path=None, config_name="optimization")
def optimize_model(cfg: DictConfig) -> None:
    """Hydra entry point for model optimization."""
    optimizer = ModelOptimizer(
        model_path=cfg.model_path,
        config=OptimizationConfig(**cfg.optimization)
    )
    optimizer.optimize(cfg.output_path)

if __name__ == "__main__":
    # Example usage:
    # python optimization.py model_path=/path/to/model output_path=/path/to/output
    optimize_model() 