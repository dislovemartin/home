# NVIDIA Optimization Guide

## Hardware Requirements

- NVIDIA GPU with Compute Capability 7.0 or higher
- Recommended GPUs:
  - NVIDIA A100
  - NVIDIA H100
  - NVIDIA V100
  - NVIDIA T4
  - NVIDIA RTX 3090/4090 (for development)

## Software Requirements

- NVIDIA Driver: >= 525.60.13
- CUDA Toolkit: >= 11.8
- cuDNN: >= 8.6
- TensorRT: >= 8.6.1
- NVIDIA Container Toolkit

## Model Optimization Techniques

### 1. Precision Optimization

#### FP16 Mixed Precision
```python
from srt_model_quantizing.nemo import ModelOptimizer

optimizer = ModelOptimizer(
    model_path="bert-base-uncased",
    config=OptimizationConfig(
        precision="fp16",
        use_transformer_engine=True
    )
)
```

#### INT8 Quantization
```python
optimizer = ModelOptimizer(
    model_path="bert-base-uncased",
    config=OptimizationConfig(
        precision="int8",
        calibration_data="path/to/calibration/data"
    )
)
```

#### FP8 Hybrid Mode (H100 Only)
```python
optimizer = ModelOptimizer(
    model_path="bert-base-uncased",
    config=OptimizationConfig(
        precision="fp8",
        fp8_hybrid=True,
        use_transformer_engine=True
    )
)
```

### 2. NVIDIA Transformer Engine

The NVIDIA Transformer Engine provides optimized kernels for transformer models:

- Automatic precision selection
- Optimized attention mechanisms
- Efficient memory management
- Hardware-specific optimizations

Enable it in your configuration:
```python
config = OptimizationConfig(
    use_transformer_engine=True,
    transformer_engine_config={
        "tp_size": 1,  # Tensor Parallelism
        "pp_size": 1,  # Pipeline Parallelism
        "precision": "fp16"
    }
)
```

### 3. Multi-GPU Training

#### Data Parallel Training
```python
config = OptimizationConfig(
    device_ids=[0, 1, 2, 3],
    distributed_strategy="ddp"
)
```

#### Model Parallel Training (Large Models)
```python
config = OptimizationConfig(
    device_ids=[0, 1, 2, 3],
    distributed_strategy="model_parallel",
    tp_size=2,  # Tensor Parallelism
    pp_size=2   # Pipeline Parallelism
)
```

### 4. Memory Optimization

#### Gradient Checkpointing
```python
config = OptimizationConfig(
    gradient_checkpointing=True,
    checkpoint_every_n_layers=2
)
```

#### Activation Recomputation
```python
config = OptimizationConfig(
    activation_recomputation=True,
    recompute_granularity="selective"
)
```

## Performance Monitoring

### 1. GPU Metrics

Monitor GPU utilization and memory:
```python
from srt_model_quantizing.utils.gpu import get_gpu_info

gpu_info = get_gpu_info()
print(f"GPU Utilization: {gpu_info['devices'][0]['utilization']}%")
print(f"Memory Usage: {gpu_info['devices'][0]['memory_used']} MB")
```

### 2. Inference Latency

Profile model inference:
```python
from srt_model_quantizing.utils.profiling import measure_inference_latency

latency_stats = measure_inference_latency(
    model=optimized_model,
    input_tensors=sample_inputs,
    num_iterations=100,
    warmup_iterations=10
)
print(f"Average Latency: {latency_stats['mean']:.2f} ms")
print(f"P95 Latency: {latency_stats['p95']:.2f} ms")
```

### 3. Prometheus Metrics

NVIDIA DCGM metrics are automatically collected:
- GPU utilization
- Memory usage
- Power consumption
- Temperature
- PCIe throughput

## Container Deployment

### 1. Base Image Selection

Use NVIDIA optimized containers:
```dockerfile
# For PyTorch
FROM nvcr.io/nvidia/pytorch:23.04-py3

# For TensorRT
FROM nvcr.io/nvidia/tensorrt:23.04-py3

# For Triton Inference Server
FROM nvcr.io/nvidia/tritonserver:23.04-py3
```

### 2. Runtime Configuration

Enable NVIDIA Container Runtime in docker-compose.yml:
```yaml
services:
  app:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### 3. Multi-GPU Support

Configure multiple GPUs:
```yaml
services:
  app:
    environment:
      - NVIDIA_VISIBLE_DEVICES=0,1,2,3
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 4
              capabilities: [gpu]
```

## Best Practices

1. **Memory Management**
   - Use gradient checkpointing for large models
   - Enable activation recomputation
   - Monitor memory usage with NVIDIA tools

2. **Performance Optimization**
   - Profile models with NVIDIA NSight
   - Use TensorRT for inference
   - Enable Transformer Engine optimizations

3. **Multi-GPU Deployment**
   - Use appropriate distributed strategy
   - Balance GPU memory usage
   - Monitor inter-GPU communication

4. **Production Deployment**
   - Use NVIDIA Triton Inference Server
   - Enable dynamic batching
   - Implement proper error handling

5. **Monitoring and Logging**
   - Use NVIDIA DCGM for metrics
   - Monitor GPU health
   - Track performance metrics

## Troubleshooting

### Common Issues

1. **Out of Memory (OOM)**
   - Enable gradient checkpointing
   - Reduce batch size
   - Use model parallelism

2. **Poor Performance**
   - Check GPU utilization
   - Verify CUDA version compatibility
   - Profile with NVIDIA tools

3. **Multi-GPU Issues**
   - Check NVLink connectivity
   - Verify NCCL configuration
   - Monitor GPU affinity

### Debugging Tools

1. **NVIDIA NSight Systems**
   ```bash
   nsys profile python your_script.py
   ```

2. **NVIDIA DCGM**
   ```bash
   dcgmi discovery -l
   dcgmi dmon
   ```

3. **NVIDIA SMI**
   ```bash
   nvidia-smi topo -m
   nvidia-smi dmon
   