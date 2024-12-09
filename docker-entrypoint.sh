#!/bin/bash
set -e

# Setup NVIDIA GPU environment
nvidia-smi

# Initialize environment variables
export NVIDIA_VISIBLE_DEVICES=${NVIDIA_VISIBLE_DEVICES:-all}
export MODEL_REPOSITORY=${MODEL_REPOSITORY:-/models}
export CATALOG_PATH=${CATALOG_PATH:-/models/catalog}
export MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-/mlflow}

# Create necessary directories
mkdir -p "$MODEL_REPOSITORY" "$CATALOG_PATH" "/mlflow"

# Check GPU availability
if ! command -v nvidia-smi &> /dev/null; then
    echo "WARNING: NVIDIA GPU is not available"
    export CUDA_VISIBLE_DEVICES=""
fi

# Initialize MLflow
mlflow server --backend-store-uri "$MLFLOW_TRACKING_URI" \
    --default-artifact-root "$MLFLOW_TRACKING_URI/artifacts" \
    --host 0.0.0.0 --port 5000 &

# Start Prometheus
/usr/local/bin/prometheus \
    --config.file=/app/prometheus/prometheus.yml \
    --storage.tsdb.path=/prometheus \
    --web.console.libraries=/usr/share/prometheus/console_libraries \
    --web.console.templates=/usr/share/prometheus/consoles &

# Start AlertManager
/usr/local/bin/alertmanager \
    --config.file=/app/alertmanager/alertmanager.yml \
    --storage.path=/alertmanager &

# Start OpenTelemetry collector
otelcol --config /app/otel-collector-config.yaml &

# Wait for services to start
sleep 5

# Execute the main command
exec "$@" 