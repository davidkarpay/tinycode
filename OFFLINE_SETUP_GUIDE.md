# TinyCode Offline Setup Guide

This guide ensures TinyCode can operate completely offline by pre-downloading all required models and dependencies.

## Prerequisites

- Python 3.8+
- Ollama installed
- Internet connection for initial model downloads
- At least 5GB free disk space

## Quick Verification

Check if your system is already ready for offline operation:

```bash
python scripts/verify_offline_models.py
```

## Complete Offline Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(sentence-transformers|faiss|ollama|chromadb)"
```

### 2. Download Ollama Models

```bash
# Download primary model (required)
ollama pull tinyllama:latest

# Optional: Download additional coding models
ollama pull qwen2.5-coder:7b
ollama pull starcoder2:7b

# Verify models
ollama list
```

### 3. Download Embedding Models

```bash
# Pre-download sentence transformers model
python -c "
from sentence_transformers import SentenceTransformer
print('Downloading all-MiniLM-L6-v2...')
model = SentenceTransformer('all-MiniLM-L6-v2')
print('✅ Model downloaded and cached')
"
```

### 4. Verify Offline Readiness

```bash
# Run comprehensive verification
python scripts/verify_offline_models.py

# Should show "Overall Status: PASS"
```

## Air-Gapped Environment Setup

For completely isolated environments without internet access:

### 1. Prepare Transfer Package

On a connected machine:

```bash
# Create offline package directory
mkdir tinyllama-offline-package
cd tinyllama-offline-package

# Download Python wheels
pip download -r requirements.txt -d wheels/

# Export Ollama models
ollama list | grep tinyllama
mkdir ollama-models
# Note: Ollama models are stored in ~/.ollama - copy this directory

# Download HuggingFace models
python -c "
import os
from sentence_transformers import SentenceTransformer
print('Pre-downloading models...')
model = SentenceTransformer('all-MiniLM-L6-v2')
print(f'Models cached in: {model.cache_folder}')
"

# Copy HuggingFace cache
cp -r ~/.cache/huggingface/ ./huggingface-cache/

# Create transfer archive
cd ..
tar -czf tinyllama-offline-package.tar.gz tinyllama-offline-package/
```

### 2. Install on Air-Gapped System

```bash
# Extract package
tar -xzf tinyllama-offline-package.tar.gz
cd tinyllama-offline-package

# Install Python packages
pip install --no-index --find-links wheels/ -r requirements.txt

# Restore Ollama models
cp -r ollama-models/* ~/.ollama/

# Restore HuggingFace cache
mkdir -p ~/.cache/
cp -r huggingface-cache/ ~/.cache/huggingface/

# Start Ollama service
ollama serve &

# Verify installation
python ../scripts/verify_offline_models.py
```

## Model Storage Locations

### Ollama Models
- **Location**: `~/.ollama/`
- **Size**: ~637MB for tinyllama:latest
- **Format**: GGUF binary files

### Embedding Models
- **Location**: `~/.cache/huggingface/hub/`
- **Size**: ~87MB for all-MiniLM-L6-v2
- **Format**: PyTorch model files

### Python Packages
- **Location**: Python site-packages
- **Size**: ~2GB for all dependencies
- **Critical packages**: sentence-transformers, faiss-cpu, chromadb

## Backup and Restore

### Create Model Backup

```bash
# Create backup directory
mkdir -p backups/models/$(date +%Y%m%d)

# Backup Ollama models
tar -czf backups/models/$(date +%Y%m%d)/ollama-models.tar.gz -C ~ .ollama

# Backup HuggingFace cache
tar -czf backups/models/$(date +%Y%m%d)/huggingface-cache.tar.gz -C ~/.cache huggingface

# Backup Python environment
pip freeze > backups/models/$(date +%Y%m%d)/requirements-freeze.txt
```

### Restore from Backup

```bash
# Restore Ollama models
tar -xzf backups/models/YYYYMMDD/ollama-models.tar.gz -C ~

# Restore HuggingFace cache
tar -xzf backups/models/YYYYMMDD/huggingface-cache.tar.gz -C ~/.cache/

# Restart Ollama
ollama serve &

# Verify restoration
python scripts/verify_offline_models.py
```

## Troubleshooting

### Common Issues

#### 1. Ollama Service Not Running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service
ollama serve &

# Or use systemd (if configured)
sudo systemctl start ollama
```

#### 2. Models Not Found
```bash
# Check available models
ollama list

# Re-download if missing
ollama pull tinyllama:latest
```

#### 3. Embedding Model Cache Issues
```bash
# Check cache location
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print(f'Cache: {model.cache_folder}')
"

# Clear and re-download cache
rm -rf ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

#### 4. Permission Issues
```bash
# Fix cache permissions
chmod -R 755 ~/.cache/huggingface/
chmod -R 755 ~/.ollama/

# Fix script permissions
chmod +x scripts/*.py
chmod +x scripts/*.sh
```

### Network Connectivity Test

Verify true offline operation:

```bash
# Disable network (temporary)
sudo ifconfig en0 down  # macOS
# sudo ip link set eth0 down  # Linux

# Test TinyCode functionality
python tiny_code.py

# Re-enable network
sudo ifconfig en0 up  # macOS
# sudo ip link set eth0 up  # Linux
```

## Performance Optimization

### Model Warm-up

Pre-load models to reduce startup time:

```bash
# Warm up Ollama model
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "tinyllama:latest", "prompt": "warmup", "stream": false}'

# Warm up embedding model
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.encode(['warmup text'])
print('✅ Models warmed up')
"
```

### Resource Optimization

```bash
# Check model memory usage
ps aux | grep ollama
ps aux | grep python

# Monitor disk space
du -sh ~/.ollama
du -sh ~/.cache/huggingface

# Clean up unnecessary models
ollama rm unused-model:tag
```

## Automated Setup Script

Use the provided automation script:

```bash
# Run complete setup
./scripts/download_models.sh

# Verify setup
python scripts/verify_offline_models.py
```

## Docker Offline Setup

For containerized deployments:

```bash
# Build offline-ready image
docker build -f docker/Dockerfile.offline -t tinyllama-offline .

# Run with model volumes
docker run -v ~/.ollama:/app/.ollama -v ~/.cache:/app/.cache tinyllama-offline

# Verify in container
docker exec -it container_name python scripts/verify_offline_models.py
```

## Security Considerations

- **Model Integrity**: Verify model checksums after transfer
- **Access Control**: Secure model directories with appropriate permissions
- **Audit Trail**: Log model downloads and modifications
- **Updates**: Plan for periodic offline model updates

## Deployment Checklist

- [ ] Ollama service running
- [ ] tinyllama:latest model available
- [ ] all-MiniLM-L6-v2 model cached
- [ ] Python dependencies installed
- [ ] FAISS operations functional
- [ ] Network connectivity disabled (test)
- [ ] Application starts without errors
- [ ] RAG functionality works
- [ ] Model responses generated

Run the verification script as final confirmation:

```bash
python scripts/verify_offline_models.py
# Expected: "Overall Status: PASS"
```