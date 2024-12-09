#!/bin/bash

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INFRASTRUCTURE_DIR="${PROJECT_ROOT}/infrastructure"
DEPLOY_ENV=${DEPLOY_ENV:-"local"}
KUBE_CONTEXT=${KUBE_CONTEXT:-""}
ENABLE_GPU=${ENABLE_GPU:-"true"}

# Source environment variables
if [ -f "${PROJECT_ROOT}/.env.${DEPLOY_ENV}" ]; then
    source "${PROJECT_ROOT}/.env.${DEPLOY_ENV}"
fi

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

check_dependencies() {
    log "Checking dependencies..."
    
    # Check required tools
    command -v kubectl >/dev/null 2>&1 || error "kubectl is required but not installed"
    command -v helm >/dev/null 2>&1 || error "helm is required but not installed"
    
    if [ "${DEPLOY_ENV}" = "cloud" ]; then
        command -v terraform >/dev/null 2>&1 || error "terraform is required but not installed"
        command -v aws >/dev/null 2>&1 || error "aws CLI is required but not installed"
    fi
    
    if [ "${ENABLE_GPU}" = "true" ]; then
        log "Verifying NVIDIA GPU setup..."
        bash "${SCRIPT_DIR}/verify_gpu.sh" || error "GPU verification failed"
    fi
}

setup_local_cluster() {
    log "Setting up local Kubernetes cluster..."
    
    if [ -z "$(kubectl config current-context 2>/dev/null)" ]; then
        log "No Kubernetes context found. Creating local cluster..."
        if command -v k3d >/dev/null 2>&1; then
            k3d cluster create srt-cluster --config "${INFRASTRUCTURE_DIR}/kubernetes/k3d-config.yaml"
        elif command -v kind >/dev/null 2>&1; then
            kind create cluster --config "${INFRASTRUCTURE_DIR}/kubernetes/kind-config.yaml"
        else
            error "Neither k3d nor kind is installed. Please install one of them."
        fi
    fi
    
    if [ "${ENABLE_GPU}" = "true" ]; then
        log "Setting up NVIDIA device plugin..."
        kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.1/nvidia-device-plugin.yml
        kubectl rollout status daemonset/nvidia-device-plugin-daemonset -n kube-system --timeout=60s || \
            error "Failed to deploy NVIDIA device plugin"
    fi
}

setup_cloud_infrastructure() {
    log "Setting up cloud infrastructure..."
    
    cd "${INFRASTRUCTURE_DIR}/terraform"
    
    # Initialize Terraform
    terraform init
    
    # Plan and apply infrastructure changes
    terraform plan -out=tfplan
    terraform apply tfplan
    
    # Update kubeconfig for EKS
    aws eks update-kubeconfig --name $(terraform output -raw eks_cluster_name) --region ${AWS_REGION}
    
    if [ "${ENABLE_GPU}" = "true" ]; then
        log "Setting up NVIDIA device plugin in EKS..."
        kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.1/nvidia-device-plugin.yml
        kubectl rollout status daemonset/nvidia-device-plugin-daemonset -n kube-system --timeout=60s || \
            error "Failed to deploy NVIDIA device plugin"
    fi
}

deploy_application() {
    log "Deploying application..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace srt-model-quantizing --dry-run=client -o yaml | kubectl apply -f -
    
    # Set GPU values for Helm
    GPU_VALUES=""
    if [ "${ENABLE_GPU}" = "true" ]; then
        GPU_VALUES="--set global.nvidia.enabled=true"
    fi
    
    # Deploy with Helm
    helm upgrade --install srt-model-quantizing \
        "${INFRASTRUCTURE_DIR}/kubernetes/helm/srt-model-quantizing" \
        --namespace srt-model-quantizing \
        --values "${INFRASTRUCTURE_DIR}/kubernetes/helm/srt-model-quantizing/values-${DEPLOY_ENV}.yaml" \
        ${GPU_VALUES} \
        --wait
    
    # Verify GPU access if enabled
    if [ "${ENABLE_GPU}" = "true" ]; then
        log "Verifying GPU access in deployed pods..."
        kubectl wait --for=condition=ready pod -l app=srt-model-quantizing -n srt-model-quantizing --timeout=120s || \
            error "Pods failed to become ready"
        
        # Check GPU access in a pod
        POD_NAME=$(kubectl get pod -l app=srt-model-quantizing -n srt-model-quantizing -o jsonpath='{.items[0].metadata.name}')
        kubectl exec -n srt-model-quantizing ${POD_NAME} -- nvidia-smi || \
            error "Failed to access GPU in deployed pod"
    fi
}

main() {
    log "Starting deployment for environment: ${DEPLOY_ENV}"
    
    # Check dependencies
    check_dependencies
    
    # Setup infrastructure based on environment
    if [ "${DEPLOY_ENV}" = "local" ]; then
        setup_local_cluster
    elif [ "${DEPLOY_ENV}" = "cloud" ]; then
        setup_cloud_infrastructure
    else
        error "Invalid DEPLOY_ENV. Must be 'local' or 'cloud'"
    fi
    
    # Deploy application
    deploy_application
    
    log "Deployment completed successfully!"
    
    if [ "${ENABLE_GPU}" = "true" ]; then
        log "GPU support is enabled and verified"
        kubectl get nodes -o custom-columns=NAME:.metadata.name,GPU:.status.allocatable.nvidia\\.com/gpu
    fi
}

# Execute main function
main "$@" 