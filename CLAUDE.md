# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Setup & Prerequisites
```bash
# Quick setup with Makefile
make quick-start   # Complete setup for new developers
make bootstrap     # Install dependencies and download models

# Manual setup
pip install -r requirements.txt
./scripts/download_models.sh
python scripts/verify_offline_models.py

# Ensure Ollama is running with TinyLlama
ollama pull tinyllama
ollama list  # Verify tinyllama:latest is available
```

### Development & Launch Modes
```bash
# Using Makefile commands
make dev           # Launch API server mode
make cli           # Launch interactive CLI mode
make rag           # Launch RAG-enhanced agent

# Direct Python commands
python tiny_code.py         # Interactive CLI mode
python tiny_code_rag.py     # RAG-enhanced agent
python api_server.py        # API server (http://localhost:8000)
```

### Testing
```bash
# Using Makefile commands
make test          # Run all basic tests
make test-coverage # Run tests with coverage
make e2e           # Run end-to-end tests
make stress        # Run stress tests

# Direct Python commands
python example_test.py
python test_plan_execution.py
python demo_safety_systems.py
python test_plugin_system.py  # Test plugin architecture

# Stress tests for security and resource limits
python run_stress_tests.py
python stress_test_security.py
python stress_test_resource_limits.py
python stress_test_edge_cases.py

# Run pytest tests
pytest
```

### Docker Deployment
```bash
# Using Makefile commands
make docker-up           # Start all Docker services
make docker-down         # Stop Docker services
make docker-logs         # View Docker logs
make docker-offline-up   # Start offline deployment

# Direct Docker commands
docker-compose -f docker/docker-compose.yml up -d
docker-compose -f docker/docker-compose.yml --profile offline up -d
docker-compose -f docker/docker-compose.yml logs -f tinyllama
```

### RAG System Operations
```bash
# Ingest documents into knowledge base
python tiny_code_rag.py ingest <path> --kb general|genetics|code

# Search knowledge base
python tiny_code_rag.py search "query" --kb general|genetics|code

# Interactive mode with RAG
python tiny_code_rag.py
# Then use: /rag "your question"
```

## Architecture

TinyCode is a Python-based AI coding assistant system with sophisticated safety features and multiple operation modes. It's designed for 100% local operation using Ollama and TinyLlama.

### Core Components

**Main Agent System** (`tiny_code/`)
- `agent.py` - Base TinyCode agent with code operations (completion, explanation, bug fixing, refactoring)
- `rag_enhanced_agent.py` - Extended agent with RAG capabilities for context-aware responses
- `ollama_client.py` - Wrapper for Ollama API communication
- `cli.py` - Enhanced CLI with mode awareness, Rich formatting, command history, and autocompletion
- `tools.py` - Advanced file system operations including glob pattern matching, grep functionality, and multi-file editing

**Three-Mode Operation System**
- `mode_manager.py` - Controls CHAT/PROPOSE/EXECUTE modes with safety boundaries
- `command_registry.py` - 40+ commands categorized by safety level and mode restrictions
- `cli_enhancements.py` - Advanced CLI features with command history, autocompletion, and usage analytics
- Mode transitions require explicit commands, preventing accidental dangerous operations

**Enhanced Capabilities Framework**
- `git_operations.py` - Comprehensive git integration with workflow automation and repository analysis
- `system_integration.py` - System monitoring, environment management, and process control
- `error_handling.py` - Robust error recovery system with automatic categorization and recovery strategies
- `self_awareness.py` - Dynamic capability discovery and introspection system
- `plugin_system.py` - Modular plugin architecture for extensibility

**Plan-Based Execution Framework**
- `plan_generator.py` - Creates detailed execution plans with risk assessment
- `plan_executor.py` - Executes approved plans with progress tracking
- `plan_validator.py` - Pre-execution validation, dangerous pattern detection
- Plans stored persistently in `data/plans/` with JSON serialization

**Safety Infrastructure**
- `safety_config.py` - Four-tier safety levels (PERMISSIVE/STANDARD/STRICT/PARANOID)
- `timeout_manager.py` - Plan and action-level timeout controls (default 5 min/30 sec)
- `audit_logger.py` - Hash-chain integrity logging with tamper detection
- `resource_monitor.py` - CPU/memory/disk monitoring with enforcement
- `rate_limiter.py` - Token bucket algorithm for API rate limiting

**RAG System** (`rag/`, `summarizer/`)
- `rag/embeddings/local_embedder.py` - Local sentence-transformers (all-MiniLM-L6-v2)
- `rag/vectorstore/faiss_store.py` - FAISS-based similarity search
- `rag/retrieval/hybrid_retriever.py` - Dense + sparse search (70/30 weighting)
- `rag/ingestion/` - Multi-format document processing (PDF, DOCX, code files)
- `summarizer/core/rag_manager.py` - Central RAG orchestration

**Genetics Specialization** (`genetics/`)
- `corpus_crawler.py` - Specialized bioinformatics documentation crawler
- Pre-configured for HTS specs, GATK, samtools, NCBI sources

**Plugin System** (`plugins/`)
- `plugin_system.py` - Core plugin management and loading infrastructure
- `utilities.py` - Text processing utilities (hash, encode/decode, UUID, timestamps)
- `code_formatter.py` - Multi-language code formatting (Python, JS, TypeScript, Rust, Go, C/C++)
- `web_scraper.py` - Web content extraction and scraping capabilities
- Hot-reloadable plugins with dependency management and safety integration

**API Server** (`api_server.py`)
- Flask-based REST API with Prometheus metrics
- Health checks, rate limiting, API key authentication
- Endpoints: /complete, /fix, /explain, /refactor, /test, /review

### Data Storage
```
data/
├── index/faiss/       # FAISS vector indexes for RAG
├── plans/             # Stored execution plans
├── backups/           # Automatic backups before risky operations
├── audit_logs/        # Hash-chain integrity logs
├── embeddings_cache/  # Cached embeddings
└── genetics_corpus/   # Downloaded genetics documentation
```

### Operation Flow

**Three-Mode Workflow:**
1. **Chat Mode** (default): Safe Q&A, read-only file access, no modifications
2. **Propose Mode**: Plan generation and review, `/plan "task"` creates execution plans
3. **Execute Mode**: Execute approved plans with full safety features

**Critical Commands for Mode Control:**
```bash
/mode chat      # Switch to safe exploration mode
/mode propose   # Switch to planning mode
/mode execute   # Switch to execution mode
/plan "task"    # Generate execution plan (in propose mode)
/approve <id>   # Approve plan for execution
/execute_plan <id>  # Execute approved plan (in execute mode)
```

**Enhanced File Operations:**
```bash
/find "*.py" --max 100        # Advanced file search with glob patterns
/grep "function" --type py    # Search file contents with filters
/tree /path/to/dir           # Directory structure visualization
/compare file1.py file2.py   # Advanced file comparison
/multi-edit pattern old new  # Multi-file find and replace
```

**Git Integration Commands:**
```bash
/git-status                  # Enhanced git status with file details
/git-log --graph            # Visual commit history
/git-branches               # Branch management and analysis
/git-workflow               # Automated workflow operations
/git-analyze                # Repository statistics and insights
```

**System Integration Commands:**
```bash
/env VAR_NAME               # Environment variable management
/processes --filter python  # Process monitoring and control
/sysinfo                    # System resource information
/monitor <pid>              # Real-time process monitoring
```

**Plugin Management Commands:**
```bash
/plugins                    # List available plugins
/plugin-enable utilities    # Enable a specific plugin
/plugin-info web_scraper    # Get detailed plugin information
/plugin-reload code_formatter # Hot-reload plugin during development
```

**Error Handling Commands:**
```bash
/errors                     # Show recent error history
/error-stats               # Error analytics and patterns
/recover TC_1234567890     # Manual error recovery by ID
```

**Safety Features:**
- Pre-execution validation scans for dangerous patterns (`rm -rf`, `DROP TABLE`, etc.)
- Automatic backups before file modifications
- Path traversal protection
- Configurable safety levels affect confirmation requirements
- Hash-chain audit logging for forensics
- Timeout controls at plan (5 min) and action (30 sec) levels

### Configuration

**RAG Configuration** (`config/rag_config.yaml`)
- Embedding model: all-MiniLM-L6-v2 (384 dimensions)
- Vector store: FAISS with adaptive indexing (IVF/HNSW/Flat)
- Chunking: 800 chars default with 100 char overlap
- Retrieval: Hybrid search with 0.7 dense / 0.3 sparse weighting

**Genetics Sources** (`config/genetics_corpus.yaml`)
- Pre-configured bioinformatics documentation sources
- Rate-limited crawling with robots.txt respect

## Documentation Structure

The project documentation is organized in the `docs/` directory:

```
docs/
├── getting-started/
│   ├── installation.md      # Complete setup guide
│   ├── quickstart.md        # 5-minute introduction
│   └── offline-setup.md     # Offline deployment
├── user-guide/
│   ├── commands.md          # Command reference
│   ├── modes.md            # Three-mode system
│   ├── workflows.md        # Usage patterns
│   └── safety.md           # Safety features
├── advanced/
│   ├── rag-system.md       # RAG architecture
│   └── plan-execution.md   # Plan system details
└── deployment/
    ├── production.md       # Production setup
    └── docker.md          # Container deployment
```

Key documentation files:
- `README.md` - Project overview with links to detailed docs
- `CONTRIBUTING.md` - Contribution guidelines
- `CHANGELOG.md` - Version history
- `LICENSE` - MIT license
- `docs/reference/troubleshooting.md` - Comprehensive troubleshooting guide

## Development Commands Summary

For convenience, TinyCode includes a Makefile with common development tasks:

```bash
make help          # Show all available commands
make quick-start   # Complete setup for new developers
make bootstrap     # Install dependencies and download models
make dev           # Start API server
make cli           # Start interactive CLI
make test          # Run tests
make docker-up     # Start Docker services
make verify        # Verify offline setup
make clean         # Clean up artifacts
```

## Enhanced Architecture Patterns

### Command Registration Pattern
TinyCode uses a centralized command registry pattern (`command_registry.py`) where all commands are categorized by:
- **Safety Level**: NONE, LOW, MEDIUM, HIGH, CRITICAL
- **Mode Availability**: Which operation modes can execute the command
- **Category**: SAFE, PLANNING, MODIFICATION, EXECUTION, SYSTEM

When adding new commands:
1. Register in `CommandRegistry._register_all_commands()`
2. Implement handler method in `TinyCodeCLI`
3. Add to the commands dictionary in `handle_command()`

### Plugin Development Pattern
Plugins extend TinyCode through a standardized interface:
1. Inherit from `PluginBase`
2. Implement `get_metadata()` returning `PluginMetadata`
3. Register commands in `initialize()` using `register_command()`
4. Commands are accessed via `/plugin_name command_name args`

Example plugin structure:
```python
class MyPlugin(PluginBase):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(name="my_plugin", version="1.0.0", ...)

    def initialize(self) -> bool:
        self.register_command(PluginCommand(...))
        return True
```

### Error Handling Integration
The system uses context managers for consistent error handling:
- `error_context()` - Wraps operations with automatic error categorization
- `ErrorRecoveryManager` - Centralized error tracking and recovery
- All commands should use `with error_context(self.error_manager, action, category)`

### CLI Enhancement Pattern
CLI features are modularized in `cli_enhancements.py`:
- Command completion via `TinyCodeCompleter`
- Usage analytics in SQLite database
- History management with intelligent suggestions
- All enhancements integrate with the main CLI loop

## Development Guidelines

### Adding New File Operations
File operations should use `AdvancedFileOperations` class in `tools.py`:
- Support glob patterns for file matching
- Include metadata (size, modified time, permissions)
- Implement proper error handling and validation
- Consider safety implications and required backups

### Extending Git Integration
Git operations are centralized in `git_operations.py`:
- Use `GitOperations` class for all git interactions
- Parse command output into structured data classes
- Handle non-git directories gracefully
- Provide both basic and advanced operation modes

### System Integration Best Practices
When adding system integration features:
- Use `psutil` for cross-platform compatibility
- Implement resource monitoring and limits
- Provide filtering and formatting options
- Consider security implications of system access

## Troubleshooting

If you encounter issues:
1. Run `make verify` to check system health
2. Check `docs/reference/troubleshooting.md` for solutions
3. Use `make health` for system diagnostics
4. Test plugin system with `python test_plugin_system.py`