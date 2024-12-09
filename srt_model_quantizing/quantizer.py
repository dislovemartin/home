"""Core quantization module using NVIDIA NIM."""

import os
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple
import logging
from contextlib import contextmanager
import time

import torch
from transformers import AutoModel, AutoTokenizer, PreTrainedModel, PreTrainedTokenizer
from pydantic import BaseModel, Field, validator
import tensorrt as trt
from polygraphy.backend.trt import CreateConfig, Profile, NetworkFromOnnxPath
from polygraphy.backend.trt import engine_from_network, save_engine
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class QuantizationConfig(BaseModel):
    """Configuration for model quantization."""
    model_name: str = Field(..., description="Name or path of the model to quantize")
    output_dir: Path = Field(..., description="Directory to save quantized model")
    precision: str = Field("fp16", description="Quantization precision (fp16, int8)")
    max_workspace_size: int = Field(1 << 30, description="Maximum workspace size in bytes")
    max_batch_size: int = Field(1, description="Maximum batch size for inference")
    dynamic_shapes: bool = Field(True, description="Enable dynamic shapes")
    calibration_data: Optional[str] = Field(None, description="Path to calibration data for INT8")
    optimization_level: int = Field(3, description="TensorRT optimization level (0-5)")
    
    @validator('precision')
    def validate_precision(cls, v):
        if v not in ["fp16", "int8"]:
            raise ValueError("Precision must be either 'fp16' or 'int8'")
        return v
    
    @validator('optimization_level')
    def validate_optimization_level(cls, v):
        if not 0 <= v <= 5:
            raise ValueError("Optimization level must be between 0 and 5")
        return v

class ModelQuantizer:
    """Main class for model quantization using NVIDIA NIM."""
    
    def __init__(self, config: QuantizationConfig):
        self.config = config
        self.logger = trt.Logger(trt.Logger.WARNING)
        self.model: Optional[PreTrainedModel] = None
        self.tokenizer: Optional[PreTrainedTokenizer] = None
        
        # Ensure output directory exists
        os.makedirs(self.config.output_dir, exist_ok=True)
        
    @contextmanager
    def timer(self, task_name: str):
        """Context manager for timing operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            logger.info(f"{task_name} completed in {duration:.2f} seconds")
    
    def prepare_model(self) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
        """Download and prepare the model for quantization."""
        with self.timer("Model preparation"):
            try:
                console.log(f"Downloading model: {self.config.model_name}")
                self.model = AutoModel.from_pretrained(
                    self.config.model_name,
                    torchscript=True,  # Enable TorchScript for better optimization
                    return_dict=False  # Simplify model outputs
                )
                self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
                
                # Move model to GPU if available
                if torch.cuda.is_available():
                    self.model = self.model.cuda()
                    logger.info("Model moved to GPU")
                
                self.model.eval()  # Set to evaluation mode
                return self.model, self.tokenizer
                
            except Exception as e:
                logger.error(f"Failed to prepare model: {str(e)}")
                raise
        
    def export_to_onnx(self, sample_input: Optional[torch.Tensor] = None) -> Path:
        """Export the model to ONNX format with optimizations."""
        with self.timer("ONNX export"):
            if sample_input is None:
                sample_input = torch.ones(1, 32, dtype=torch.long)
                if torch.cuda.is_available():
                    sample_input = sample_input.cuda()
            
            onnx_path = self.config.output_dir / f"{self.config.model_name.split('/')[-1]}.onnx"
            
            # Enable ONNX optimizations
            torch.onnx.export(
                self.model,
                sample_input,
                onnx_path,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes={'input': {0: 'batch_size', 1: 'sequence_length'},
                            'output': {0: 'batch_size', 1: 'sequence_length'}}
                if self.config.dynamic_shapes else None,
                opset_version=13,
                do_constant_folding=True,  # Enable constant folding optimization
                verbose=False,
                export_params=True,
                training=torch.onnx.TrainingMode.EVAL,
                use_external_data_format=False
            )
            
            logger.info(f"Model exported to ONNX: {onnx_path}")
            return onnx_path
        
    def build_engine(self, onnx_path: Path) -> None:
        """Build TensorRT engine from ONNX model with enhanced configuration."""
        with self.timer("Engine building"):
            try:
                # Create optimized TensorRT config
                config = CreateConfig(
                    fp16=self.config.precision == "fp16",
                    int8=self.config.precision == "int8",
                    max_workspace_size=self.config.max_workspace_size,
                    profiles=[Profile().add(
                        "input",
                        min=(1, 32),
                        opt=(self.config.max_batch_size // 2, 128),
                        max=(self.config.max_batch_size, 512)
                    )] if self.config.dynamic_shapes else None,
                    optimization_level=self.config.optimization_level,
                    precision_constraints="obey",
                    strict_types=True
                )
                
                # Progress bar with enhanced visuals
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TimeElapsedColumn()
                ) as progress:
                    task = progress.add_task("[cyan]Building TensorRT engine...", total=100)
                    
                    # Create network from ONNX
                    network = NetworkFromOnnxPath(onnx_path)
                    
                    # Build and optimize engine
                    engine = engine_from_network(
                        network,
                        config=config,
                        save_timing_cache=True
                    )
                    
                    progress.update(task, advance=50)
                    
                    # Save the optimized engine
                    engine_path = self.config.output_dir / f"{self.config.model_name.split('/')[-1]}.engine"
                    save_engine(engine, engine_path)
                    
                    progress.update(task, advance=50)
                    
                console.log(f"[green]Engine saved to: {engine_path}")
                logger.info(f"Engine built successfully: {engine_path}")
                
            except Exception as e:
                logger.error(f"Failed to build engine: {str(e)}")
                raise
    
    def quantize(self) -> None:
        """Main quantization pipeline with enhanced error handling and logging."""
        try:
            with self.timer("Complete quantization process"):
                # Prepare model
                self.prepare_model()
                
                # Export to ONNX
                onnx_path = self.export_to_onnx()
                
                # Build TensorRT engine
                self.build_engine(onnx_path)
                
                console.log("[green]Quantization completed successfully!")
                
        except Exception as e:
            error_msg = f"Error during quantization: {str(e)}"
            logger.error(error_msg)
            console.log(f"[red]{error_msg}")
            raise
        finally:
            # Cleanup
            if hasattr(self, 'model') and self.model is not None:
                del self.model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()