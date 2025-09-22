# TinyCode Troubleshooting Guide

This guide helps resolve common issues encountered when installing, configuring, or using TinyCode.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Ollama Service Issues](#ollama-service-issues)
- [Model Issues](#model-issues)
- [Python Environment Issues](#python-environment-issues)
- [Docker Issues](#docker-issues)
- [Performance Issues](#performance-issues)
- [RAG System Issues](#rag-system-issues)
- [Safety System Issues](#safety-system-issues)
- [General Debugging](#general-debugging)

## Installation Issues

### Python Version Compatibility

**Problem**: `ModuleNotFoundError` or compatibility errors
```bash
ERROR: Python 3.7 is not supported
```

**Solutions**:
```bash
# Check Python version
python --version

# Install Python 3.8+ if needed
# macOS with Homebrew
brew install python@3.11

# Ubuntu/Debian
sudo apt update && sudo apt install python3.11

# Use pyenv for version management
pyenv install 3.11.0
pyenv local 3.11.0
```

### Virtual Environment Issues

**Problem**: Package conflicts or permission errors

**Solutions**:
```bash
# Create fresh virtual environment
python -m venv venv-tinycode
source venv-tinycode/bin/activate  # Linux/macOS
# or
venv-tinycode\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Permission Errors

**Problem**: `Permission denied` when running scripts
```bash
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

**Problem**: `Permission denied` when accessing data directories
```bash
chmod -R 755 data/
chown -R $USER:$USER data/
```

## Ollama Service Issues

### Service Not Running

**Problem**: `Could not connect to Ollama`

**Diagnosis**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check process
ps aux | grep ollama
```

**Solutions**:
```bash
# Start Ollama service
ollama serve

# Run in background
ollama serve &

# Check specific host/port
export OLLAMA_HOST=localhost
export OLLAMA_PORT=11434
ollama serve --host 0.0.0.0 --port 11434
```

### Ollama Installation Issues

**Problem**: `ollama: command not found`

**Solutions**:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Manual installation (Linux)
wget https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64
chmod +x ollama-linux-amd64
sudo mv ollama-linux-amd64 /usr/local/bin/ollama

# Verify installation
ollama --version
```

### Port Conflicts

**Problem**: `Port 11434 already in use`

**Solutions**:
```bash
# Find process using port
lsof -i :11434
netstat -tulpn | grep 11434

# Kill existing process
pkill ollama

# Use different port
ollama serve --port 11435
export OLLAMA_PORT=11435
```

## Model Issues

### Model Not Found

**Problem**: `Model 'tinyllama' not found`

**Solutions**:
```bash
# List available models
ollama list

# Pull required model
ollama pull tinyllama:latest

# Verify model
ollama show tinyllama:latest
```

### Model Download Failures

**Problem**: Download timeouts or network errors

**Solutions**:
```bash
# Retry with specific tag
ollama pull tinyllama:latest

# Check disk space
df -h

# Clear corrupted downloads
rm -rf ~/.ollama/models/blobs/*
ollama pull tinyllama:latest
```

### Model Performance Issues

**Problem**: Slow model responses

**Solutions**:
```bash
# Check system resources
htop
nvidia-smi  # If using GPU

# Reduce parallel requests
export OLLAMA_NUM_PARALLEL=1

# Use smaller model
ollama pull tinyllama:latest  # Instead of larger models
```

## Python Environment Issues

### Package Installation Failures

**Problem**: Failed to install specific packages

**Solutions**:
```bash
# Update pip and setuptools
pip install --upgrade pip setuptools wheel

# Install with specific options
pip install --no-cache-dir -r requirements.txt

# Install problematic packages individually
pip install sentence-transformers
pip install faiss-cpu
pip install ollama
```

### FAISS Installation Issues

**Problem**: FAISS compilation errors

**Solutions**:
```bash
# Use CPU version
pip install faiss-cpu

# Clear cache and reinstall
pip cache purge
pip install --no-cache-dir faiss-cpu

# Platform-specific
# macOS
brew install openblas
pip install faiss-cpu

# Ubuntu/Debian
sudo apt-get install python3-dev build-essential
pip install faiss-cpu
```

### Sentence Transformers Issues

**Problem**: Model download failures or CUDA errors

**Solutions**:
```bash
# Force CPU usage
export CUDA_VISIBLE_DEVICES=""

# Clear HuggingFace cache
rm -rf ~/.cache/huggingface/

# Reinstall
pip uninstall sentence-transformers
pip install sentence-transformers
```

## Docker Issues

### Build Failures

**Problem**: Docker build errors

**Solutions**:
```bash
# Clean Docker cache
docker system prune -a

# Build with no cache
docker build --no-cache -f docker/Dockerfile .

# Check available space
docker system df
```

### Container Startup Issues

**Problem**: Container crashes or health check failures

**Solutions**:
```bash
# Check container logs
docker-compose -f docker/docker-compose.yml logs tinyllama

# Run container interactively
docker run -it tinycode:latest /bin/bash

# Check resource limits
docker stats
```

### Volume Mount Issues

**Problem**: Permission denied in containers

**Solutions**:
```bash
# Fix host permissions
chmod -R 755 ./data
chmod -R 755 ./logs

# Use correct user ID
docker run --user $(id -u):$(id -g) tinycode:latest
```

## Performance Issues

### Memory Issues

**Problem**: Out of memory errors

**Solutions**:
```bash
# Check memory usage
free -h
top

# Reduce model concurrency
export OLLAMA_NUM_PARALLEL=1

# Increase swap space (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### CPU Usage Issues

**Problem**: High CPU usage

**Solutions**:
```bash
# Monitor processes
htop

# Limit CPU usage
nice -n 10 python tiny_code.py

# Reduce thread count
export OMP_NUM_THREADS=2
```

### Disk Space Issues

**Problem**: No space left on device

**Solutions**:
```bash
# Check disk usage
df -h
du -sh ~/.ollama
du -sh ~/.cache/huggingface

# Clean up
docker system prune -a
pip cache purge
rm -rf ~/.cache/huggingface/hub/models--*
```

## RAG System Issues

### Embedding Issues

**Problem**: Embedding generation failures

**Solutions**:
```bash
# Test embedding model
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(['test'])
print('Embeddings shape:', embeddings.shape)
"

# Clear embedding cache
rm -rf ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2
```

### Vector Store Issues

**Problem**: FAISS index corruption or errors

**Solutions**:
```bash
# Remove corrupted index
rm -rf data/index/faiss/*

# Rebuild index
python tiny_code_rag.py ingest /path/to/documents

# Test FAISS operations
python -c "
import faiss
import numpy as np
index = faiss.IndexFlatL2(384)
vectors = np.random.random((10, 384)).astype('float32')
index.add(vectors)
print('FAISS test successful')
"
```

### Document Ingestion Issues

**Problem**: Failed to process documents

**Solutions**:
```bash
# Check file permissions
chmod 644 /path/to/documents/*

# Process files individually
python tiny_code_rag.py ingest single_file.pdf

# Check supported formats
file /path/to/document
```

## Safety System Issues

### Mode Switching Problems

**Problem**: Cannot switch modes or commands rejected

**Solutions**:
```bash
# Check current mode
/mode status

# Reset to chat mode
/mode chat

# Clear any pending operations
exit  # and restart
```

### Plan Execution Issues

**Problem**: Plans fail to execute or get stuck

**Solutions**:
```bash
# List current plans
/list_plans

# Check plan status
/show_plan 1

# Cancel problematic plan
/cancel_plan 1

# Clear all plans (restart application)
```

### Backup System Issues

**Problem**: Backup creation failures

**Solutions**:
```bash
# Check backup directory permissions
chmod 755 data/backups/

# Manual backup
cp important_file.py data/backups/important_file.py.backup
```

## General Debugging

### Enable Debug Logging

```bash
# Set environment variables
export LOG_LEVEL=DEBUG
export PYTHONPATH=/path/to/tinycode

# Run with verbose output
python -v tiny_code.py
```

### Comprehensive System Check

```bash
# Run verification script
python scripts/verify_offline_models.py

# Check all components
make health  # If Makefile is available

# Manual checks
python --version
pip list | grep -E "(ollama|sentence|faiss|rich)"
curl http://localhost:11434/api/tags
ollama list
```

### Log File Locations

```bash
# Application logs
ls -la logs/

# Ollama logs (varies by system)
# macOS
cat ~/.ollama/logs/server.log

# Linux systemd
journalctl -u ollama

# Docker logs
docker-compose -f docker/docker-compose.yml logs
```

### Getting Help

If issues persist:

1. **Check GitHub Issues**: Search existing issues at the repository
2. **Run verification**: `python scripts/verify_offline_models.py`
3. **Collect information**:
   ```bash
   # System info
   uname -a
   python --version
   pip --version

   # TinyCode info
   ls -la
   cat requirements.txt

   # Resource info
   free -h
   df -h
   ```

4. **Create minimal reproduction**:
   ```bash
   # Start fresh
   python -c "import ollama; print('Ollama imported')"
   python -c "from sentence_transformers import SentenceTransformer; print('ST imported')"
   python -c "import faiss; print('FAISS imported')"
   ```

### Emergency Recovery

If TinyCode is completely broken:

```bash
# Complete reset
pip uninstall -r requirements.txt -y
rm -rf venv/
rm -rf data/
rm -rf ~/.cache/huggingface/
pkill ollama

# Fresh installation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./scripts/download_models.sh
python scripts/verify_offline_models.py
```

### Platform-Specific Notes

#### macOS
- Use Homebrew for system dependencies
- Check security settings for script execution
- Consider using Docker for isolation

#### Linux
- Install build tools: `sudo apt-get install build-essential`
- Check systemd services: `systemctl status ollama`
- Monitor system resources: `htop`, `iotop`

#### Windows (WSL)
- Use WSL2 for better performance
- Ensure WSL has sufficient memory allocated
- Access files via `/mnt/c/path/to/project`

Remember to always backup important data before attempting major fixes!