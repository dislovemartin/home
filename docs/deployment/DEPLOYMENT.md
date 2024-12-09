# Deployment Guide

## Overview

This guide covers the deployment process for the SRT Model Quantizing platform, including production setup, scaling considerations, and maintenance procedures.

## Prerequisites

- Linux server with Docker and Docker Compose installed
- NVIDIA GPU with CUDA support
- Minimum 32GB RAM
- At least 500GB storage
- Python 3.10+
- Node.js 18+ (for frontend builds)

## Deployment Methods

### 1. Docker Compose Deployment (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/solidrust/srt-model-quantizing.git
   cd srt-model-quantizing
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Build and start services:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. Verify deployment:
   ```bash
   ./scripts/health_check.sh
   ```

### 2. Kubernetes Deployment

1. Apply Kubernetes manifests:
   ```bash
   kubectl apply -f k8s/
   ```

2. Verify deployment:
   ```bash
   kubectl get pods -n srt-model-quantizing
   ```

## Configuration

### Production Environment

1. Update production configuration:
   ```yaml
   # config/prod/settings.yaml
   storage:
     base_path: "/data/storage"
     models:
       path: "/data/storage/models"
     metrics:
       path: "/data/storage/metrics"
     grafana:
       path: "/data/storage/grafana"

   security:
     jwt_secret: "<your-secret>"
     allowed_origins: ["https://your-domain.com"]

   monitoring:
     log_level: "INFO"
     metrics_enabled: true
     tracing_enabled: true
   ```

2. Configure SSL/TLS:
   ```nginx
   # nginx/prod.conf
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /etc/nginx/certs/cert.pem;
       ssl_certificate_key /etc/nginx/certs/key.pem;
       
       # ... rest of configuration
   }
   ```

### Scaling Configuration

1. Horizontal scaling:
   ```yaml
   # docker-compose.prod.yml
   services:
     api:
       deploy:
         replicas: 3
         resources:
           limits:
             cpus: '2'
             memory: 8G
   ```

2. Load balancer setup:
   ```nginx
   # nginx/load-balancer.conf
   upstream api_servers {
       server api1:8000;
       server api2:8000;
       server api3:8000;
   }
   ```

## Monitoring Setup

1. Configure Prometheus alerts:
   ```yaml
   # prometheus/rules/prod-alerts.yml
   groups:
     - name: production_alerts
       rules:
         - alert: HighErrorRate
           expr: rate(http_requests_total{status=~"5.."}[5m]) > 1
           for: 5m
           labels:
             severity: critical
   ```

2. Set up Grafana dashboards:
   ```bash
   cp grafana/dashboards/* /data/storage/grafana/dashboards/
   ```

3. Configure alert notifications:
   ```yaml
   # alertmanager/prod.yml
   receivers:
     - name: 'team-notifications'
       slack_configs:
         - channel: '#prod-alerts'
           api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
   ```

## Backup and Recovery

1. Configure automated backups:
   ```bash
   # Add to crontab
   0 2 * * * /opt/srt-model-quantizing/scripts/backup.sh data
   0 3 * * 0 /opt/srt-model-quantizing/scripts/backup.sh config
   ```

2. Backup verification:
   ```bash
   ./scripts/verify_backup.sh /path/to/backup
   ```

3. Recovery procedure:
   ```bash
   ./scripts/restore.sh /path/to/backup
   ```

## Security Measures

1. Enable security features:
   ```yaml
   # config/prod/security.yaml
   security:
     enable_2fa: true
     rate_limiting: true
     ip_whitelist: ["10.0.0.0/8"]
     audit_logging: true
   ```

2. Set up firewall rules:
   ```bash
   # Example UFW configuration
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw allow from 10.0.0.0/8 to any port 8000
   ```

## Maintenance Procedures

### Regular Maintenance

1. Log rotation:
   ```bash
   # /etc/logrotate.d/srt-model-quantizing
   /var/log/srt-model-quantizing/*.log {
       daily
       rotate 14
       compress
       delaycompress
       notifempty
       create 0640 srt-user srt-group
   }
   ```

2. Storage cleanup:
   ```bash
   # Add to crontab
   0 1 * * * /opt/srt-model-quantizing/scripts/storage_cleanup.sh
   ```

### Updates and Upgrades

1. Update procedure:
   ```bash
   # Stop services
   docker-compose -f docker-compose.prod.yml down

   # Pull updates
   git pull origin main

   # Rebuild and restart
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

2. Database migrations:
   ```bash
   ./scripts/migrate.sh
   ```

## Troubleshooting

### Common Issues

1. GPU Issues:
   ```bash
   # Check GPU status
   nvidia-smi
   # Check CUDA version
   nvcc --version
   ```

2. Storage Issues:
   ```bash
   # Check disk usage
   df -h
   # Clean up old data
   ./scripts/cleanup.sh
   ```

3. Performance Issues:
   ```bash
   # Check system resources
   htop
   # Monitor GPU usage
   nvidia-smi -l 1
   ```

### Health Checks

1. Service health:
   ```bash
   ./scripts/health_check.sh
   ```

2. Model serving:
   ```bash
   curl -f http://localhost:8000/health
   ```

3. Metrics collection:
   ```bash
   curl -f http://localhost:9090/-/healthy
   ```

## Rollback Procedures

1. Service rollback:
   ```bash
   # Revert to previous version
   git checkout <previous-tag>
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

2. Data rollback:
   ```bash
   ./scripts/restore.sh /path/to/backup
   ```

## Contact and Support

- Technical Support: support@soln.ai
- Emergency Contact: oncall@soln.ai
- Documentation: https://docs.soln.ai/srt-model-quantizing