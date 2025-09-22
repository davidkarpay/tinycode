# TinyCode - AI Coding Assistant

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-orange)](https://ollama.ai)

TinyCode is a powerful, local-first AI coding assistant that combines the capabilities of TinyLlama with advanced safety features and RAG (Retrieval-Augmented Generation) for enhanced code development.

## ✨ Features

- **🔒 100% Local** - All processing happens on your machine, no external API calls
- **🎯 Three-Mode System** - Separate modes for safe exploration, planning, and execution
- **📚 RAG-Enhanced** - Document search and knowledge base integration
- **🛡️ Enterprise Safety** - Multiple protection layers with automatic backups
- **🚀 Production Ready** - REST API, Docker support, and monitoring

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Download models
ollama pull tinyllama

# Verify setup
python scripts/verify_offline_models.py

# Launch TinyCode
python tiny_code.py
```

For detailed setup instructions, see the [Installation Guide](docs/getting-started/installation.md).

## 📖 Documentation

### Getting Started
- [**Installation Guide**](docs/getting-started/installation.md) - Complete setup instructions
- [**Quickstart**](docs/getting-started/quickstart.md) - 5-minute introduction
- [**Offline Setup**](docs/getting-started/offline-setup.md) - Configure for offline use

### User Guides
- [**Command Reference**](docs/user-guide/commands.md) - All available commands
- [**Operation Modes**](docs/user-guide/modes.md) - Understanding the three-mode system
- [**Workflows**](docs/user-guide/workflows.md) - Common usage patterns
- [**Safety Features**](docs/user-guide/safety.md) - Security and protection mechanisms

### Advanced Topics
- [**RAG System**](docs/advanced/rag-system.md) - Document search and knowledge bases
- [**API Server**](docs/advanced/api-server.md) - REST API integration
- [**Plan Execution**](docs/advanced/plan-execution.md) - Understanding the plan system

### Deployment
- [**Docker Guide**](docs/deployment/docker.md) - Container deployment
- [**Production Setup**](docs/deployment/production.md) - Enterprise deployment
- [**Monitoring**](docs/deployment/monitoring.md) - Metrics and observability

## 💻 Basic Usage

### Interactive Mode

```bash
# Basic agent
python tiny_code.py

# RAG-enhanced agent
python tiny_code_rag.py

# API server
python api_server.py
```

### Three-Mode Workflow

1. **Chat Mode** (Default) - Safe exploration and questions
   ```
   /mode chat
   read file.py
   "Explain this code"
   ```

2. **Propose Mode** - Create and review execution plans
   ```
   /mode propose
   /plan "Add error handling to user authentication"
   /approve 1
   ```

3. **Execute Mode** - Run approved plans with safety checks
   ```
   /mode execute
   /execute_plan 1
   ```

## 🛡️ Safety First

TinyCode includes enterprise-grade safety features:
- Automatic backups before modifications
- Plan review and approval workflow
- Risk assessment for all operations
- Audit logging with hash-chain integrity
- Configurable safety levels (Permissive → Paranoid)

Learn more in the [Safety Guide](docs/user-guide/safety.md).

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

TinyCode is released under the MIT License. See [LICENSE](LICENSE) for details.

## 🔗 Links

- [Documentation](docs/) - Complete documentation
- [Changelog](CHANGELOG.md) - Version history
- [Issues](https://github.com/davidkarpay/tinycode/issues) - Report bugs or request features

## 🏃 Quick Commands

```bash
# Get help
help

# Change modes
/mode chat     # Safe exploration
/mode propose  # Create plans
/mode execute  # Run plans

# Create and execute a plan
/plan "Your task description"
/approve 1
/execute_plan 1

# Exit
exit
```

---

Built with ❤️ for developers who value privacy, safety, and local-first AI assistance.