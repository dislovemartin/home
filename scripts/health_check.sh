#!/bin/bash
set -e

# Configuration
LOG_FILE="health_check.log"
MAX_RETRIES=5
RETRY_INTERVAL=10

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    local retries=0
    
    log "Checking $service_name health..."
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -f "$url" > /dev/null 2>&1; then
            log "$service_name is healthy"
            return 0
        else
            retries=$((retries + 1))
            if [ $retries -lt $MAX_RETRIES ]; then
                log "$service_name check failed, retrying in $RETRY_INTERVAL seconds..."
                sleep $RETRY_INTERVAL
            fi
        fi
    done
    
    log "$service_name health check failed after $MAX_RETRIES attempts"
    return 1
}

# Function to check GPU availability
check_gpu() {
    log "Checking GPU availability..."
    
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi > /dev/null 2>&1; then
            log "GPU is available and functioning"
            return 0
        else
            log "nvidia-smi command failed"
            return 1
        fi
    else
        log "nvidia-smi command not found"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    local threshold=90
    log "Checking disk space..."
    
    local usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -lt "$threshold" ]; then
        log "Disk space is adequate (${usage}% used)"
        return 0
    else
        log "Disk space usage is critical: ${usage}%"
        return 1
    fi
}

# Function to check memory usage
check_memory() {
    local threshold=90
    log "Checking memory usage..."
    
    local usage=$(free | awk '/Mem:/ {print int($3/$2 * 100)}')
    if [ "$usage" -lt "$threshold" ]; then
        log "Memory usage is adequate (${usage}% used)"
        return 0
    else
        log "Memory usage is critical: ${usage}%"
        return 1
    fi
}

# Main health check process
main() {
    log "Starting health check..."
    
    # Check system resources
    check_disk_space || exit 1
    check_memory || exit 1
    check_gpu || exit 1
    
    # Check services
    check_service "Frontend" "http://localhost:3000" || exit 1
    check_service "API" "http://localhost:8000/health" || exit 1
    check_service "Prometheus" "http://localhost:9090/-/healthy" || exit 1
    check_service "Grafana" "http://localhost:3001/api/health" || exit 1
    check_service "Jaeger" "http://localhost:16686" || exit 1
    
    # Check Docker containers
    log "Checking Docker containers..."
    if docker ps --format '{{.Names}} {{.Status}}' | grep -v "Up"; then
        log "Some containers are not running"
        exit 1
    fi
    
    log "All health checks passed successfully"
}

# Execute main function
main 