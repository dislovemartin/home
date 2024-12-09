"""Utility functions for the SRT Model Quantizing tool."""

import os
from pathlib import Path
from typing import Optional, Union, List

import torch
from rich.console import Console

console = Console()

def check_gpu_availability() -> bool:
    """Check if CUDA GPU is available."""
    return torch.cuda.is_available()

def get_gpu_info() -> dict:
    """Get information about available GPUs."""
    if not check_gpu_availability():
        return {"available": False, "devices": []}
    
    devices = []
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        devices.append({
            "name": props.name,
            "compute_capability": f"{props.major}.{props.minor}",
            "total_memory": props.total_memory // (1024*1024),  # Convert to MB
            "max_threads_per_block": props.max_threads_per_block
        })
    
    return {
        "available": True,
        "devices": devices,
        "cuda_version": torch.version.cuda
    }

def validate_output_dir(path: Union[str, Path]) -> Path:
    """Validate and create output directory if it doesn't exist."""
    path = Path(path)
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except Exception as e:
        console.print(f"[red]Error creating output directory: {str(e)}")
        raise

def get_model_size(model: torch.nn.Module) -> float:
    """Get the size of a PyTorch model in MB."""
    param_size = 0
    for param in model.parameters():
        param_size += param.nelement() * param.element_size()
    buffer_size = 0
    for buffer in model.buffers():
        buffer_size += buffer.nelement() * buffer.element_size()
    
    size_mb = (param_size + buffer_size) / (1024 * 1024)
    return round(size_mb, 2)

def validate_precision(precision: str) -> str:
    """Validate the requested precision."""
    valid_precisions = ["fp16", "int8"]
    precision = precision.lower()
    if precision not in valid_precisions:
        raise ValueError(f"Invalid precision: {precision}. Must be one of {valid_precisions}")
    return precision

def setup_environment() -> None:
    """Setup the environment for model quantization."""
    # Set PyTorch to use CUDA if available
    if check_gpu_availability():
        torch.backends.cudnn.benchmark = True
        console.print("[green]CUDA is available and enabled")
    else:
        console.print("[yellow]Warning: CUDA is not available. Using CPU only.")
    
    # Set environment variables for TensorRT
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Reduce TensorFlow logging
    if "CUDA_VISIBLE_DEVICES" not in os.environ:
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use first GPU by default 