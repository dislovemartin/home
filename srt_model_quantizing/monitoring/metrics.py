"""Prometheus metrics configuration for model and system monitoring."""

from prometheus_client import Counter, Gauge, Histogram, Summary

# Model metrics
MODEL_INFERENCE_TIME = Histogram(
    "model_inference_time_seconds",
    "Time spent processing inference requests",
    ["model_name", "precision"]
)

MODEL_INFERENCE_REQUESTS = Counter(
    "model_inference_requests_total",
    "Total number of inference requests",
    ["model_name", "precision", "status"]
)

MODEL_MEMORY_USAGE = Gauge(
    "model_memory_usage_bytes",
    "Memory usage by model",
    ["model_name", "precision"]
)

# GPU metrics
GPU_MEMORY_USAGE = Gauge(
    "gpu_memory_usage_bytes",
    "GPU memory usage",
    ["device_id"]
)

GPU_UTILIZATION = Gauge(
    "gpu_utilization_percent",
    "GPU utilization percentage",
    ["device_id"]
)

# Input data metrics
INPUT_VECTOR_NORM = Summary(
    "input_vector_norm",
    "L2 norm of input vectors",
    ["model_name"]
)

# System metrics
SYSTEM_MEMORY_USAGE = Gauge(
    "system_memory_usage_bytes",
    "System memory usage"
)

SYSTEM_CPU_USAGE = Gauge(
    "system_cpu_usage_percent",
    "System CPU usage percentage"
)

# Error metrics
ERROR_COUNTER = Counter(
    "errors_total",
    "Total number of errors",
    ["type", "model_name"]
)

def record_inference_time(model_name: str, precision: str, duration: float):
    """Record inference time for a model."""
    MODEL_INFERENCE_TIME.labels(model_name=model_name, precision=precision).observe(duration)

def increment_inference_requests(model_name: str, precision: str, status: str = "success"):
    """Increment the inference request counter."""
    MODEL_INFERENCE_REQUESTS.labels(
        model_name=model_name,
        precision=precision,
        status=status
    ).inc()

def update_model_memory_usage(model_name: str, precision: str, bytes_used: int):
    """Update memory usage for a model."""
    MODEL_MEMORY_USAGE.labels(model_name=model_name, precision=precision).set(bytes_used)

def update_gpu_metrics(device_id: int, memory_used: int, utilization: float):
    """Update GPU metrics."""
    GPU_MEMORY_USAGE.labels(device_id=str(device_id)).set(memory_used)
    GPU_UTILIZATION.labels(device_id=str(device_id)).set(utilization)

def record_input_norm(model_name: str, norm_value: float):
    """Record input vector norm."""
    INPUT_VECTOR_NORM.labels(model_name=model_name).observe(norm_value)

def update_system_metrics(memory_usage: int, cpu_usage: float):
    """Update system metrics."""
    SYSTEM_MEMORY_USAGE.set(memory_usage)
    SYSTEM_CPU_USAGE.set(cpu_usage)

def record_error(error_type: str, model_name: str):
    """Record an error occurrence."""
    ERROR_COUNTER.labels(type=error_type, model_name=model_name).inc() 