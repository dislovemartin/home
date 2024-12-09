#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/backup"

# Function to list available backups
list_backups() {
    local backup_type=$1
    echo "Available $backup_type backups:"
    ls -lh "$BACKUP_DIR/${backup_type}_"*.tar.gz 2>/dev/null || echo "No backups found"
}

# Function to restore configuration
restore_config() {
    local backup_file=$1
    echo "Restoring configuration from $backup_file..."
    
    # Create temporary directory
    local temp_dir=$(mktemp -d)
    
    # Extract backup
    tar -xzf "$backup_file" -C "$temp_dir"
    
    # Copy files to their locations
    cp -r "$temp_dir"/config/* ./config/ 2>/dev/null || true
    cp -r "$temp_dir"/prometheus/* ./prometheus/ 2>/dev/null || true
    cp -r "$temp_dir"/alertmanager/* ./alertmanager/ 2>/dev/null || true
    cp -r "$temp_dir"/grafana/provisioning/* ./grafana/provisioning/ 2>/dev/null || true
    cp -r "$temp_dir"/grafana/dashboards/* ./grafana/dashboards/ 2>/dev/null || true
    cp "$temp_dir"/otel-collector-config.yaml . 2>/dev/null || true
    cp "$temp_dir"/docker-compose.yml . 2>/dev/null || true
    
    # Cleanup
    rm -rf "$temp_dir"
    
    echo "Configuration restore completed"
}

# Function to restore data
restore_data() {
    local backup_file=$1
    echo "Restoring data from $backup_file..."
    
    # Stop services
    docker-compose stop
    
    # Create temporary directory
    local temp_dir=$(mktemp -d)
    
    # Extract backup
    tar -xzf "$backup_file" -C "$temp_dir"
    
    # Restore data
    rsync -av --delete "$temp_dir"/data/models/ /data/models/
    rsync -av --delete "$temp_dir"/data/catalog/ /data/catalog/
    rsync -av --delete "$temp_dir"/data/prometheus/ /data/prometheus/
    rsync -av --delete "$temp_dir"/data/grafana/ /data/grafana/
    rsync -av --delete "$temp_dir"/data/mlflow/ /data/mlflow/
    
    # Cleanup
    rm -rf "$temp_dir"
    
    # Start services
    docker-compose up -d
    
    echo "Data restore completed"
}

# Function to verify backup integrity
verify_backup() {
    local backup_file=$1
    local manifest_file="${backup_file%.tar.gz}.manifest"
    
    if [ ! -f "$manifest_file" ]; then
        echo "Warning: Manifest file not found"
        return
    fi
    
    echo "Verifying backup integrity..."
    local stored_md5=$(grep "MD5:" "$manifest_file" | cut -d' ' -f2)
    local current_md5=$(md5sum "$backup_file" | cut -d' ' -f1)
    
    if [ "$stored_md5" != "$current_md5" ]; then
        echo "Error: Backup integrity check failed"
        exit 1
    fi
    
    echo "Backup integrity verified"
}

# Main restore logic
case "$1" in
    "list")
        case "$2" in
            "config")
                list_backups "config"
                ;;
            "data")
                list_backups "data"
                ;;
            *)
                echo "Usage: $0 list {config|data}"
                exit 1
                ;;
        esac
        ;;
    "restore")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 restore {config|data} <backup_file>"
            exit 1
        fi
        
        backup_file="$3"
        if [ ! -f "$backup_file" ]; then
            echo "Error: Backup file not found: $backup_file"
            exit 1
        fi
        
        verify_backup "$backup_file"
        
        case "$2" in
            "config")
                restore_config "$backup_file"
                ;;
            "data")
                restore_data "$backup_file"
                ;;
            *)
                echo "Usage: $0 restore {config|data} <backup_file>"
                exit 1
                ;;
        esac
        ;;
    *)
        echo "Usage: $0 {list|restore} {config|data} [backup_file]"
        exit 1
        ;;
esac

echo "Operation completed successfully" 