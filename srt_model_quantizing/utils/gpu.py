"""GPU utilities for monitoring and management."""

import os
from typing import Dict, List, Optional

import torch
from pynvml import (NVMLError, nvmlDeviceGetCount, nvmlDeviceGetHandleByIndex,
                   nvmlDeviceGetMemoryInfo, nvmlDeviceGetName,
                   nvmlDeviceGetTemperature, nvmlInit, nvmlShutdown)

def get_gpu_info() -> Dict:
    """Get GPU information.
    
    Returns:
        Dictionary containing GPU information:
        - available: Whether GPUs are available
        - count: Number of GPUs
        - devices: List of device information
    """
    try:
        nvmlInit()
        
        device_count = nvmlDeviceGetCount()
        devices = []
        
        for i in range(device_count):
            handle = nvmlDeviceGetHandleByIndex(i)
            name = nvmlDeviceGetName(handle)
            memory = nvmlDeviceGetMemoryInfo(handle)
            temperature = nvmlDeviceGetTemperature(handle, 0)
            
            devices.append({
                "index": i,
                "name": name,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_free": memory.free,
                "temperature": temperature,
                "compute_capability": torch.cuda.get_device_capability(i)
            })
        
        return {
            "available": True,
            "count": device_count,
            "devices": devices
        }
    
    except NVMLError:
        return {
            "available": False,
            "count": 0,
            "devices": []
        }
    finally:
        try:
            nvmlShutdown()
        except:
            pass

def get_available_gpus() -> List[int]:
    """Get list of available GPU indices.
    
    Returns:
        List of available GPU indices
    """
    if not torch.cuda.is_available():
        return []
    
    return list(range(torch.cuda.device_count()))

def get_gpu_memory_usage(device_id: Optional[int] = None) -> Dict[int, Dict[str, int]]:
    """Get GPU memory usage.
    
    Args:
        device_id: Specific GPU device ID to check, or None for all devices
    
    Returns:
        Dictionary mapping device IDs to memory usage information
    """
    try:
        nvmlInit()
        
        if device_id is not None:
            devices = [device_id]
        else:
            devices = range(nvmlDeviceGetCount())
        
        memory_info = {}
        for i in devices:
            handle = nvmlDeviceGetHandleByIndex(i)
            memory = nvmlDeviceGetMemoryInfo(handle)
            
            memory_info[i] = {
                "total": memory.total,
                "used": memory.used,
                "free": memory.free
            }
        
        return memory_info
    
    except NVMLError:
        return {}
    finally:
        try:
            nvmlShutdown()
        except:
            pass

def set_gpu_memory_growth():
    """Configure GPU memory growth to avoid allocating all memory at once."""
    if torch.cuda.is_available():
        for device in range(torch.cuda.device_count()):
            torch.cuda.set_per_process_memory_fraction(0.9, device)

def select_gpu(required_memory_mb: int = 0) -> Optional[int]:
    """Select the best available GPU based on memory usage.
    
    Args:
        required_memory_mb: Minimum required free memory in MB
    
    Returns:
        Selected GPU index or None if no suitable GPU is found
    """
    if not torch.cuda.is_available():
        return None
    
    try:
        nvmlInit()
        
        best_gpu = None
        max_free_memory = 0
        
        for i in range(nvmlDeviceGetCount()):
            handle = nvmlDeviceGetHandleByIndex(i)
            memory = nvmlDeviceGetMemoryInfo(handle)
            free_memory = memory.free / (1024 * 1024)  # Convert to MB
            
            if free_memory > max_free_memory and free_memory >= required_memory_mb:
                best_gpu = i
                max_free_memory = free_memory
        
        return best_gpu
    
    except NVMLError:
        return None
    finally:
        try:
            nvmlShutdown()
        except:
            pass

def get_optimal_batch_size(
    model_size_mb: int,
    input_size_mb: int,
    output_size_mb: int,
    device_id: Optional[int] = None
) -> int:
    """Calculate optimal batch size based on available GPU memory.
    
    Args:
        model_size_mb: Model size in MB
        input_size_mb: Size of one input sample in MB
        output_size_mb: Size of one output sample in MB
        device_id: Specific GPU device ID to use
    
    Returns:
        Optimal batch size
    """
    if not torch.cuda.is_available():
        return 1
    
    try:
        nvmlInit()
        
        if device_id is None:
            device_id = select_gpu() or 0
        
        handle = nvmlDeviceGetHandleByIndex(device_id)
        memory = nvmlDeviceGetMemoryInfo(handle)
        
        # Calculate available memory (80% of free memory)
        available_mb = (memory.free * 0.8) / (1024 * 1024)
        
        # Calculate memory needed per sample
        memory_per_sample = input_size_mb + output_size_mb
        
        # Calculate maximum batch size
        max_batch_size = int((available_mb - model_size_mb) / memory_per_sample)
        
        # Ensure batch size is at least 1
        return max(1, max_batch_size)
    
    except NVMLError:
        return 1
    finally:
        try:
            nvmlShutdown()
        except:
            pass 