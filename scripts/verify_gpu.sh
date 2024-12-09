#!/bin/bash

set -e

echo "[INFO] Starting NVIDIA GPU verification..."

# Check NVIDIA driver installation
echo "[INFO] Checking NVIDIA driver installation..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "[ERROR] NVIDIA driver is not installed"
    exit 1
fi

nvidia-smi
if [ $? -ne 0 ]; then
    echo "[ERROR] NVIDIA driver is not functioning properly"
    exit 1
fi
echo "[INFO] NVIDIA driver is properly installed and functioning."

# Check NVIDIA Container Toolkit installation
echo "[INFO] Checking NVIDIA Container Toolkit..."
if ! dpkg -l | grep -q nvidia-container-toolkit; then
    echo "[ERROR] NVIDIA Container Toolkit is not installed"
    exit 1
fi
echo "[INFO] NVIDIA Container Toolkit is properly installed."

# Check Docker NVIDIA runtime
echo "[INFO] Checking Docker NVIDIA runtime..."
if ! docker info | grep -i "Default Runtime: nvidia" > /dev/null; then
    echo "[ERROR] Docker NVIDIA runtime is not set as default. Please configure Docker to use NVIDIA runtime."
    exit 1
fi

# Pull CUDA container image
echo "[INFO] Pulling CUDA test container..."
if ! docker pull nvidia/cuda:12.4.0-base-ubuntu22.04; then
    echo "[ERROR] Failed to pull CUDA test container"
    exit 1
fi

# Test NVIDIA runtime with container
echo "[INFO] Testing NVIDIA runtime with test container..."
if ! docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi; then
    echo "[ERROR] Failed to run NVIDIA test container"
    echo "[ERROR] Please check that the NVIDIA Container Toolkit is properly configured"
    echo "[ERROR] You may need to restart the Docker daemon after installing the NVIDIA Container Toolkit"
    exit 1
fi

echo "[INFO] GPU verification completed successfully"
exit 0 