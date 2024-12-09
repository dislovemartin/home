#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Checking required dependencies..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install kubectl on different distributions
install_kubectl() {
    if command_exists apt-get; then
        echo "Installing kubectl using apt..."
        sudo apt-get update && sudo apt-get install -y apt-transport-https
        curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
        echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
        sudo apt-get update
        sudo apt-get install -y kubectl
    elif command_exists yum; then
        echo "Installing kubectl using yum..."
        cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOF
        sudo yum install -y kubectl
    else
        echo "Installing kubectl using direct download..."
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
        rm kubectl
    fi
}

# Function to install Helm
install_helm() {
    if command_exists apt-get; then
        echo "Installing Helm using apt..."
        curl https://baltocdn.com/helm/signing.asc | sudo apt-key add -
        echo "deb https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
        sudo apt-get update
        sudo apt-get install -y helm
    elif command_exists yum; then
        echo "Installing Helm using yum..."
        curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
        chmod 700 get_helm.sh
        ./get_helm.sh
        rm get_helm.sh
    else
        echo "Installing Helm using direct download..."
        curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
        chmod 700 get_helm.sh
        ./get_helm.sh
        rm get_helm.sh
    fi
}

# Check for required tools
MISSING_DEPS=0

# Check for kubectl
if ! command_exists kubectl; then
    echo -e "${YELLOW}kubectl is not installed${NC}"
    read -p "Would you like to install kubectl? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_kubectl
        if command_exists kubectl; then
            echo -e "${GREEN}kubectl installed successfully${NC}"
        else
            echo -e "${RED}Failed to install kubectl${NC}"
            MISSING_DEPS=1
        fi
    else
        MISSING_DEPS=1
    fi
else
    echo -e "${GREEN}kubectl is installed${NC}"
fi

# Check for helm
if ! command_exists helm; then
    echo -e "${YELLOW}Helm is not installed${NC}"
    read -p "Would you like to install Helm? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_helm
        if command_exists helm; then
            echo -e "${GREEN}Helm installed successfully${NC}"
        else
            echo -e "${RED}Failed to install Helm${NC}"
            MISSING_DEPS=1
        fi
    else
        MISSING_DEPS=1
    fi
else
    echo -e "${GREEN}Helm is installed${NC}"
fi

# Check for docker
if ! command_exists docker; then
    echo -e "${RED}Docker is not installed${NC}"
    echo "Please install Docker manually following the official documentation:"
    echo "https://docs.docker.com/engine/install/"
    MISSING_DEPS=1
else
    echo -e "${GREEN}Docker is installed${NC}"
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "${RED}Some required dependencies are missing. Please install them and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}All required dependencies are installed!${NC}"
exit 0 