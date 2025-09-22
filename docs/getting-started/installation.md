# Installation Guide

This guide walks through installing TinyCode and its dependencies for different use cases.

## Table of Contents

- [Requirements](#requirements)
- [Quick Install](#quick-install)
- [Detailed Installation](#detailed-installation)
- [Offline Setup](#offline-setup)
- [Docker Installation](#docker-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Requirements

### System Requirements
- **OS**: Linux, macOS, or Windows (WSL recommended)
- **Python**: 3.8 or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 5GB free space for models and data
- **CPU**: Multi-core processor recommended

### Software Dependencies
- Python 3.8+
- pip (Python package manager)
- Ollama for local LLM inference
- Git (for cloning repository)

## Quick Install

For most users, this quick installation will get you started:

```bash
# 1. Clone the repository
git clone https://github.com/davidkarpay/tinycode.git
cd tinycode

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Ollama (if not already installed)
# macOS/Linux:
curl -fsSL https://ollama.ai/install.sh | sh

# 4. Download TinyLlama model
ollama pull tinyllama

# 5. Verify installation
python scripts/verify_offline_models.py

# 6. Launch TinyCode
python tiny_code.py
```

## Detailed Installation

### Step 1: Python Setup

Ensure Python 3.8+ is installed:

```bash
python --version
# or
python3 --version
```

If Python is not installed, download from [python.org](https://python.org) or use your package manager:

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip

# macOS with Homebrew
brew install python@3.11

# Windows
# Download installer from python.org
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Step 3: Clone Repository

```bash
git clone https://github.com/davidkarpay/tinycode.git
cd tinycode
```

### Step 4: Install Python Dependencies

```bash
# Basic installation
pip install -r requirements.txt

# With specific versions locked
pip install --no-cache-dir -r requirements.txt

# For development (if requirements-dev.txt exists)
pip install -r requirements-dev.txt
```

### Step 5: Install Ollama

#### macOS/Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows
Download and run the installer from [ollama.ai](https://ollama.ai)

#### Manual Installation
```bash
# Download binary for your platform from https://github.com/ollama/ollama/releases
wget https://github.com/ollama/ollama/releases/download/v0.1.0/ollama-linux-amd64
chmod +x ollama-linux-amd64
sudo mv ollama-linux-amd64 /usr/local/bin/ollama
```

### Step 6: Start Ollama Service

```bash
# Start Ollama service
ollama serve

# In a new terminal, verify it's running
curl http://localhost:11434/api/tags
```

### Step 7: Download Models

```bash
# Download TinyLlama (required)
ollama pull tinyllama

# Optional: Download additional models
ollama pull qwen2.5-coder:7b
ollama pull starcoder2:7b

# Download embedding models for RAG
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

## Offline Setup

For completely offline operation, pre-download all models and dependencies:

```bash
# Use the automated script
./scripts/download_models.sh

# Or manually download everything
./scripts/download_models.sh --all

# Verify offline readiness
python scripts/verify_offline_models.py
```

See [Offline Setup Guide](offline-setup.md) for detailed offline deployment instructions.

## Docker Installation

### Using Docker Compose

```bash
# Build and start all services
docker-compose -f docker/docker-compose.yml up -d

# With offline-ready configuration
docker-compose -f docker/docker-compose.yml --profile offline up -d

# Check status
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f tinyllama
```

### Using Docker Directly

```bash
# Build Docker image
docker build -t tinycode:latest -f docker/Dockerfile .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --name tinycode \
  tinycode:latest
```

## Verification

### Verify Installation

Run the comprehensive verification script:

```bash
python scripts/verify_offline_models.py
```

Expected output:
```
🔍 TinyCode Offline Model Verification
============================================================
Overall Status: PASS
✅ Ollama Service: Running
✅ TinyLlama Model: Available and Functional
✅ Embedding Models: Loaded
✅ FAISS Operations: Functional
```

### Quick Tests

```bash
# Test basic agent
python example_test.py

# Test plan execution
python test_plan_execution.py

# Test safety systems
python demo_safety_systems.py
```

## Troubleshooting

### Common Issues

#### Ollama Connection Error
```bash
# Error: "Could not connect to Ollama"

# Solution 1: Start Ollama service
ollama serve

# Solution 2: Check if running
curl http://localhost:11434/api/tags

# Solution 3: Use custom host/port
export OLLAMA_HOST=localhost
export OLLAMA_PORT=11434
```

#### Model Not Found
```bash
# Error: "Model 'tinyllama' not found"

# Solution: Pull the model
ollama pull tinyllama

# Verify it's available
ollama list
```

#### Python Package Issues
```bash
# Error: "ModuleNotFoundError"

# Solution 1: Reinstall requirements
pip install --force-reinstall -r requirements.txt

# Solution 2: Check Python version
python --version  # Must be 3.8+

# Solution 3: Use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Permission Errors
```bash
# Error: "Permission denied"

# Solution 1: Fix file permissions
chmod +x scripts/*.sh

# Solution 2: Fix data directory permissions
chmod -R 755 data/

# Solution 3: Run with appropriate user
# Avoid using sudo unless necessary
```

#### Memory Issues
```bash
# Error: "Out of memory"

# Solution 1: Reduce parallel operations
export OLLAMA_NUM_PARALLEL=1

# Solution 2: Use smaller models
ollama pull tinyllama  # Instead of larger models

# Solution 3: Increase swap space (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Platform-Specific Issues

#### macOS
```bash
# SSL Certificate errors
pip install --upgrade certifi

# Xcode tools required
xcode-select --install
```

#### Windows (WSL)
```bash
# Enable WSL2
wsl --set-default-version 2

# Install in WSL environment, not Windows directly
wsl
cd /mnt/c/path/to/tinycode
```

#### Linux
```bash
# Missing system libraries
sudo apt-get install python3-dev build-essential

# FAISS installation issues
pip install faiss-cpu --no-cache-dir
```

## Environment Configuration

Create a `.env` file for custom configuration:

```bash
# Ollama settings
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=tinyllama:latest

# Safety settings
SAFETY_LEVEL=moderate
REQUIRE_CONFIRMATION=true

# Performance settings
MAX_TOKENS=2048
TEMPERATURE=0.7
OLLAMA_NUM_PARALLEL=1

# Paths
RAG_INDEX_PATH=./data/index
LOG_PATH=./logs
```

## Next Steps

After successful installation:

1. Read the [Quickstart Guide](quickstart.md) for a 5-minute introduction
2. Explore [Command Reference](../user-guide/commands.md) for available commands
3. Learn about [Operation Modes](../user-guide/modes.md)
4. Check [Workflows](../user-guide/workflows.md) for common usage patterns

## Getting Help

If you encounter issues not covered here:

1. Check the [Troubleshooting Guide](../reference/troubleshooting.md)
2. Search existing [GitHub Issues](https://github.com/davidkarpay/tinycode/issues)
3. Join the community discussion
4. Open a new issue with detailed error information