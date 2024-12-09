# SRT Model Quantizing

A comprehensive pipeline for downloading, quantizing, and managing AI models with support for both local and cloud deployments.

## Project Structure

```
.
├── infrastructure/
│   ├── kubernetes/        # Kubernetes configurations
│   │   ├── helm/         # Helm charts
│   │   ├── k3d-config.yaml
│   │   └── kind-config.yaml
│   ├── docker/           # Docker configurations
│   └── terraform/        # Cloud infrastructure as code
├── storage/
│   ├── models/          # Original models
│   ├── quantized/       # Quantized models
│   ├── cache/          # Temporary cache
│   └── temp/           # Temporary files
├── srt_model_quantizing/  # Main application code
├── scripts/              # Utility scripts
├── docs/                 # Documentation
└── tests/               # Test suite
```

## Prerequisites

- Python 3.8+
- Docker
- Kubernetes CLI (kubectl)
- Helm
- Either k3d or kind for local development
- Terraform (for cloud deployment)
- AWS CLI (for cloud deployment)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/srt-model-quantizing.git
   cd srt-model-quantizing
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Choose your deployment method:

   ### Local Development
   ```bash
   # Set environment
   export DEPLOY_ENV=local
   
   # Deploy
   ./scripts/deploy.sh
   ```

   ### Cloud Deployment (AWS)
   ```bash
   # Configure AWS credentials
   aws configure
   
   # Set environment
   export DEPLOY_ENV=cloud
   export AWS_REGION=us-west-2  # or your preferred region
   
   # Deploy
   ./scripts/deploy.sh
   ```

## Features

- Automated model downloading from Hugging Face
- Efficient model quantization
- Support for both NVIDIA CUDA and AMD ROCm GPUs
- Comprehensive monitoring and logging
- Scalable deployment options (local and cloud)
- Storage management and cleanup policies

## Configuration

- Environment variables can be set in `.env.local` or `.env.cloud`
- Kubernetes configurations are managed through Helm charts
- Infrastructure configurations are managed through Terraform

## Development

1. Set up local development environment:
   ```bash
   # Create local cluster
   k3d cluster create -c infrastructure/kubernetes/k3d-config.yaml
   
   # Deploy application
   DEPLOY_ENV=local ./scripts/deploy.sh
   ```

2. Access the application:
   - Web UI: http://localhost
   - API: http://localhost/api
   - Monitoring: http://localhost/grafana

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=srt_model_quantizing
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
