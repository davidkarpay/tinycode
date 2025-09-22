# TinyCode Monitoring Guide

This guide covers comprehensive monitoring, alerting, and observability for TinyCode deployments.

## Table of Contents

- [Overview](#overview)
- [Metrics Collection](#metrics-collection)
- [Prometheus Setup](#prometheus-setup)
- [Grafana Dashboards](#grafana-dashboards)
- [Alerting](#alerting)
- [Log Management](#log-management)
- [Health Checks](#health-checks)
- [Performance Monitoring](#performance-monitoring)
- [Troubleshooting](#troubleshooting)

## Overview

TinyCode provides comprehensive observability through:
- **Prometheus metrics** for quantitative monitoring
- **Grafana dashboards** for visualization
- **Structured logging** for debugging
- **Health checks** for service availability
- **Custom alerts** for proactive issue detection

## Metrics Collection

### Application Metrics

TinyCode exposes metrics at the `/metrics` endpoint:

```python
# Core application metrics
tinyllama_requests_total{method="POST", endpoint="/complete", status="200"}
tinyllama_request_duration_seconds{endpoint="/complete"}
tinyllama_errors_total{error_type="validation", endpoint="/fix"}
tinyllama_active_sessions
tinyllama_concurrent_requests

# Model performance metrics
tinyllama_model_inference_time_seconds{model="tinyllama"}
tinyllama_model_requests_total{model="tinyllama", status="success"}
tinyllama_model_errors_total{model="tinyllama", error_type="timeout"}
tinyllama_tokens_generated_total
tinyllama_context_length_bytes

# RAG system metrics
tinyllama_rag_search_duration_seconds
tinyllama_rag_documents_indexed_total
tinyllama_rag_cache_hits_total
tinyllama_rag_cache_misses_total

# Safety metrics
tinyllama_safety_checks_total{level="strict", result="passed"}
tinyllama_plan_executions_total{risk_level="medium", status="completed"}
tinyllama_backups_created_total
tinyllama_rollbacks_total

# Resource metrics
tinyllama_memory_usage_bytes
tinyllama_cpu_usage_percent
tinyllama_disk_usage_bytes
tinyllama_file_handles_open
```

### System Metrics

Standard system metrics via node_exporter:

```yaml
# System resources
node_memory_MemAvailable_bytes
node_cpu_seconds_total
node_filesystem_avail_bytes
node_network_receive_bytes_total

# Docker metrics
container_memory_usage_bytes
container_cpu_usage_seconds_total
container_fs_usage_bytes
```

## Prometheus Setup

### Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  # TinyCode application
  - job_name: 'tinyllama'
    static_configs:
      - targets: ['tinyllama:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  # System metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Docker Deployment

```yaml
# docker-compose.yml
prometheus:
  image: prom/prometheus:latest
  container_name: prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    - ./monitoring/alert_rules.yml:/etc/prometheus/alert_rules.yml
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--web.console.libraries=/etc/prometheus/console_libraries'
    - '--web.console.templates=/etc/prometheus/consoles'
    - '--web.enable-lifecycle'
    - '--storage.tsdb.retention.time=30d'
```

## Grafana Dashboards

### Setup

```yaml
# docker-compose.yml
grafana:
  image: grafana/grafana:latest
  container_name: grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin123
    - GF_SECURITY_ADMIN_USER=admin
  volumes:
    - grafana_data:/var/lib/grafana
    - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
```

### TinyCode Dashboard

Main application dashboard panels:

#### Request Rate & Latency
```yaml
# Panel configuration
title: "Request Rate"
targets:
  - expr: rate(tinyllama_requests_total[5m])
    legendFormat: "{{endpoint}} - {{method}}"

title: "Request Latency P95"
targets:
  - expr: histogram_quantile(0.95, rate(tinyllama_request_duration_seconds_bucket[5m]))
    legendFormat: "{{endpoint}}"
```

#### Error Rates
```yaml
title: "Error Rate by Endpoint"
targets:
  - expr: rate(tinyllama_errors_total[5m]) / rate(tinyllama_requests_total[5m]) * 100
    legendFormat: "{{endpoint}} - {{error_type}}"
```

#### Model Performance
```yaml
title: "Model Inference Time"
targets:
  - expr: rate(tinyllama_model_inference_time_seconds[5m])
    legendFormat: "{{model}}"

title: "Tokens Generated/sec"
targets:
  - expr: rate(tinyllama_tokens_generated_total[5m])
    legendFormat: "Tokens/sec"
```

#### System Resources
```yaml
title: "Memory Usage"
targets:
  - expr: tinyllama_memory_usage_bytes / 1024 / 1024 / 1024
    legendFormat: "Memory (GB)"

title: "CPU Usage"
targets:
  - expr: tinyllama_cpu_usage_percent
    legendFormat: "CPU %"
```

### RAG System Dashboard

```yaml
title: "RAG Search Performance"
targets:
  - expr: histogram_quantile(0.95, rate(tinyllama_rag_search_duration_seconds_bucket[5m]))
    legendFormat: "Search Latency P95"

title: "RAG Cache Hit Rate"
targets:
  - expr: rate(tinyllama_rag_cache_hits_total[5m]) / (rate(tinyllama_rag_cache_hits_total[5m]) + rate(tinyllama_rag_cache_misses_total[5m])) * 100
    legendFormat: "Cache Hit Rate %"
```

### Safety Metrics Dashboard

```yaml
title: "Plan Execution Status"
targets:
  - expr: rate(tinyllama_plan_executions_total[5m])
    legendFormat: "{{status}} - {{risk_level}}"

title: "Safety Check Results"
targets:
  - expr: rate(tinyllama_safety_checks_total[5m])
    legendFormat: "{{level}} - {{result}}"
```

## Alerting

### Alert Rules

Create `monitoring/alert_rules.yml`:

```yaml
groups:
  - name: tinyllama_alerts
    rules:
      # High error rate
      - alert: TinyLlamaHighErrorRate
        expr: rate(tinyllama_errors_total[5m]) / rate(tinyllama_requests_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

      # Service down
      - alert: TinyLlamaServiceDown
        expr: up{job="tinyllama"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "TinyLlama service is down"
          description: "TinyLlama has been down for more than 1 minute"

      # High latency
      - alert: TinyLlamaHighLatency
        expr: histogram_quantile(0.95, rate(tinyllama_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High request latency"
          description: "95th percentile latency is {{ $value }}s"

      # Resource usage
      - alert: TinyLlamaHighMemoryUsage
        expr: tinyllama_memory_usage_bytes / (1024^3) > 1.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanize }}GB"

      # Model performance
      - alert: TinyLlamaModelTimeout
        expr: rate(tinyllama_model_errors_total{error_type="timeout"}[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Model timeout errors detected"
          description: "Model is experiencing timeout errors"

      # Safety alerts
      - alert: TinyLlamaFrequentRollbacks
        expr: rate(tinyllama_rollbacks_total[10m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Frequent plan rollbacks"
          description: "High rollback rate: {{ $value }} per second"
```

### AlertManager Configuration

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@tinycode.local'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    email_configs:
      - to: 'admin@tinycode.local'
        subject: 'TinyCode Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}

    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: 'TinyCode Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

## Log Management

### Structured Logging

TinyCode uses structured JSON logging:

```python
# Log format
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "tinyllama.api",
  "message": "Request completed",
  "request_id": "req_12345",
  "endpoint": "/complete",
  "method": "POST",
  "status_code": 200,
  "duration_ms": 150,
  "user_id": "user_123",
  "model": "tinyllama"
}
```

### Log Aggregation

#### Using ELK Stack

```yaml
# docker-compose.yml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
  environment:
    - discovery.type=single-node
  ports:
    - "9200:9200"

logstash:
  image: docker.elastic.co/logstash/logstash:7.14.0
  volumes:
    - ./monitoring/logstash.conf:/usr/share/logstash/pipeline/logstash.conf

kibana:
  image: docker.elastic.co/kibana/kibana:7.14.0
  ports:
    - "5601:5601"
  environment:
    - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

#### Using Loki

```yaml
# docker-compose.yml
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  volumes:
    - ./monitoring/loki.yml:/etc/loki/local-config.yaml

promtail:
  image: grafana/promtail:latest
  volumes:
    - /var/log:/var/log:ro
    - ./monitoring/promtail.yml:/etc/promtail/config.yml
```

### Log Analysis Queries

```yaml
# Common log queries
# Error rate by endpoint
sum by (endpoint) (rate({job="tinyllama"} |= "ERROR" [5m]))

# Slow requests
{job="tinyllama"} | json | duration_ms > 1000

# User activity
{job="tinyllama"} | json | line_format "{{.user_id}} {{.endpoint}}"
```

## Health Checks

### Application Health

```python
# /health endpoint response
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "checks": {
    "ollama": {
      "status": "healthy",
      "response_time_ms": 50
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2
    },
    "rag_system": {
      "status": "healthy",
      "documents_indexed": 1500
    },
    "database": {
      "status": "healthy",
      "connection_pool": "8/10"
    }
  },
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

### External Monitoring

```bash
# Uptime monitoring script
#!/bin/bash
ENDPOINT="http://localhost:8000/health"
TIMEOUT=5

response=$(curl -s -w "%{http_code}" --max-time $TIMEOUT "$ENDPOINT")
http_code=${response: -3}

if [[ $http_code -eq 200 ]]; then
    echo "✅ TinyCode is healthy"
    exit 0
else
    echo "❌ TinyCode health check failed: $http_code"
    exit 1
fi
```

## Performance Monitoring

### Key Performance Indicators (KPIs)

1. **Availability**: Target 99.9% uptime
2. **Response Time**: P95 < 2 seconds
3. **Error Rate**: < 1% of requests
4. **Throughput**: Requests per second capacity
5. **Model Performance**: Inference time consistency

### Performance Dashboards

```yaml
# SLA Dashboard
title: "Service Level Objectives"
panels:
  - title: "Availability (99.9% target)"
    expr: avg_over_time(up{job="tinyllama"}[24h]) * 100

  - title: "Response Time P95 (2s target)"
    expr: histogram_quantile(0.95, rate(tinyllama_request_duration_seconds_bucket[5m]))

  - title: "Error Rate (1% target)"
    expr: rate(tinyllama_errors_total[5m]) / rate(tinyllama_requests_total[5m]) * 100
```

### Capacity Planning

```yaml
# Resource utilization trends
title: "CPU Utilization Trend"
expr: avg_over_time(tinyllama_cpu_usage_percent[24h])

title: "Memory Growth Rate"
expr: deriv(tinyllama_memory_usage_bytes[1h])

title: "Request Volume Trend"
expr: avg_over_time(rate(tinyllama_requests_total[5m])[24h])
```

## Troubleshooting

### Common Monitoring Issues

#### No Metrics Available

```bash
# Check if metrics endpoint is accessible
curl http://localhost:8000/metrics

# Verify Prometheus can scrape
curl http://localhost:9090/api/v1/targets

# Check container connectivity
docker exec -it prometheus curl http://tinyllama:8000/metrics
```

#### Grafana Dashboard Issues

```bash
# Check datasource connection
curl -u admin:admin123 http://localhost:3000/api/datasources

# Test query
curl -u admin:admin123 \
  'http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up'
```

#### Alert Not Firing

```bash
# Check alert rules
curl http://localhost:9090/api/v1/rules

# Verify alert evaluation
curl http://localhost:9090/api/v1/alerts

# Test alert condition manually
curl 'http://localhost:9090/api/v1/query?query=up{job="tinyllama"}'
```

### Debugging Commands

```bash
# Check all monitoring services
docker-compose ps prometheus grafana alertmanager

# View Prometheus config
docker exec -it prometheus cat /etc/prometheus/prometheus.yml

# Check Grafana logs
docker logs grafana

# Validate alert rules
docker exec -it prometheus promtool check rules /etc/prometheus/alert_rules.yml
```

## Monitoring Checklist

- [ ] Prometheus collecting all metrics
- [ ] Grafana dashboards configured
- [ ] Alert rules defined and tested
- [ ] Log aggregation working
- [ ] Health checks responding
- [ ] External monitoring setup
- [ ] SLA targets defined
- [ ] Escalation procedures documented

## See Also

- [Production Deployment](production.md) - Enterprise deployment
- [Docker Guide](docker.md) - Container deployment
- [Troubleshooting](../reference/troubleshooting.md) - Issue resolution
- [Configuration Reference](../reference/configuration.md) - All settings