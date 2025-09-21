# 🚀 TinyCode - AI Coding Assistant

> **RAG-Enhanced Coding Assistant powered by TinyLlama**
> Complete offline operation with local models and comprehensive safety features

TinyCode is an advanced AI-powered coding assistant that uses TinyLlama via Ollama with Retrieval-Augmented Generation (RAG) capabilities.

## ✨ Features

- 🤖 **Local AI Models** - Powered by Ollama and TinyLlama
- 📚 **RAG System** - Retrieval-Augmented Generation with document search
- 🛡️ **Safety First** - Multiple operation modes with confirmation prompts
- 🔄 **Three Modes** - Chat (safe), Plan (design), Code (full access)
- 🌐 **API Server** - Production-ready REST API with monitoring
- 📊 **Monitoring** - Prometheus metrics and health checks
- 🐳 **Docker Ready** - Full containerization support
- ⚡ **Offline Capable** - No internet required after setup
- **Code Completion** - Complete partial code with intelligent suggestions
- **Bug Fixing** - Identify and fix bugs in your code
- **Code Explanation** - Get clear explanations of code functionality
- **Code Refactoring** - Improve code quality and maintainability
- **Test Generation** - Automatically generate test cases
- **Code Review** - Get feedback on code quality and best practices

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai/) installed
- 4GB+ RAM recommended

### Installation

1. Clone the repository:
```bash
git clone https://github.com/davidkarpay/tinycode.git
cd tinycode
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download models:
```bash
./scripts/download_models.sh
```

4. Verify setup:
```bash
python scripts/verify_offline_models.py
```

### Legacy Installation Method

1. Ensure you have Ollama installed and running:
```bash
# Install Ollama (if not already installed)
# See https://ollama.ai for installation instructions

# Pull TinyLlama model
ollama pull tinyllama
```

2. Install Python dependencies:
```bash
pip install ollama click rich prompt_toolkit pygments
```

## 🎮 Usage

### Interactive CLI Mode
```bash
python tiny_code.py
```

### RAG-Enhanced Mode
```bash
python tiny_code_rag.py
```

### API Server Mode
```bash
python api_server.py
# Access at: http://localhost:8000
```

### Operating Modes

#### 💬 Chat Mode (Safe)
```bash
/mode chat
```
- Safe Q&A mode
- No file modifications
- Perfect for learning

#### 📋 Plan Mode (Design)
```bash
/mode plan
```
- Architecture planning
- Read-only file access
- System design

#### 💻 Code Mode (Full)
```bash
/mode code
```
- Full coding capabilities
- File read/write access
- Complete development workflow

## 📚 Documentation

- 📖 **[Super-User Guide](TINYCODER_SUPERUSER_GUIDE.md)** - Complete mastery guide
- 🎮 **[Command Reference](TINYCODER_COMMAND_CARD.md)** - Quick reference card
- 🔄 **[Workflow Guide](TINYCODER_WORKFLOWS.md)** - Visual workflow patterns
- 🛠️ **[Setup Guide](OFFLINE_SETUP_GUIDE.md)** - Offline deployment
- 🚀 **[Production Guide](PRODUCTION_DEPLOYMENT.md)** - Enterprise deployment

### Legacy Interactive Mode
This launches an interactive chat interface where you can:
- Type questions directly
- Use `/` commands for file operations
- Type `help` for available commands
- Type `exit` to quit

### Command Line Mode

#### Process a file with a specific operation:
```bash
# Explain code
python tiny_code.py process example.py --operation explain

# Fix bugs
python tiny_code.py process example.py --operation fix

# Generate tests
python tiny_code.py process example.py --operation test

# Review code
python tiny_code.py process example.py --operation review

# Refactor code
python tiny_code.py process example.py --operation refactor
```

#### Ask a quick question:
```bash
python tiny_code.py ask "What is a decorator in Python?"
```

#### Execute a Python file:
```bash
python tiny_code.py run script.py
```

## Interactive Commands

When in interactive mode, you can use these commands:

### File Operations
- `/file <path>` - Load a file for processing
- `/analyze <path>` - Analyze code structure and metrics
- `/complete <path>` - Complete incomplete code
- `/fix <path>` - Fix bugs in code
- `/explain <path>` - Get explanation of code
- `/refactor <path>` - Refactor code for improvements
- `/test <path>` - Generate test cases
- `/review <path>` - Review code quality
- `/run <path>` - Execute a Python file

### Workspace Management
- `/workspace <path>` - Set working directory
- `/list [pattern]` - List files matching pattern (default: *.py)
- `/save <path>` - Save last response to file

### Other Commands
- `help` - Show available commands
- `clear` - Clear the screen
- `exit` - Exit the program

## Examples

### Example 1: Interactive Code Help
```
$ python tiny_code.py
Welcome to Tiny Code!
Tiny Code> How do I read a CSV file in Python?
[Response with code examples and explanation]
```

### Example 2: Fix a Bug
```bash
$ python tiny_code.py process buggy_code.py --operation fix
[Fixed code with explanation]
```

### Example 3: Generate Tests
```bash
$ python tiny_code.py process my_module.py --operation test
[Generated test cases]
```

## Project Structure

```
tiny_code/
├── __init__.py          # Package initialization
├── agent.py             # Main agent logic
├── ollama_client.py     # Ollama API wrapper
├── tools.py             # Code manipulation tools
├── prompts.py           # Prompt templates
├── cli.py               # CLI interface
└── main.py              # Entry point
```

## Requirements

- Python 3.8+
- Ollama installed and running
- TinyLlama model (`ollama pull tinyllama`)

## Troubleshooting

1. **Model not found error**: Ensure you've run `ollama pull tinyllama`
2. **Connection errors**: Check that Ollama is running (`ollama serve`)
3. **Import errors**: Install all dependencies with `pip install ollama click rich prompt_toolkit pygments`

## License

MIT License - Feel free to use and modify as needed.