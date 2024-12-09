# 使用 NVIDIA 的 Triton Inference Server 作为基础镜像
FROM nvcr.io/nvidia/tritonserver:23.12-py3

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 并安装依赖
COPY requirements.txt ./

# 安装系统依赖和 Python 包，并清理缓存
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3-pip \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -U pip setuptools wheel \
    && pip install --no-cache-dir nvidia-pyindex \
    && pip install --no-cache-dir \
    nvidia-cuda-runtime-cu12 \
    nvidia-cublas-cu12 \
    nvidia-cudnn-cu12 \
    tritonclient[all] \
    tensorrt \
    && pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY srt_model_quantizing ./srt_model_quantizing
COPY README.md ./

# 复制 Prometheus 配置文件
COPY config/prometheus/prometheus.yml /etc/prometheus/prometheus.yml

# 创��目录并设置权限，同时创建 non-root 用户
RUN mkdir -p /models /quantized_models && \
    chmod -R 755 /models /quantized_models && \
    # 检查用户是否存在并创建
    if ! getent passwd triton > /dev/null 2>&1; then \
        useradd -m -u 2000 triton || { \
            echo "Failed to create user triton" >&2; \
            exit 1; \
        }; \
    fi && \
    chown -R triton:triton /app /models /quantized_models

# 切换到 non-root 用���
USER triton

# 设置环境变量
ENV NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    PYTHONUNBUFFERED=1 \
    MODEL_REPOSITORY=/models \
    PYTHONPATH=/app \
    PATH="/home/triton/.local/bin:$PATH"

# 创建卷挂载点
VOLUME ["/models", "/quantized_models"]

# 暴露端口
EXPOSE 8000 8001 8002

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v2/health/ready || exit 1

# 设置入口点和命令
ENTRYPOINT ["tritonserver"]
CMD ["--model-repository=/models", "--http-port=8000", "--grpc-port=8001", "--metrics-port=8002"]