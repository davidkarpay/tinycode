# Docker Deployment Guide

This guide covers deploying TinyCode using Docker containers for development and production environments.

## Table of Contents

- [Quick Start](#quick-start)
- [Container Architecture](#container-architecture)
- [Docker Images](#docker-images)
- [Configuration](#configuration)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Offline Deployment](#offline-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Development Environment

```bash
# Clone repository
git clone https://github.com/davidkarpay/tinycode.git
cd tinycode

# Start development stack
make docker-up

# Or using docker-compose directly
docker-compose -f docker/docker-compose.yml up -d
```

### Production Environment

```bash
# Build production images
make docker-build

# Deploy with production settings
docker-compose -f docker/docker-compose.yml --profile production up -d
```

### Offline Environment

```bash
# Deploy offline-ready stack with pre-loaded models
make docker-offline-up

# Or using docker-compose directly
docker-compose -f docker/docker-compose.yml --profile offline up -d
```

## Container Architecture

TinyCode's Docker deployment consists of several interconnected services:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TinyCode      │───▶│     Redis       │    │    Nginx        │
│   Main App      │    │   Rate Limiting │    │ Reverse Proxy   │
│   Port: 8000    │    │   Port: 6379    │    │ Ports: 80/443   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │    Grafana      │    │   TinyCode      │
│   Metrics       │    │   Dashboards    │    │   Offline       │
│   Port: 9090    │    │   Port: 3000    │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Docker Images

### Base Image (`docker/Dockerfile`)

Multi-stage production build:
- **Builder stage**: Compiles dependencies
- **Production stage**: Minimal runtime image
- **Security**: Non-root user execution
- **Size**: ~200MB (optimized)

```dockerfile
FROM python:3.11-slim as builder
# Build dependencies
RUN apt-get update && apt-get install -y gcc g++ build-essential

FROM python:3.11-slim as production
# Runtime dependencies only
RUN apt-get update && apt-get install -y curl procps
# Non-root user for security
RUN groupadd -r tinyllama && useradd -r -g tinyllama tinyllama
```

### Offline Image (`docker/Dockerfile.offline`)

Self-contained image with pre-loaded models:
- **Pre-loaded models**: TinyLlama, embeddings
- **Ollama service**: Built-in local LLM server
- **Larger size**: ~2GB (includes models)
- **Air-gap ready**: No external dependencies

## Configuration

### Environment Variables

Create `.env` file for configuration:

```bash
# Core settings
OLLAMA_MODEL=tinyllama:latest
OLLAMA_HOST=localhost
OLLAMA_PORT=11434

# API settings
API_KEY_REQUIRED=true
API_KEY=your-secure-api-key-here
CORS_ORIGINS=*

# Redis settings
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=your-redis-password

# Security settings
SAFETY_LEVEL=moderate
REQUIRE_CONFIRMATION=true

# Performance settings
MAX_WORKERS=4
MAX_REQUESTS_PER_WORKER=1000
TIMEOUT=300

# Monitoring
METRICS_ENABLED=true
LOG_LEVEL=INFO
```

### Docker Compose Variables

```yaml
# docker-compose.yml
environment:
  - REDIS_URL=redis://redis:6379
  - API_KEY_REQUIRED=true
  - METRICS_ENABLED=true
  - LOG_LEVEL=INFO
  - SAFETY_LEVEL=${SAFETY_LEVEL:-moderate}
```

## Development Deployment

### Standard Development Stack

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Services available:
# - TinyCode API: http://localhost:8000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
# - Redis: localhost:6379
```

### Development with Hot Reload

```bash
# Mount source code for development
docker-compose -f docker/docker-compose.yml \
  -f docker/docker-compose.dev.yml up -d

# Source code changes trigger automatic reload
```

### Custom Configuration

```bash
# Use custom environment file
docker-compose --env-file .env.development up -d

# Override specific services
docker-compose up -d tinyllama redis
```

## Production Deployment

### Production Configuration

```yaml
# docker-compose.yml
services:
  tinyllama:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### SSL/TLS Setup

```bash
# Create SSL certificates directory
mkdir -p ssl/

# Generate self-signed certificates (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/tinycode.key \
  -out ssl/tinycode.crt

# Copy your production certificates
cp /path/to/production.crt ssl/
cp /path/to/production.key ssl/
```

### Production Deployment Steps

```bash
# 1. Build production images
docker-compose -f docker/docker-compose.yml build

# 2. Create production environment file
cp .env.example .env.production

# 3. Deploy with production profile
docker-compose -f docker/docker-compose.yml \
  --env-file .env.production up -d

# 4. Verify deployment
docker-compose ps
curl -k https://localhost/health
```

## Offline Deployment

### Offline-Ready Stack

For air-gapped environments:

```bash
# Build offline image (requires internet initially)
docker build -f docker/Dockerfile.offline -t tinycode-offline .

# Deploy offline stack
docker-compose -f docker/docker-compose.yml \
  --profile offline up -d

# Services:
# - TinyCode Offline: http://localhost:8001
# - Ollama: http://localhost:11435
```

### Model Pre-loading

The offline image pre-loads:
- TinyLlama model (~637MB)
- Sentence transformer embeddings (~87MB)
- FAISS vector operations
- Python dependencies

### Verification

```bash
# Test offline functionality
docker exec -it tinycode-offline python scripts/verify_offline_models.py

# Check model availability
docker exec -it tinycode-offline ollama list
```

## Monitoring

### Prometheus Metrics

TinyCode exposes metrics at `/metrics`:

```yaml
# Custom metrics
tinyllama_requests_total
tinyllama_request_duration_seconds
tinyllama_errors_total
tinyllama_active_sessions
tinyllama_model_inference_time
```

### Grafana Dashboards

Access Grafana at `http://localhost:3000`:
- Username: `admin`
- Password: `admin123`

Pre-configured dashboards:
- TinyCode Performance
- System Resources
- Error Rates
- User Activity

### Health Checks

```bash
# Container health
docker-compose ps

# Application health
curl http://localhost:8000/health

# Services health
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health # Grafana
```

## Troubleshooting

### Common Issues

#### Port Conflicts

```bash
# Check port usage
netstat -tulpn | grep -E "(8000|9090|3000|6379)"

# Change ports in docker-compose.yml
ports:
  - "8080:8000"  # Use different host port
```

#### Memory Issues

```bash
# Check container memory usage
docker stats

# Increase memory limits
deploy:
  resources:
    limits:
      memory: 4G
```

#### Model Loading Failures

```bash
# Check Ollama in offline container
docker exec -it tinycode-offline ollama list

# Rebuild with fresh models
docker build --no-cache -f docker/Dockerfile.offline .
```

#### Permission Issues

```bash
# Fix data directory permissions
sudo chown -R 1000:1000 data/
chmod -R 755 data/

# Check container user
docker exec -it tinyllama id
```

### Debugging Commands

```bash
# View logs
docker-compose logs -f tinyllama

# Interactive shell
docker exec -it tinyllama /bin/bash

# Check environment
docker exec -it tinyllama env

# Test connectivity
docker exec -it tinyllama curl http://localhost:11434/api/tags
```

### Performance Tuning

```bash
# Optimize for production
version: '3.8'
services:
  tinyllama:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    environment:
      - OLLAMA_NUM_PARALLEL=1
      - WORKERS=4
      - WORKER_CONNECTIONS=1000
```

## Advanced Configuration

### Custom Networking

```yaml
networks:
  tinycode_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  tinyllama:
    networks:
      - tinycode_network
```

### Volume Management

```yaml
volumes:
  tinyllama_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/tinycode/data

  redis_data:
    driver: local
```

### Secrets Management

```yaml
secrets:
  api_key:
    file: ./secrets/api_key.txt
  redis_password:
    file: ./secrets/redis_password.txt

services:
  tinyllama:
    secrets:
      - api_key
      - redis_password
```

## Backup and Recovery

### Data Backup

```bash
# Backup application data
docker run --rm -v tinycode_tinyllama_data:/data \
  -v $(pwd):/backup alpine \
  tar czf /backup/data-backup.tar.gz /data

# Backup Redis data
docker run --rm -v tinycode_redis_data:/data \
  -v $(pwd):/backup alpine \
  tar czf /backup/redis-backup.tar.gz /data
```

### Recovery

```bash
# Restore application data
docker run --rm -v tinycode_tinyllama_data:/data \
  -v $(pwd):/backup alpine \
  tar xzf /backup/data-backup.tar.gz -C /

# Restart services
docker-compose restart
```

## Security Best Practices

1. **Use non-root containers**: ✅ Implemented
2. **Limit container capabilities**: Configure in docker-compose
3. **Network segmentation**: Use custom networks
4. **Secret management**: Use Docker secrets
5. **Regular updates**: Keep base images updated
6. **Vulnerability scanning**: Use `docker scan`
7. **Read-only filesystems**: Where possible

## Deployment Checklist

- [ ] Environment variables configured
- [ ] SSL certificates in place (production)
- [ ] Resource limits set appropriately
- [ ] Health checks configured
- [ ] Monitoring enabled
- [ ] Backup strategy defined
- [ ] Network security configured
- [ ] Logs aggregation setup

## See Also

- [Production Deployment](production.md) - Enterprise deployment guide
- [Monitoring Guide](monitoring.md) - Detailed monitoring setup
- [Installation Guide](../getting-started/installation.md) - Initial setup
- [Troubleshooting](../reference/troubleshooting.md) - Common issues