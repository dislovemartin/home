"""Profiling utilities for performance monitoring."""

import cProfile
import functools
import io
import pstats
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

import torch
from torch.profiler import ProfilerActivity, profile, record_function

def timeit(func: Callable) -> Callable:
    """Decorator to measure function execution time.
    
    Args:
        func: Function to measure
    
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper

@contextmanager
def timer(name: str):
    """Context manager for timing code blocks.
    
    Args:
        name: Name of the code block
    """
    start_time = time.perf_counter()
    yield
    end_time = time.perf_counter()
    print(f"{name} took {end_time - start_time:.4f} seconds")

def profile_function(func: Callable) -> Callable:
    """Decorator to profile function execution.
    
    Args:
        func: Function to profile
    
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        ps.print_stats()
        print(s.getvalue())
        return result
    return wrapper

@contextmanager
def torch_profile(
    activities: Optional[list] = None,
    record_shapes: bool = True,
    profile_memory: bool = True,
    with_stack: bool = True
):
    """Context manager for PyTorch profiling.
    
    Args:
        activities: List of activities to profile
        record_shapes: Whether to record tensor shapes
        profile_memory: Whether to profile memory usage
        with_stack: Whether to record stack traces
    """
    if activities is None:
        activities = [
            ProfilerActivity.CPU,
            ProfilerActivity.CUDA if torch.cuda.is_available() else None
        ]
    activities = [a for a in activities if a is not None]
    
    with profile(
        activities=activities,
        record_shapes=record_shapes,
        profile_memory=profile_memory,
        with_stack=with_stack
    ) as prof:
        yield prof

def measure_inference_latency(
    model: torch.nn.Module,
    input_tensors: Dict[str, torch.Tensor],
    num_iterations: int = 100,
    warmup_iterations: int = 10
) -> Dict[str, float]:
    """Measure model inference latency.
    
    Args:
        model: PyTorch model
        input_tensors: Dictionary of input tensors
        num_iterations: Number of iterations to measure
        warmup_iterations: Number of warmup iterations
    
    Returns:
        Dictionary containing latency statistics
    """
    model.eval()
    if torch.cuda.is_available():
        model.cuda()
        input_tensors = {k: v.cuda() for k, v in input_tensors.items()}
    
    # Warmup
    with torch.no_grad():
        for _ in range(warmup_iterations):
            model(**input_tensors)
    
    # Measure latency
    latencies = []
    with torch.no_grad():
        for _ in range(num_iterations):
            start_time = time.perf_counter()
            model(**input_tensors)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            end_time = time.perf_counter()
            latencies.append((end_time - start_time) * 1000)  # Convert to ms
    
    return {
        "mean": sum(latencies) / len(latencies),
        "min": min(latencies),
        "max": max(latencies),
        "p50": sorted(latencies)[len(latencies) // 2],
        "p90": sorted(latencies)[int(len(latencies) * 0.9)],
        "p95": sorted(latencies)[int(len(latencies) * 0.95)],
        "p99": sorted(latencies)[int(len(latencies) * 0.99)]
    }

def measure_memory_usage(func: Callable) -> Callable:
    """Decorator to measure peak memory usage.
    
    Args:
        func: Function to measure
    
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.empty_cache()
        
        result = func(*args, **kwargs)
        
        if torch.cuda.is_available():
            peak_memory = torch.cuda.max_memory_allocated() / (1024 * 1024)  # MB
            print(f"Peak GPU memory usage: {peak_memory:.2f} MB")
        
        return result
    return wrapper

def profile_model(
    model: torch.nn.Module,
    input_tensors: Dict[str, torch.Tensor],
    num_iterations: int = 10
) -> None:
    """Profile model execution.
    
    Args:
        model: PyTorch model
        input_tensors: Dictionary of input tensors
        num_iterations: Number of iterations to profile
    """
    model.eval()
    if torch.cuda.is_available():
        model.cuda()
        input_tensors = {k: v.cuda() for k, v in input_tensors.items()}
    
    with torch_profile() as prof:
        with record_function("model_inference"):
            for _ in range(num_iterations):
                with torch.no_grad():
                    model(**input_tensors)
    
    print(prof.key_averages().table(
        sort_by="cuda_time_total" if torch.cuda.is_available() else "cpu_time_total",
        row_limit=10
    )) 