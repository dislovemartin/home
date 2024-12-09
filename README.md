# SRT Model Quantizing

A powerful pipeline for downloading models from Hugging Face, quantizing them using NVIDIA NIM (Neural Interface Model), and uploading them to a Hugging Face-compatible repository.

## Features

- 🚀 Easy-to-use CLI interface
- 🔧 Support for FP16 and INT8 quantization
- 📦 Automatic model download from Hugging Face
- 💪 NVIDIA TensorRT optimization
- 🔄 Dynamic shape support
- 📊 Comprehensive monitoring and observability
- 🔐 Enterprise-grade security features
- 🎯 Designed for Linux servers

## Requirements

- Python 3.8+
- NVIDIA GPU with CUDA support
- NVIDIA drivers and CUDA toolkit installed
- Poetry for dependency management
- Docker and Docker Compose for containerized deployment

## Installation

1. Clone the repository:
```bash
git clone https://github.com/solidrust/srt-model-quantizing.git
cd srt-model-quantizing
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Activate the virtual environment:
```bash
poetry shell
```

4. Set up environment variables:
```bash
# Create .env file
cp .env.example .env

# Edit the .env file with your configuration
# Required for Slack notifications
SLACK_WEBHOOK_URL=your_slack_webhook_url
# Optional: Override default Grafana admin password
GRAFANA_ADMIN_PASSWORD=your_secure_password
```

## Usage

The tool provides a simple CLI interface for model quantization:

```bash
# Basic usage with default settings (FP16)
srt-quantize quantize bert-base-uncased

# Specify output directory and precision
srt-quantize quantize bert-base-uncased --output-dir ./my_models --precision fp16

# Use INT8 quantization with calibration data
srt-quantize quantize bert-base-uncased --precision int8 --calibration-data ./calibration_data

# Disable dynamic shapes
srt-quantize quantize bert-base-uncased --no-dynamic-shapes

# Set maximum batch size
srt-quantize quantize bert-base-uncased --max-batch-size 32

# Check version
srt-quantize version
```

## Monitoring and Observability

The project includes comprehensive monitoring and observability features:

### Metrics and Dashboards

- **Prometheus Integration**: Collects metrics from:
  - Model inference performance
  - GPU utilization and memory usage
  - System resources (CPU, memory, network)
  - Container metrics

- **Grafana Dashboards**: Pre-configured dashboards for:
  - Model performance metrics
  - Resource utilization
  - System health
  - Request patterns and latencies

### Alerting

- **Prometheus AlertManager**: Configured for:
  - High model latency alerts
  - Resource utilization thresholds
  - Error rate monitoring
  - System health checks

- **Slack Integration**: Real-time notifications for:
  - Critical alerts
  - Performance degradation
  - System events
  - Error conditions

### Accessing Monitoring Tools

```bash
# Start the monitoring stack
docker-compose up -d

# Access Grafana
open http://localhost:3000
# Default credentials: admin/admin (change on first login)

# Access Prometheus
open http://localhost:9090

# View AlertManager
open http://localhost:9093
```

## Configuration

The tool supports various configuration options:

- `model_name`: Name or path of the model to quantize (required)
- `output_dir`: Directory to save the quantized model (default: ./quantized_models)
- `precision`: Quantization precision (fp16 or int8, default: fp16)
- `max_batch_size`: Maximum batch size for inference (default: 1)
- `dynamic_shapes`: Enable/disable dynamic shapes (default: enabled)
- `calibration_data`: Path to calibration data for INT8 quantization (optional)

### Monitoring Configuration

- `prometheus.yml`: Prometheus scraping configuration
- `alertmanager.yml`: Alert rules and notification settings
- `grafana/dashboards/`: Custom Grafana dashboard definitions

## Hardware Compatibility

- NVIDIA GPUs with CUDA support
- Tested on various NVIDIA GPU architectures
- Requires appropriate NVIDIA drivers and CUDA toolkit

## Security Features

- Container security with no-new-privileges flag
- Non-root container execution
- Resource limits and quotas
- Network isolation
- Secure monitoring endpoints

## Development

To contribute to the project:

1. Fork the repository
2. Create a feature branch
3. Install development dependencies:
```bash
poetry install --with dev
```

4. Run tests:
```bash
poetry run pytest
```

5. Format code:
```bash
poetry run black .
poetry run isort .
```

6. Submit a pull request

## Troubleshooting

### Common Issues

1. **GPU Not Detected**
   - Verify NVIDIA drivers are installed and working
   - Check NVIDIA Docker runtime configuration
   - Ensure GPU is visible to containers

2. **Monitoring Issues**
   - Check if all containers are running: `docker-compose ps`
   - Verify Prometheus targets: http://localhost:9090/targets
   - Check AlertManager status: http://localhost:9093/#/status

3. **Performance Issues**
   - Monitor GPU utilization through Grafana dashboards
   - Check model inference latency metrics
   - Verify resource allocation in docker-compose.yml

## License

MIT License - see LICENSE file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Acknowledgments

- NVIDIA for TensorRT and NIM
- Hugging Face for their model hub and transformers library
- The PyTorch team for their excellent deep learning framework 