#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
MAX_BACKUPS=5

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function to backup configuration
backup_config() {
    echo "Backing up configuration..."
    tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
        config/ \
        prometheus/ \
        alertmanager/ \
        grafana/provisioning/ \
        grafana/dashboards/ \
        otel-collector-config.yaml \
        docker-compose.yml
    echo "Configuration backup completed: config_$DATE.tar.gz"
}

# Function to backup data
backup_data() {
    echo "Backing up data..."
    
    # Stop services to ensure data consistency
    docker-compose stop
    
    tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" \
        /data/models \
        /data/catalog \
        /data/prometheus \
        /data/grafana \
        /data/mlflow
    
    # Restart services
    docker-compose start
    
    echo "Data backup completed: data_$DATE.tar.gz"
}

# Function to cleanup old backups
cleanup_old_backups() {
    local backup_type=$1
    echo "Cleaning up old $backup_type backups..."
    
    # List backups sorted by date, keep only the latest MAX_BACKUPS
    ls -t "$BACKUP_DIR/${backup_type}_"*.tar.gz 2>/dev/null | \
    tail -n +$((MAX_BACKUPS + 1)) | \
    xargs -r rm
    
    echo "Cleanup completed"
}

# Main backup logic
case "$1" in
    "config")
        backup_config
        cleanup_old_backups "config"
        ;;
    "data")
        backup_data
        cleanup_old_backups "data"
        ;;
    *)
        echo "Usage: $0 {config|data}"
        exit 1
        ;;
esac

# Verify backup
if [ -f "$BACKUP_DIR/${1}_$DATE.tar.gz" ]; then
    echo "Backup verification successful"
    echo "Backup size: $(du -h "$BACKUP_DIR/${1}_$DATE.tar.gz" | cut -f1)"
else
    echo "Backup verification failed"
    exit 1
fi

# Create backup manifest
cat > "$BACKUP_DIR/${1}_$DATE.manifest" << EOF
Backup Type: $1
Date: $(date)
Size: $(du -h "$BACKUP_DIR/${1}_$DATE.tar.gz" | cut -f1)
MD5: $(md5sum "$BACKUP_DIR/${1}_$DATE.tar.gz" | cut -d' ' -f1)
EOF

echo "Backup completed successfully" 