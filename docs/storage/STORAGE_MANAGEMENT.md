# Storage Management

## Overview

The storage management system provides comprehensive monitoring, metrics collection, and automated cleanup for model storage. It ensures efficient use of storage resources and maintains optimal performance.

## Directory Structure

```
storage/
├── models/                 # Model storage
│   ├── raw/               # Original downloaded models
│   ├── quantized/         # Optimized and quantized models
│   └── repository/        # Production-ready model repository
├── grafana/               # Grafana persistent data
│   ├── dashboards/        # Custom dashboards
│   └── data/             # Time series data
└── metrics/               # Prometheus metrics storage
    ├── wal/              # Write-ahead log
    └── chunks/           # TSDB chunks
```

## Monitoring Features

### Storage Metrics
- Real-time storage usage tracking
- Model count monitoring
- Directory-specific metrics
- Total storage capacity monitoring

### Grafana Dashboard
The storage metrics dashboard provides:
- Storage usage trends
- Model distribution visualization
- Capacity utilization gauges
- Model count statistics

### Prometheus Alerts
Configured alerts for:
- Critical storage space usage (>90%)
- High storage space usage (>75%)
- Storage imbalance between directories
- Unused model detection
- Rapid storage growth detection

## Cleanup Policies

### Age-Based Cleanup
- Removes models older than a specified age
- Default: 30 days retention
- Configurable through settings

### Usage-Based Cleanup
- Removes models with low usage
- Considers request count over time
- Default: <10 requests in 7 days
- Configurable thresholds

### Size-Based Cleanup
- Maintains storage below size threshold
- Removes largest unused models first
- Default: 10GB total limit
- Configurable size limits

## API Endpoints

### Storage Information
```http
GET /storage/info
```
Returns current storage metrics and statistics.

### Manual Metrics Collection
```http
POST /storage/collect
```
Triggers immediate metrics collection.

### Storage Cleanup
```http
POST /storage/cleanup
Query Parameters:
  - dry_run: boolean (optional, default: false)
```
Executes cleanup policies. Use `dry_run=true` to preview changes.

### List Cleanup Policies
```http
GET /storage/cleanup/policies
```
Lists configured cleanup policies and their settings.

## Configuration

### Environment Variables
```yaml
STORAGE_BASE_PATH: "./storage"
STORAGE_MODELS_PATH: "./storage/models"
STORAGE_METRICS_PATH: "./storage/metrics"
STORAGE_GRAFANA_PATH: "./storage/grafana"
STORAGE_MAX_SIZE_GB: 100
STORAGE_CLEANUP_AGE_DAYS: 30
STORAGE_MIN_REQUESTS: 10
STORAGE_REQUEST_TIMEFRAME_DAYS: 7
```

### Development Configuration
```yaml
storage:
  base_path: "./storage"
  models:
    path: "./storage/models"
    raw_dir: "raw"
    quantized_dir: "quantized"
    repository_dir: "repository"
  metrics:
    path: "./storage/metrics"
  grafana:
    path: "./storage/grafana"
```

## Best Practices

### Storage Organization
1. Keep models in appropriate directories
2. Use consistent naming conventions
3. Maintain clean directory structure
4. Regular cleanup execution

### Monitoring
1. Regular metric collection
2. Alert threshold adjustment
3. Dashboard monitoring
4. Usage pattern analysis

### Cleanup
1. Regular policy review
2. Threshold adjustment
3. Backup before cleanup
4. Dry run verification

## Troubleshooting

### Common Issues
1. **Storage Full**
   - Run manual cleanup
   - Adjust cleanup thresholds
   - Review large models

2. **Missing Metrics**
   - Check collector service
   - Verify permissions
   - Review logs

3. **Failed Cleanup**
   - Check permissions
   - Verify file locks
   - Review error logs

### Logging
All storage operations are logged with:
- Operation type
- Timestamp
- Success/failure status
- Error details if applicable

## Security

### Access Control
- Admin-only cleanup operations
- Read-only metrics access
- Audit logging of operations

### Data Protection
- Backup before cleanup
- Verification steps
- Rollback capabilities 