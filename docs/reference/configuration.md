# TinyCode Configuration Reference

This document provides comprehensive reference for all TinyCode configuration options, environment variables, and configuration files.

## Table of Contents

- [Configuration Overview](#configuration-overview)
- [Environment Variables](#environment-variables)
- [Configuration Files](#configuration-files)
- [Safety Configuration](#safety-configuration)
- [RAG System Configuration](#rag-system-configuration)
- [Performance Configuration](#performance-configuration)
- [Docker Configuration](#docker-configuration)
- [Advanced Configuration](#advanced-configuration)

## Configuration Overview

TinyCode uses a hierarchical configuration system:

1. **Default values** (hardcoded in source)
2. **Configuration files** (YAML/JSON)
3. **Environment variables** (override files)
4. **Command-line arguments** (override all)

### Configuration Precedence

```
Command Line > Environment Variables > Config Files > Defaults
```

### Configuration Locations

```
config/
├── rag_config.yaml         # RAG system settings
├── genetics_corpus.yaml    # Genetics knowledge sources
└── safety.yaml            # Safety configuration (optional)

.env                        # Environment variables
.env.production            # Production overrides
.env.development           # Development overrides
```

## Environment Variables

### Core Settings

```bash
# Model Configuration
OLLAMA_MODEL=tinyllama:latest       # Default model to use
OLLAMA_HOST=localhost               # Ollama server host
OLLAMA_PORT=11434                   # Ollama server port
OLLAMA_TIMEOUT=60                   # Request timeout (seconds)
OLLAMA_NUM_PARALLEL=1               # Parallel requests limit

# TinyCode Behavior
SAFETY_LEVEL=moderate               # Safety level (permissive/moderate/strict/paranoid)
DEFAULT_MODE=chat                   # Starting mode (chat/propose/execute)
REQUIRE_CONFIRMATION=true           # Require user confirmation for changes
AUTO_BACKUP=true                    # Enable automatic backups

# Paths and Storage
DATA_DIR=./data                     # Main data directory
LOG_DIR=./logs                      # Log file directory
BACKUP_DIR=./data/backups          # Backup storage location
RAG_INDEX_PATH=./data/index        # RAG vector index path
AUDIT_LOG_PATH=./data/audit_logs   # Audit log storage

# Performance Settings
MAX_TOKENS=2048                     # Maximum tokens per request
TEMPERATURE=0.7                     # Model temperature
MAX_CONTEXT_LENGTH=4096            # Maximum context window
CACHE_SIZE=1000                    # Response cache size (entries)

# Timeouts
PLAN_TIMEOUT=300                   # Plan execution timeout (seconds)
ACTION_TIMEOUT=30                  # Individual action timeout (seconds)
REQUEST_TIMEOUT=60                 # HTTP request timeout
CONNECTION_TIMEOUT=10              # Connection timeout

# Resource Limits
MAX_MEMORY_MB=2048                 # Maximum memory usage (MB)
MAX_CPU_PERCENT=80                 # Maximum CPU usage (%)
MAX_DISK_IO_MBPS=100              # Maximum disk I/O (MB/s)
MAX_OPEN_FILES=100                # Maximum open file handles
```

### API Server Settings

```bash
# Server Configuration
HOST=0.0.0.0                      # Server bind address
PORT=8000                         # Server port
DEBUG=false                       # Debug mode
WORKERS=4                         # Number of worker processes

# Security
API_KEY_REQUIRED=true             # Require API key authentication
API_KEY=your-secure-key-here      # API key (generate securely)
CORS_ORIGINS=*                    # CORS allowed origins
RATE_LIMIT_ENABLED=true           # Enable rate limiting
RATE_LIMIT_REQUESTS=100           # Requests per minute
RATE_LIMIT_WINDOW=60              # Rate limit window (seconds)

# SSL/TLS
SSL_ENABLED=false                 # Enable SSL
SSL_CERT_PATH=/path/to/cert.pem   # SSL certificate path
SSL_KEY_PATH=/path/to/key.pem     # SSL private key path
```

### RAG System Settings

```bash
# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Sentence transformer model
EMBEDDING_DIMENSION=384           # Embedding vector dimension
EMBEDDING_BATCH_SIZE=32           # Batch size for embeddings
EMBEDDING_CACHE_SIZE=10000        # Number of cached embeddings

# Vector Search
VECTOR_STORE=faiss                # Vector store backend (faiss/chromadb)
FAISS_INDEX_TYPE=IVF              # FAISS index type (Flat/IVF/HNSW)
SEARCH_TOP_K=10                   # Number of search results
HYBRID_ALPHA=0.7                  # Dense vs sparse search weight
BM25_K1=1.2                      # BM25 parameter k1
BM25_B=0.75                      # BM25 parameter b

# Document Processing
CHUNK_SIZE=800                    # Document chunk size (characters)
CHUNK_OVERLAP=100                 # Overlap between chunks
MAX_DOCUMENT_SIZE=10000000        # Maximum document size (bytes)
SUPPORTED_FORMATS=pdf,docx,txt,md,py,js,html

# Knowledge Bases
DEFAULT_KB=general                # Default knowledge base
KB_AUTO_CREATE=true              # Auto-create knowledge bases
KB_MAX_SIZE=1000000              # Maximum KB size (documents)
```

### Logging Configuration

```bash
# Log Levels
LOG_LEVEL=INFO                    # Global log level (DEBUG/INFO/WARNING/ERROR)
API_LOG_LEVEL=INFO               # API-specific log level
RAG_LOG_LEVEL=WARNING            # RAG system log level
SAFETY_LOG_LEVEL=INFO           # Safety system log level

# Log Format
LOG_FORMAT=json                   # Log format (json/text)
LOG_TIMESTAMP=true               # Include timestamps
LOG_COLORS=true                  # Colored output (CLI only)

# Log Rotation
LOG_MAX_SIZE=100MB               # Maximum log file size
LOG_BACKUP_COUNT=5               # Number of backup logs to keep
LOG_ROTATION=daily               # Rotation frequency (daily/weekly/monthly)

# Audit Logging
AUDIT_ENABLED=true               # Enable audit logging
AUDIT_HASH_CHAIN=true           # Enable hash chain integrity
AUDIT_COMPRESSION=true          # Compress old audit logs
AUDIT_RETENTION_DAYS=90         # Audit log retention period
```

### Development Settings

```bash
# Development Mode
DEVELOPMENT=false                # Enable development mode
AUTO_RELOAD=false               # Auto-reload on code changes
DEBUG_MODE=false                # Enable debug features
PROFILING=false                 # Enable performance profiling

# Testing
TEST_MODE=false                 # Enable test mode
MOCK_OLLAMA=false              # Use mock Ollama client
SKIP_MODEL_DOWNLOAD=false      # Skip model verification
TEST_DATA_DIR=./test_data      # Test data directory
```

## Configuration Files

### Main RAG Configuration (`config/rag_config.yaml`)

```yaml
# Embedding settings
embedding:
  model: "all-MiniLM-L6-v2"
  dimension: 384
  batch_size: 32
  cache_size: 10000
  device: "cpu"  # cpu/cuda/mps

# Vector store settings
vectorstore:
  backend: "faiss"
  index_type: "IVF"
  nlist: 100
  nprobe: 10
  metric: "L2"

# Retrieval settings
retrieval:
  hybrid_search: true
  hybrid_alpha: 0.7
  top_k: 10
  score_threshold: 0.5
  rerank: false

# Document processing
document:
  chunk_size: 800
  chunk_overlap: 100
  max_size: 10000000
  formats:
    - pdf
    - docx
    - txt
    - md
    - py
    - js
    - html
    - json
    - yaml

# Language model settings
llm:
  primary_model: "tinyllama:latest"
  fallback_model: "tinyllama:latest"
  temperature: 0.7
  max_tokens: 2048
  timeout: 60

# Performance settings
performance:
  index_batch_size: 1000
  search_timeout: 30
  max_concurrent_requests: 5
  cache_embeddings: true
  preload_index: true

# Knowledge base settings
knowledge_bases:
  general:
    description: "General purpose knowledge base"
    max_documents: 10000
    auto_cleanup: true

  genetics:
    description: "Genetics and bioinformatics knowledge"
    max_documents: 5000
    specialized: true

  code:
    description: "Programming examples and patterns"
    max_documents: 5000
    code_specific: true
```

### Genetics Corpus Configuration (`config/genetics_corpus.yaml`)

```yaml
sources:
  hts_specs:
    name: "HTS Format Specifications"
    base_url: "https://samtools.github.io/hts-specs/"
    max_pages: 50
    include_patterns:
      - "SAMv1.pdf"
      - "VCFv4.3.pdf"
      - "tabix.pdf"
    priority: high

  gatk_docs:
    name: "GATK Best Practices"
    base_url: "https://gatk.broadinstitute.org/hc/en-us"
    max_pages: 100
    sections:
      - "best-practices"
      - "tool-docs"
    priority: high

  samtools:
    name: "SAMtools Documentation"
    base_url: "http://www.htslib.org/"
    max_pages: 30
    include_patterns:
      - "doc/*"
    priority: medium

  ncbi:
    name: "NCBI Resources"
    base_url: "https://www.ncbi.nlm.nih.gov/"
    max_pages: 50
    sections:
      - "RefSeq"
      - "ClinVar"
      - "dbSNP"
    priority: medium

crawling:
  rate_limit: 1.0  # Requests per second
  timeout: 30
  retries: 3
  respect_robots: true
  user_agent: "TinyCode-Bot/1.0"

processing:
  extract_text: true
  extract_tables: true
  extract_code: true
  min_content_length: 100
  remove_navigation: true
  clean_html: true
```

### Safety Configuration (`config/safety.yaml`)

```yaml
# Safety levels
levels:
  permissive:
    confirmations: minimal
    backups: manual
    validation: basic
    audit: optional

  moderate:
    confirmations: medium_risk
    backups: automatic
    validation: standard
    audit: enabled

  strict:
    confirmations: all_changes
    backups: always
    validation: enhanced
    audit: required

  paranoid:
    confirmations: everything
    backups: multiple
    validation: maximum
    audit: hash_chain

# Validation rules
validation:
  dangerous_patterns:
    - "rm\\s+-rf\\s+/"
    - "DROP\\s+TABLE"
    - "eval\\s*\\("
    - "exec\\s*\\("
    - "__import__"
    - "subprocess\\.call"
    - "os\\.system"

  blocked_paths:
    - "/etc"
    - "/usr"
    - "/bin"
    - "/sbin"
    - "/System"
    - "/Windows"
    - "../"
    - "/.."

  file_limits:
    max_size: 10000000  # 10MB
    max_lines: 100000
    max_line_length: 10000

# Backup settings
backup:
  automatic: true
  compression: true
  retention_days: 30
  max_backups: 100
  exclude_patterns:
    - "*.log"
    - "*.tmp"
    - "__pycache__"
    - ".git"

# Audit settings
audit:
  enabled: true
  hash_chain: true
  compression: true
  retention_days: 90
  max_log_size: 100000000  # 100MB

# Resource limits
resources:
  max_memory: 2147483648   # 2GB
  max_cpu_time: 300        # 5 minutes
  max_open_files: 100
  max_disk_io: 104857600   # 100MB/s

# Timeouts
timeouts:
  plan_execution: 300      # 5 minutes
  action_execution: 30     # 30 seconds
  user_confirmation: 300   # 5 minutes
  network_request: 60      # 1 minute
```

## Performance Configuration

### Memory Management

```bash
# Memory Settings
MEMORY_LIMIT=2048                 # Total memory limit (MB)
MODEL_MEMORY_LIMIT=1024          # Model-specific memory limit
CACHE_MEMORY_LIMIT=512           # Cache memory limit
EMBEDDING_MEMORY_LIMIT=256       # Embedding memory limit

# Garbage Collection
GC_THRESHOLD=0.8                 # GC threshold (% of memory limit)
GC_FREQUENCY=60                  # GC frequency (seconds)
FORCE_GC_AFTER_REQUEST=false     # Force GC after each request
```

### Caching Configuration

```bash
# Response Caching
RESPONSE_CACHE_ENABLED=true      # Enable response caching
RESPONSE_CACHE_SIZE=1000         # Number of cached responses
RESPONSE_CACHE_TTL=3600         # Cache TTL (seconds)

# Embedding Caching
EMBEDDING_CACHE_ENABLED=true     # Enable embedding caching
EMBEDDING_CACHE_SIZE=10000       # Number of cached embeddings
EMBEDDING_CACHE_TTL=86400       # Cache TTL (seconds)

# Model Caching
MODEL_CACHE_ENABLED=true         # Enable model caching
MODEL_PRELOAD=true              # Preload models at startup
MODEL_WARMUP=true               # Warm up models at startup
```

### Concurrent Processing

```bash
# Threading
MAX_THREADS=4                    # Maximum thread pool size
THREAD_TIMEOUT=30               # Thread timeout (seconds)
QUEUE_SIZE=100                  # Task queue size

# Async Processing
ASYNC_ENABLED=true              # Enable async processing
ASYNC_POOL_SIZE=10              # Async pool size
ASYNC_TIMEOUT=60                # Async operation timeout
```

## Docker Configuration

### Environment Files

Create `.env.docker` for Docker-specific settings:

```bash
# Docker-specific settings
DOCKER_NETWORK=tinycode_network
DOCKER_VOLUME_PATH=/app/data
DOCKER_LOG_DRIVER=json-file
DOCKER_LOG_MAX_SIZE=10m

# Container settings
CONTAINER_MEMORY_LIMIT=2g
CONTAINER_CPU_LIMIT=2.0
CONTAINER_RESTART_POLICY=unless-stopped

# Service dependencies
REDIS_URL=redis://redis:6379
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
```

### Docker Compose Variables

```yaml
# docker-compose.yml
version: '3.8'

x-common-variables: &common-variables
  OLLAMA_HOST: localhost
  OLLAMA_PORT: 11434
  SAFETY_LEVEL: ${SAFETY_LEVEL:-moderate}
  LOG_LEVEL: ${LOG_LEVEL:-INFO}

services:
  tinyllama:
    environment:
      <<: *common-variables
      REDIS_URL: redis://redis:6379
      API_KEY_REQUIRED: ${API_KEY_REQUIRED:-true}
```

## Advanced Configuration

### Custom Model Configuration

```yaml
# Custom model settings
models:
  tinyllama:
    name: "tinyllama:latest"
    context_length: 4096
    temperature: 0.7
    top_p: 0.9
    top_k: 40
    repeat_penalty: 1.1

  custom_model:
    name: "custom:latest"
    context_length: 8192
    temperature: 0.5
    specialized: true
    use_cases: ["code_generation"]
```

### Plugin Configuration

```yaml
# Plugin system (future feature)
plugins:
  enabled: true
  directory: "./plugins"
  auto_load: true

  available:
    - name: "git_integration"
      enabled: true
      config:
        auto_commit: false
        commit_message_template: "TinyCode: {description}"

    - name: "ide_integration"
      enabled: false
      config:
        supported_ides: ["vscode", "pycharm"]
```

### Advanced RAG Configuration

```yaml
# Advanced RAG settings
advanced_rag:
  reranking:
    enabled: false
    model: "cross-encoder/ms-marco-MiniLM-L-2-v2"
    top_k_rerank: 20

  query_expansion:
    enabled: false
    method: "keyword"  # keyword/llm/embedding
    max_expansions: 3

  multi_vector:
    enabled: false
    summary_vectors: true
    keyword_vectors: true

  adaptive_chunking:
    enabled: false
    min_chunk_size: 400
    max_chunk_size: 1200
    similarity_threshold: 0.8
```

## Configuration Validation

### Validation Commands

```bash
# Validate configuration
python -m tiny_code.config validate

# Show current configuration
python -m tiny_code.config show

# Test configuration
python -m tiny_code.config test

# Export configuration
python -m tiny_code.config export --format yaml
```

### Configuration Schema

```python
# Configuration validation schema
CONFIG_SCHEMA = {
    "ollama": {
        "required": ["host", "port"],
        "optional": ["model", "timeout"]
    },
    "safety": {
        "required": ["level"],
        "valid_levels": ["permissive", "moderate", "strict", "paranoid"]
    },
    "rag": {
        "required": ["embedding_model"],
        "optional": ["top_k", "hybrid_alpha"]
    }
}
```

## Environment-Specific Configurations

### Development

```bash
# .env.development
DEBUG=true
LOG_LEVEL=DEBUG
AUTO_RELOAD=true
SAFETY_LEVEL=permissive
MOCK_EXTERNAL_SERVICES=true
```

### Staging

```bash
# .env.staging
DEBUG=false
LOG_LEVEL=INFO
SAFETY_LEVEL=strict
RATE_LIMIT_ENABLED=true
MONITORING_ENABLED=true
```

### Production

```bash
# .env.production
DEBUG=false
LOG_LEVEL=WARNING
SAFETY_LEVEL=strict
API_KEY_REQUIRED=true
SSL_ENABLED=true
MONITORING_ENABLED=true
AUDIT_ENABLED=true
```

## Configuration Best Practices

1. **Use Environment Variables**: For secrets and environment-specific settings
2. **Configuration Files**: For complex, structured configuration
3. **Validation**: Always validate configuration at startup
4. **Documentation**: Document all configuration options
5. **Defaults**: Provide sensible defaults for all options
6. **Security**: Never commit secrets to version control
7. **Monitoring**: Monitor configuration changes
8. **Testing**: Test different configuration combinations

## See Also

- [Architecture Reference](architecture.md) - System architecture
- [Safety Features](../user-guide/safety.md) - Safety configuration details
- [Production Deployment](../deployment/production.md) - Production settings
- [Troubleshooting](troubleshooting.md) - Configuration issues