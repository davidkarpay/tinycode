# TinyCode Production Deployment Guide

This guide covers deploying TinyCode in a production environment with enterprise-grade security, monitoring, and scalability.

## Quick Start

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run production deployment
./deploy.sh
```

## Architecture Overview

The production deployment includes:

- **API Server**: Flask-based REST API with rate limiting and authentication
- **Rate Limiting**: Token bucket algorithm with Redis backing
- **Resource Monitoring**: File handle management and system resource tracking
- **Reverse Proxy**: Nginx with SSL termination and security headers
- **Monitoring**: Prometheus metrics collection and Grafana dashboards
- **Containerization**: Docker with security hardening
- **Service Management**: Systemd with resource limits and security restrictions

## Components

### 1. Rate Limiting (`tiny_code/rate_limiter.py`)
- Token bucket algorithm implementation
- Configurable limits per operation type
- Redis backing for distributed deployments
- Automatic cleanup of expired tokens

### 2. API Server (`api_server.py`)
- Flask-based REST API
- API key authentication
- Prometheus metrics integration
- Health check endpoints
- CORS and security headers

### 3. Resource Monitor (`tiny_code/resource_monitor.py`)
- File handle management with automatic cleanup
- System resource monitoring
- Configurable thresholds and alerts
- Context manager for safe file operations

### 4. Nginx Configuration (`nginx/nginx.conf`)
- Reverse proxy with load balancing
- Rate limiting zones
- SSL termination
- Security headers
- Gzip compression

### 5. Docker Setup (`docker/`)
- Multi-stage builds for security
- Non-root user execution
- Health checks
- Resource limits
- Security scanning

### 6. Monitoring (`monitoring/`)
- Prometheus configuration
- Alert rules for critical metrics
- Grafana dashboard templates
- Custom metrics collection

## Security Features

- **Authentication**: API key-based authentication
- **Rate Limiting**: Multiple tiers of rate limiting
- **Resource Limits**: Memory, CPU, and file handle limits
- **Network Security**: Firewall rules and secure headers
- **Container Security**: Non-root execution, capability dropping
- **System Security**: SELinux/AppArmor integration

## Configuration

### Environment Variables (`.env.production`)
Key configuration options:
- `API_KEY_REQUIRED=true`
- `RATE_LIMIT_ENABLED=true`
- `METRICS_ENABLED=true`
- `SAFETY_LEVEL=standard`

### Resource Limits
- Memory: 2GB maximum
- CPU: 200% (2 cores)
- File handles: 4096
- Processes: 200

## Deployment Options

### 1. Docker Deployment (Recommended)
```bash
cd docker
docker-compose build
docker-compose up -d
```

### 2. Systemd Service
```bash
sudo cp systemd/tinyllama-coder.service /etc/systemd/system/
sudo systemctl enable tinyllama-coder
sudo systemctl start tinyllama-coder
```

### 3. Manual Deployment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
gunicorn -c gunicorn.conf.py api_server:app
```

## Monitoring & Alerting

### Metrics Available
- Request rate and latency
- Error rates by endpoint
- Resource utilization
- Rate limit statistics
- File handle usage

### Alert Rules
- API downtime detection
- High error rates
- Resource threshold breaches
- Rate limit violations

### Service URLs
- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## Maintenance

### Log Management
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f tinyllama

# System logs
journalctl -u tinyllama-coder -f
```

### Updates
```bash
# Update containers
docker-compose pull
docker-compose up -d

# Update systemd service
sudo systemctl restart tinyllama-coder
```

### Backup
```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env nginx/ monitoring/
```

## Troubleshooting

### Common Issues
1. **Port conflicts**: Check for services using ports 8000, 9090, 3000
2. **Permission errors**: Ensure proper file ownership for data directories
3. **Resource limits**: Monitor system resources and adjust limits as needed
4. **SSL issues**: Verify certificate paths and permissions

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Prometheus targets
curl http://localhost:9090/api/v1/targets

# Container status
docker-compose ps
```

## Performance Tuning

### Recommended Settings
- **Workers**: 1 worker per CPU core
- **Memory**: 2GB minimum, 4GB recommended
- **File handles**: 4096 minimum
- **Rate limits**: Adjust based on expected load

### Scaling
- Horizontal: Deploy multiple instances behind load balancer
- Vertical: Increase memory and CPU limits
- Database: Use Redis cluster for rate limiting state