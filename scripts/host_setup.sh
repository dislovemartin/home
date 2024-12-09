#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Functions
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if running on host system
if [ -f /.dockerenv ]; then
    error "This script must be run on the host system, not inside a container"
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root (use sudo)"
fi

# Install required packages
log "Installing required packages..."
if command -v apt-get >/dev/null 2>&1; then
    apt-get update
    apt-get install -y \
        kmod \
        nvidia-container-toolkit \
        nvidia-container-runtime
elif command -v yum >/dev/null 2>&1; then
    yum install -y \
        kmod \
        nvidia-container-toolkit \
        nvidia-container-runtime
else
    error "Unsupported package manager. Please install required packages manually"
fi

# Load required kernel modules
log "Loading required kernel modules..."
modules=(
    "br_netfilter"
    "iptable_nat"
    "iptable_filter"
    "ip_tables"
)

for module in "${modules[@]}"; do
    if ! lsmod | grep -q "^$module"; then
        log "Loading module: $module"
        modprobe "$module" || warn "Failed to load module: $module (may already be built into the kernel)"
    fi
done

# Configure sysctl parameters
log "Configuring sysctl parameters..."
mkdir -p /etc/sysctl.d
cat > /etc/sysctl.d/99-docker-network.conf << EOF
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF

# Apply sysctl settings
log "Applying sysctl settings..."
sysctl -p /etc/sysctl.d/99-docker-network.conf

# Configure Docker daemon
log "Configuring Docker daemon..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << EOF
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "bridge": "docker0",
    "iptables": true,
    "ip-forward": true,
    "ip-masq": true,
    "userland-proxy": true,
    "live-restore": true,
    "default-address-pools": [
        {
            "base": "172.17.0.0/16",
            "size": 24
        }
    ],
    "mtu": 1500,
    "dns": ["8.8.8.8", "8.8.4.4"],
    "dns-search": [],
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
EOF

# Restart Docker daemon
log "Restarting Docker daemon..."
if command -v systemctl >/dev/null 2>&1; then
    systemctl restart docker
else
    service docker restart || {
        warn "Could not restart Docker automatically"
        log "Please restart Docker manually using one of these commands:"
        echo "  1. sudo systemctl restart docker"
        echo "  2. sudo service docker restart"
        echo "  3. sudo kill -SIGHUP \$(pidof dockerd)"
    }
fi

# Verify NVIDIA GPU access
log "Verifying NVIDIA GPU access..."
if ! command -v nvidia-smi >/dev/null 2>&1; then
    warn "nvidia-smi not found. Please ensure NVIDIA drivers are installed"
else
    nvidia-smi || warn "Could not access NVIDIA GPU. Please check driver installation"
fi

# Test Docker NVIDIA runtime
log "Testing Docker NVIDIA runtime..."
if ! docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi; then
    warn "Failed to run NVIDIA test container"
    log "Please ensure NVIDIA Container Toolkit is properly installed"
else
    log "NVIDIA GPU is working properly with Docker"
fi

log "Setup completed successfully"
log "You can now run GPU-enabled containers" 