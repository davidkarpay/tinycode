# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

### 🚀 Essential Commands for New Claude Instances
```bash
# 1. Check system status first
ollama list                          # Verify TinyLlama is available
python tiny_code_rag.py search "test" --kb code  # Test RAG system

# 2. Start interactive mode (default: Chat mode - safe exploration)
python tiny_code_rag.py

# 3. Essential interactive commands
/mode status                         # Check current mode and permissions
/mode propose                        # Switch to plan generation mode
/plan "your development request"     # Generate execution plan
/approve <plan_id>                   # Approve plan for execution
/mode execute                        # Switch to execution mode
/execute_plan <plan_id>              # Execute approved plan
```

### 🔄 Three-Mode Workflow (CRITICAL for Claude instances)
```
┌─────────────┐    /mode propose    ┌─────────────┐    /approve     ┌─────────────┐
│ CHAT MODE   │ ──────────────────> │ PROPOSE     │ ─────────────> │ EXECUTE     │
│ (Read-only) │                     │ (Planning)  │                │ (Changes)   │
│ - Safe Q&A  │ <────────────────── │ - Generate  │ <───────────── │ - Run plans │
│ - Analysis  │    /mode chat       │   plans     │   /mode chat   │ - Backups   │
└─────────────┘                     │ - Review    │                │ - Auditing  │
                                     └─────────────┘                └─────────────┘
```

### ⚠️ Critical Safety Rules for Claude
1. **NEVER** make file changes in Chat mode
2. **ALWAYS** generate plans in Propose mode before executing
3. **VERIFY** safety level before approving high-risk plans
4. **CHECK** backup creation before destructive operations

## Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Launch RAG-enhanced agent (interactive mode with three operation modes)
python tiny_code_rag.py

# Launch basic agent (interactive mode)
python tiny_code.py
```

### Three-Mode Operation System
```bash
# Start in Chat mode (default) - safe exploration and Q&A only
python tiny_code_rag.py
# In interactive mode:
/mode chat      # Switch to Chat mode (read-only)
/mode propose   # Switch to Propose mode (plan generation and review)
/mode execute   # Switch to Execute mode (execute approved plans)
/mode status    # Show current mode and available commands
```

### Plan-Based Execution (Propose → Execute Workflow)
```bash
# In Propose mode - generate execution plans
/plan "Create a Python script to calculate fibonacci numbers"
/list_plans              # List all plans
/show_plan <plan_id>     # Show plan details
/approve <plan_id>       # Approve plan for execution
/reject <plan_id>        # Reject plan

# In Execute mode - run approved plans
/execute_plan <plan_id>  # Execute an approved plan with safety checks
```

### RAG System Operations
```bash
# Ingest documents into knowledge base
python tiny_code_rag.py ingest <path> --kb general|genetics|code

# Search knowledge base
python tiny_code_rag.py search "query" --kb general|genetics|code

# Summarize documents
python tiny_code_rag.py summarize <file> --type extractive --length 300

# Ask questions using RAG
python tiny_code_rag.py ask "question" --kb general|genetics|code

# Set up genetics knowledge base (one-time setup)
python tiny_code_rag.py setup-genetics --max-pages 50
```

### Testing and Demonstration
```bash
# Test basic agent functionality
python example_test.py

# Test complete plan execution workflow
python test_plan_execution.py

# Demonstrate enhanced safety systems
python demo_safety_systems.py

# Test RAG system components individually
python -c "from tiny_code.rag_enhanced_agent import RAGEnhancedTinyCodeAgent; agent = RAGEnhancedTinyCodeAgent(); print('RAG system initialized')"
```

### Prerequisites
```bash
# Ensure Ollama is running with TinyLlama
ollama pull tinyllama
ollama list  # Verify tinyllama:latest is available
```

## Architecture

This is a local-first AI coding assistant system built around TinyLlama with optional RAG (Retrieval-Augmented Generation) capabilities and a sophisticated three-mode operation system with enterprise-grade safety features.

### Core Components

**TinyCode Agent** (`tiny_code/agent.py`)
- Main AI coding assistant powered by TinyLlama via Ollama
- Provides code completion, explanation, bug fixing, refactoring, test generation
- Uses structured prompts for consistent responses
- Maintains conversation context and workspace awareness

**RAG-Enhanced Agent** (`tiny_code/rag_enhanced_agent.py`)
- Extends TinyCode Agent with RAG capabilities
- Integrates document search, summarization, and context-aware responses
- Provides genetics-specific coding assistance

**Three-Mode Operation System**
- **Mode Manager** (`tiny_code/mode_manager.py`) - Controls operation modes (CHAT/PROPOSE/EXECUTE)
- **Command Registry** (`tiny_code/command_registry.py`) - Categorizes 31 commands by safety level and mode permissions
- Mode-aware CLI with command filtering and Rich-formatted interfaces

**Plan-Based Execution System**
- **Plan Generator** (`tiny_code/plan_generator.py`) - Creates detailed execution plans with risk assessment
- **Plan Executor** (`tiny_code/plan_executor.py`) - Executes approved plans with comprehensive safety features
- **Plan Validator** (`tiny_code/plan_validator.py`) - Pre-execution validation and security scanning
- Persistent plan storage with JSON serialization and status tracking

**Enhanced Safety Systems**
- **Safety Configuration** (`tiny_code/safety_config.py`) - Four-tier safety levels (PERMISSIVE → PARANOID)
- **Timeout Manager** (`tiny_code/timeout_manager.py`) - Plan and action-level timeout controls
- **Audit Logger** (`tiny_code/audit_logger.py`) - Hash-chain integrity logging with tamper detection
- Automatic backup creation, rollback capabilities, and path security validation

**Foundation Components**
- **Ollama Client** (`tiny_code/ollama_client.py`) - Abstraction layer for Ollama API communication
- **Code Tools** (`tiny_code/tools.py`) - File system operations and code analysis
- **CLI Interface** (`tiny_code/cli.py`) - Enhanced command-line interface with mode awareness

### RAG Infrastructure

**RAG Manager** (`summarizer/core/rag_manager.py`)
- Central coordinator for all RAG operations
- Manages knowledge bases (general, genetics, code)
- Handles document ingestion and retrieval orchestration
- Auto-loads existing knowledge bases on startup

**Embedding System** (`rag/embeddings/local_embedder.py`)
- Local sentence-transformers (all-MiniLM-L6-v2)
- Disk-based caching for embedding reuse
- Batch processing with progress tracking

**Vector Store** (`rag/vectorstore/faiss_store.py`)
- FAISS-based similarity search with adaptive indexing
- Supports IVF, HNSW, and Flat index types
- Automatically switches index types based on dataset size
- Persistent storage with metadata

**Hybrid Retrieval** (`rag/retrieval/hybrid_retriever.py`)
- Combines dense embeddings with BM25 sparse search
- Configurable weighting (default: 70% dense, 30% sparse)
- Score normalization and metadata filtering

**Document Processing** (`rag/ingestion/`)
- Multi-format support: PDF, DOCX, PPTX, Excel, HTML, Markdown, code files
- Intelligent text chunking with overlap
- Metadata extraction and preservation

**Genetics Corpus** (`genetics/corpus_crawler.py`)
- Specialized crawler for bioinformatics documentation
- Pre-configured sources: HTS specs, GATK, samtools, NCBI, etc.
- Respects robots.txt and implements rate limiting

### Configuration System

**RAG Config** (`config/rag_config.yaml`)
- Embedding model settings (dimension, batch size, caching)
- Vector store configuration (index type, metrics, clustering)
- Chunking strategies (size, overlap, semantic/code-aware)
- Retrieval parameters (hybrid weighting, top-k, BM25 settings)
- LLM settings (model, temperature, timeouts)

**Genetics Sources** (`config/genetics_corpus.yaml`)
- Curated bioinformatics documentation sources
- Priority-based crawling with allow/deny patterns
- Quality filters and metadata extraction rules

### CLI Interface

**Enhanced CLI** (`tiny_code_rag.py`)
- Click-based command structure for all operations
- Interactive mode with command history and auto-completion
- Handles both RAG and basic coding operations
- Rich-formatted output with progress indicators

### Operation Flow

**Three-Mode Workflow**:
1. **Chat Mode**: User questions → Agent → Read-only responses (no file modifications)
2. **Propose Mode**: User request → Plan Generator → Detailed execution plan → User approval/rejection
3. **Execute Mode**: Approved plan → Plan Validator → Safety Checks → Plan Executor → Secure execution with backups

**Plan Execution Pipeline**:
1. **Validation**: Plan Validator scans for security issues, path validation, content analysis
2. **Safety Checks**: Safety Config enforces limits, Timeout Manager sets controls
3. **Execution**: Plan Executor runs actions with progress tracking and audit logging
4. **Backup & Rollback**: Automatic backup creation with rollback capabilities on failure

**RAG Data Flow**:
1. **Document Ingestion**: Files → Loader → Chunker → Embedder → Vector Store
2. **Knowledge Base Storage**: FAISS indexes + metadata stored in `data/index/faiss/`
3. **Search Process**: Query → Embedder → Hybrid Retriever → Results
4. **RAG Response**: Query + Retrieved Context → TinyLlama → Enhanced Response

### Key Design Principles

- **100% Local**: No external API dependencies, all processing on-device
- **Safety-First Architecture**: Multiple security layers with configurable risk tolerance
- **Plan-Based Execution**: Review → Approve → Execute workflow for all file modifications
- **Comprehensive Auditing**: Tamper-evident logging with hash chain integrity
- **Mode Isolation**: Clear separation between safe exploration and execution modes
- **Genetics-Focused**: Pre-configured for bioinformatics workflows
- **Persistent Storage**: Knowledge bases and execution plans auto-load between sessions
- **Enterprise Security**: Four-tier safety levels, timeout controls, and validation systems

### Security Features

- **Pre-execution validation** with dangerous pattern detection
- **Path traversal protection** and system path restrictions
- **Execution timeouts** at plan and action levels
- **Automatic backups** with rollback capabilities
- **Audit logging** with hash chain integrity verification
- **Configurable safety levels** (PERMISSIVE → PARANOID)
- **Command categorization** with 31 commands across 5 safety categories

#### 🔒 Detailed Security Examples

**Dangerous Pattern Detection:**
```python
# These patterns trigger HIGH/CRITICAL risk flags:
"rm -rf /", "sudo rm", "format", "delete *"
"DROP TABLE", "TRUNCATE", "chmod 777"
"eval()", "exec()", "subprocess.call(user_input)"
```

**Safety Level Guide:**
- **PERMISSIVE**: Development/testing (warnings only)
- **MODERATE**: Standard development (confirmation for medium+ risk)
- **STRICT**: Production-like (confirmation for low+ risk, backups required)
- **PARANOID**: Maximum security (confirmation for everything, full auditing)

**Rollback Procedures:**
1. Plans automatically create timestamped backups in `data/backups/`
2. On failure: `/rollback <execution_id>` restores from backup
3. Audit logs provide complete change history for forensics
4. Hash chain validation ensures backup integrity

**Command Risk Categories:**
```bash
# NONE (always allowed): help, status, list, show
# LOW (minimal checks): read, search, analyze
# MEDIUM (confirmation in strict+): create, modify basic files
# HIGH (backup + confirmation): refactor, install, configure
# CRITICAL (full validation): delete, execute shell, system changes
```

## 📚 Step-by-Step Tutorials

### Tutorial 1: First-Time Setup for Claude Instances
```bash
# 1. Verify prerequisites
ollama list | grep tinyllama        # Should show tinyllama:latest
python --version                    # Should be 3.8+

# 2. Test basic functionality
python tiny_code_rag.py search "test" --kb code
python tiny_code_rag.py

# 3. In interactive mode - verify modes work
/mode status                        # Check current mode
/mode propose                       # Test mode switching
/mode chat                          # Return to safe mode
```

### Tutorial 2: Safe Development Workflow
```bash
# 1. Start in Chat mode (default) - analyze first
python tiny_code_rag.py
> /rag "existing code structure"    # Understand codebase
> /analyze existing_file.py         # Review current code

# 2. Switch to Propose mode - plan changes
> /mode propose
> /plan "Add error handling to user input validation"
> /list_plans                       # Review generated plan
> /show_plan <plan_id>              # Examine details

# 3. Approve if safe, then execute
> /approve <plan_id>                # Mark plan as approved
> /mode execute                     # Switch to execution mode
> /execute_plan <plan_id>           # Run with safety checks
```

### Tutorial 3: Working with RAG System
```bash
# 1. Ingest project documentation
python tiny_code_rag.py ingest README.md --kb general
python tiny_code_rag.py ingest src/ --kb code

# 2. Use RAG for development decisions
python tiny_code_rag.py ask "How should I structure error handling?" --kb code
python tiny_code_rag.py search "authentication patterns" --kb general

# 3. Get genetics-specific help (if applicable)
python tiny_code_rag.py setup-genetics --max-pages 30
python tiny_code_rag.py ask "SAM file parsing best practices" --kb genetics
```

## 🔧 Environment Validation Checklist

### Pre-Flight Check for Claude Instances
```bash
# ✅ System Requirements
python --version                    # Must be 3.8+
pip list | grep -E "(faiss|sentence-transformers|rich|click)"

# ✅ Ollama Setup
ollama list                         # Verify TinyLlama available
ollama run tinyllama "test"         # Quick functionality test

# ✅ RAG System Health
python tiny_code_rag.py search "test" --kb code  # Should return results
ls data/index/faiss/               # Should show code_index, general_index

# ✅ Mode System Test
python -c "from tiny_code.mode_manager import ModeManager; print('✅ Mode system ready')"
```

### Common Setup Issues & Solutions
| Issue | Symptoms | Solution |
|-------|----------|----------|
| Missing TinyLlama | "Model not found" | `ollama pull tinyllama` |
| Permission errors | "Cannot write to data/" | `chmod 755 data/` or run from project root |
| Import errors | "ModuleNotFoundError" | `pip install -r requirements.txt` |
| Empty knowledge base | "No relevant documents" | Run ingestion first |
| Mode switching fails | "Command not allowed" | Check current mode with `/mode status` |

## 🚀 Advanced Usage Patterns

### Pattern 1: Multi-Step Development Project
```bash
# Step 1: Research and plan
/mode chat
/rag "project requirements and constraints"
/analyze existing_codebase/

# Step 2: Generate comprehensive plan
/mode propose
/plan "Implement user authentication with JWT tokens, including login/logout routes, middleware, and tests"
/show_plan <id>  # Review automatically generated sub-tasks

# Step 3: Execute with safety
/approve <id>
/mode execute
/execute_plan <id>  # Runs with backups and progress tracking
```

### Pattern 2: High-Risk Operations
```bash
# For operations involving deletions, refactoring, or system changes
/mode propose
/plan "Refactor database schema and migrate existing data"
# System automatically detects HIGH/CRITICAL risk patterns
# Plan requires explicit confirmation and backup creation
/show_plan <id>  # Review risk assessment and safety measures
/approve <id>    # Only after careful review
/mode execute
/execute_plan <id>  # Executes with full safety protocol
```

### Pattern 3: Knowledge Base Optimization
```bash
# Build comprehensive knowledge base for better RAG responses
python tiny_code_rag.py ingest docs/ --kb general
python tiny_code_rag.py ingest src/ --kb code
python tiny_code_rag.py ingest tests/ --kb code
python tiny_code_rag.py setup-genetics --max-pages 50  # If applicable

# Test knowledge quality
python tiny_code_rag.py search "error handling patterns" --kb code
python tiny_code_rag.py ask "What testing frameworks are used?" --kb general
```

### Pattern 4: Plan Templates for Common Tasks
```bash
# File Creation Template
/plan "Create [filename] with [functionality] including error handling and tests"

# Refactoring Template
/plan "Refactor [component] to improve [specific aspect] while maintaining backward compatibility"

# Integration Template
/plan "Integrate [library/service] with existing [system] including configuration and tests"
```

### Known Issues

- Interactive mode requires terminal input (CLI commands work in all environments)
- Large document sets may require memory optimization via config adjustments
- Initial genetics corpus setup can take 10-30 minutes depending on source availability
- Plan execution in Execute mode assumes approval for immediate changes