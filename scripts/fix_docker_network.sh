#!/bin/bash

set -e

echo "[INFO] Fixing Docker network settings..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] This script must be run as root (use sudo)"
    exit 1
fi

# Create or update Docker daemon configuration
echo "[INFO] Updating Docker daemon configuration..."
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

# Load required kernel modules
echo "[INFO] Loading required kernel modules..."
modules=(
    "br_netfilter"
    "iptable_nat"
    "iptable_filter"
    "ip_tables"
)

for module in "${modules[@]}"; do
    if ! lsmod | grep -q "^$module"; then
        echo "[INFO] Loading module: $module"
        modprobe "$module" || echo "[WARN] Failed to load module: $module (may already be built into the kernel)"
    fi
done

# Configure sysctl parameters
echo "[INFO] Configuring sysctl parameters..."
cat > /etc/sysctl.d/99-docker-network.conf << EOF
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF

# Try to apply sysctl settings
if command -v sysctl >/dev/null 2>&1; then
    echo "[INFO] Applying sysctl settings..."
    sysctl -p /etc/sysctl.d/99-docker-network.conf || echo "[WARN] Could not apply sysctl settings (may require host system access)"
fi

echo "[INFO] Docker configuration has been updated"
echo "[INFO] To apply changes, you will need to restart the Docker daemon"
echo "[INFO] Please run one of the following commands based on your environment:"
echo "  1. In a standard environment: sudo systemctl restart docker"
echo "  2. In a container environment: sudo kill -SIGHUP \$(pidof dockerd)"
echo "  3. Or contact your system administrator to restart the Docker service"

# Try to detect environment and provide more specific instructions
if [ -f /.dockerenv ]; then
    echo "[INFO] Detected container environment"
    echo "[WARN] Docker daemon configuration cannot be restarted from within a container"
    echo "[INFO] Please apply these changes on the host system"
elif command -v systemctl >/dev/null 2>&1; then
    echo "[INFO] Detected systemd environment"
    echo "[INFO] You can restart Docker with: sudo systemctl restart docker"
else
    echo "[INFO] Detected non-systemd environment"
    echo "[INFO] You can restart Docker with: sudo kill -SIGHUP \$(pidof dockerd)"
fi

echo "[INFO] Configuration update completed" 