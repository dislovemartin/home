# Build stage
FROM nvcr.io/nvidia/pytorch:23.04-py3 as builder

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
WORKDIR /app
COPY pyproject.toml poetry.lock ./
COPY srt_model_quantizing ./srt_model_quantizing

# Build package
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root \
    && poetry build

# Runtime stage
FROM nvcr.io/nvidia/pytorch:23.04-py3

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install NVIDIA Container Toolkit
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Install MLflow
RUN pip install --no-cache-dir mlflow

# Copy built package from builder
COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Copy configuration files
COPY config /app/config
COPY prometheus /app/prometheus
COPY alertmanager /app/alertmanager
COPY otel-collector-config.yaml /app/

# Set environment variables
ENV MODEL_REPOSITORY=/models
ENV CATALOG_PATH=/models/catalog
ENV PYTHONUNBUFFERED=1
ENV NVIDIA_VISIBLE_DEVICES=all

# Create necessary directories
RUN mkdir -p /models /models/catalog /mlflow

# Set working directory
WORKDIR /app

# Expose ports
EXPOSE 8000 8001 8002 9090 9093 3000 16686 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["srt-serve", "--host", "0.0.0.0", "--port", "8000"]