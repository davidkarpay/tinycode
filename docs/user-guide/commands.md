# TinyCode Command Reference

This comprehensive guide covers all commands available in TinyCode across different modes and contexts.

## Table of Contents

- [Launch Commands](#launch-commands)
- [Mode Commands](#mode-commands)
- [File Operations](#file-operations)
- [RAG Commands](#rag-commands)
- [Git Integration Commands](#git-integration-commands)
- [System Integration Commands](#system-integration-commands)
- [Plugin Management Commands](#plugin-management-commands)
- [Error Handling Commands](#error-handling-commands)
- [System Commands](#system-commands)
- [Plan Execution Commands](#plan-execution-commands)
- [Safety Commands](#safety-commands)

## Launch Commands

Start TinyCode in different modes from the command line:

```bash
# Interactive CLI mode - basic agent
python tiny_code.py

# RAG-enhanced mode - includes document search and knowledge base
python tiny_code_rag.py

# API server mode - REST API for integration
python api_server.py
```

## Mode Commands

TinyCode operates in three distinct modes with different capabilities:

| Command | Mode | Description | Capabilities |
|---------|------|-------------|--------------|
| `/mode chat` | Chat Mode | Safe Q&A mode (default) | Read-only file access, no modifications |
| `/mode propose` | Propose Mode | Planning and design | Create and review execution plans |
| `/mode execute` | Execute Mode | Full execution | Run approved plans with safety checks |
| `/mode status` | Any | Show current mode | Display active mode and permissions |
| `/mode help` | Any | Mode information | Detailed help about modes |

### Mode Transitions

```
Chat Mode → Propose Mode → Execute Mode
     ↑           ↓              ↓
     ←───────────────────────────
```

## File Operations

### Basic File Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/file <path>` | Load file for processing | `/file main.py` |
| `/analyze <file>` | Analyze code structure | `/analyze main.py` |
| `/complete <file>` | Complete incomplete code | `/complete draft.py` |
| `/fix <file>` | Fix bugs in code | `/fix buggy.py` |
| `/explain <file>` | Explain code functionality | `/explain complex.py` |
| `/refactor <file>` | Refactor code | `/refactor legacy.py` |
| `/test <file>` | Generate test cases | `/test module.py` |
| `/review <file>` | Review code quality | `/review feature.py` |
| `/run <file>` | Execute Python code | `/run script.py` |
| `/save <path>` | Save last response to file | `/save output.txt` |
| `/workspace <path>` | Set working directory | `/workspace /home/user/project` |
| `/list [pattern]` | List files matching pattern | `/list *.py` |

### Enhanced File Operations

| Command | Description | Example |
|---------|-------------|---------|
| `/find <pattern>` | Advanced file search with glob patterns | `/find "*.py" --max 100` |
| `/grep <pattern>` | Search file contents with filters | `/grep "function" --type py` |
| `/tree [path]` | Directory structure visualization | `/tree /path/to/project` |
| `/compare <file1> <file2>` | Advanced file comparison | `/compare old.py new.py` |
| `/multi-edit <pattern> <old> <new>` | Multi-file find and replace | `/multi-edit "*.js" "var " "const "` |
| `/dirstat [path]` | Directory analysis and statistics | `/dirstat /home/user/project` |

#### Find Command Options
- `--max N` - Limit results to N files
- `--type ext` - Filter by file extension
- `--size +1M` - Filter by file size
- `--hidden` - Include hidden files

#### Grep Command Options
- `--type ext` - Search only specific file types
- `--ignore-case` - Case-insensitive search
- `--context N` - Show N lines of context
- `--line-numbers` - Show line numbers

## RAG Commands

Commands available in RAG-enhanced mode for knowledge base operations:

| Command | Description | Example |
|---------|-------------|---------|
| `/ingest <path>` | Add documents to knowledge base | `/ingest docs/` |
| `/rag <question>` | Ask questions using RAG | `/rag "How to implement OAuth?"` |
| `/summarize <file>` | Summarize document | `/summarize report.pdf` |
| `/chat <question>` | Chat with documents using RAG | `/chat "Explain VCF format"` |
| `/genetics <concept>` | Explain genetics concept | `/genetics "coordinate systems"` |
| `/knowledge <base>` | Switch knowledge base | `/knowledge genetics` |
| `/rag_stats` | Show RAG system statistics | `/rag_stats` |
| `/setup_genetics` | Initialize genetics corpus | `/setup_genetics` |

### Knowledge Base Types
- `general` - General documentation
- `code` - Code-specific knowledge
- `genetics` - Bioinformatics documentation

## Git Integration Commands

Comprehensive git workflow automation and repository management:

| Command | Description | Example |
|---------|-------------|---------|
| `/git-status` | Enhanced git status with file details | `/git-status` |
| `/git-log` | Visual commit history | `/git-log --graph --limit 10` |
| `/git-branches` | Branch management and analysis | `/git-branches --remote` |
| `/git-remotes` | Remote repository information | `/git-remotes` |
| `/git-stashes` | Stash management | `/git-stashes` |
| `/git-diff` | Advanced diff with formatting | `/git-diff --staged` |
| `/git-info` | Complete repository analysis | `/git-info` |
| `/git-workflow` | Automated git workflows | `/git-workflow feature-branch` |
| `/git-analyze` | Repository statistics and insights | `/git-analyze --contributors` |

### Git Command Options
- `--graph` - Show visual branch graph
- `--limit N` - Limit number of results
- `--remote` - Include remote branches
- `--staged` - Show staged changes only
- `--contributors` - Analyze contributor statistics

## System Integration Commands

System monitoring, process management, and environment control:

| Command | Description | Example |
|---------|-------------|---------|
| `/env [var]` | Environment variable management | `/env PATH` |
| `/processes` | Process monitoring and control | `/processes --filter python` |
| `/sysinfo` | System resource information | `/sysinfo` |
| `/netstat` | Network connection status | `/netstat --listening` |
| `/kill <pid>` | Terminate process by ID | `/kill 1234` |
| `/exec <command>` | Execute system command | `/exec ls -la` |
| `/monitor <pid>` | Real-time process monitoring | `/monitor 5678` |

### System Command Options
- `--filter term` - Filter results by term
- `--listening` - Show only listening ports
- `--tree` - Show process tree
- `--usage` - Show resource usage

## Plugin Management Commands

Manage and interact with the modular plugin system:

| Command | Description | Example |
|---------|-------------|---------|
| `/plugins` | List all available plugins | `/plugins` |
| `/plugin-enable <name>` | Enable a specific plugin | `/plugin-enable utilities` |
| `/plugin-disable <name>` | Disable a plugin | `/plugin-disable web_scraper` |
| `/plugin-reload <name>` | Hot-reload plugin for development | `/plugin-reload code_formatter` |
| `/plugin-info <name>` | Show detailed plugin information | `/plugin-info utilities` |

### Plugin Commands by Plugin

#### Utilities Plugin Commands
- `/utilities hash sha256 "text"` - Generate hash
- `/utilities encode base64 "text"` - Encode text
- `/utilities uuid v4` - Generate UUID
- `/utilities timestamp iso` - Get timestamp

#### Code Formatter Plugin Commands
- `/code_formatter format file.py` - Format code file
- `/code_formatter check-format file.js` - Check formatting
- `/code_formatter list-formatters` - Show available formatters

#### Web Scraper Plugin Commands
- `/web_scraper scrape "https://example.com"` - Scrape webpage
- `/web_scraper extract-links "https://example.com"` - Extract links
- `/web_scraper scrape-table "https://example.com"` - Extract tables

## Error Handling Commands

Robust error recovery and analytics system:

| Command | Description | Example |
|---------|-------------|---------|
| `/errors` | Show recent error history | `/errors --limit 10` |
| `/error-stats` | Error analytics and patterns | `/error-stats --category USER_INPUT` |
| `/recover <id>` | Manual error recovery by ID | `/recover TC_1234567890` |

### Error Command Options
- `--limit N` - Limit number of errors shown
- `--category type` - Filter by error category
- `--severity level` - Filter by severity level

## System Commands

General system and configuration commands:

| Command | Description |
|---------|-------------|
| `help` | Show all available commands |
| `clear` | Clear the screen |
| `exit` | Exit the application |
| `/mode <mode>` | Switch operation modes |
| `/workspace <path>` | Set working directory |
| `/save <path>` | Save last response to file |
| `/list [pattern]` | List files matching pattern |

## Plan Execution Commands

Commands for the plan-based execution system (Propose/Execute modes):

| Command | Mode | Description |
|---------|------|-------------|
| `/plan "<task>"` | Propose | Generate execution plan |
| `/list_plans` | Any | List all plans |
| `/show_plan <id>` | Any | Show plan details |
| `/preview <id>` | Propose | Preview planned changes |
| `/approve <id>` | Propose | Approve plan for execution |
| `/reject <id>` | Propose | Reject plan |
| `/execute_plan <id>` | Execute | Execute approved plan |

### Plan Workflow Example

```bash
# 1. Switch to propose mode
/mode propose

# 2. Generate a plan
/plan "Add user authentication to the API"

# 3. Review the plan
/show_plan 1

# 4. Approve if satisfied
/approve 1

# 5. Switch to execute mode
/mode execute

# 6. Execute the plan
/execute_plan 1
```

## Safety Commands

Safety-related commands (implementation varies by actual safety system):

| Command | Description |
|---------|-------------|
| `/mode status` | Show current mode and safety level |
| `help` | Show available commands for current mode |

**Note**: Advanced safety commands like audit logging, backup management, and resource monitoring are handled automatically by the system. Use `/mode status` to check current safety configuration.

## Command Line Options

When running scripts from the command line:

### Basic Operations
```bash
# Process a file with specific operation
python tiny_code.py process <file> --operation <op>
# Operations: explain, fix, test, review, refactor, complete

# Ask a quick question
python tiny_code.py ask "What is a decorator?"

# Execute a Python file
python tiny_code.py run script.py
```

### RAG Operations
```bash
# Ingest documents
python tiny_code_rag.py ingest <path> --kb <type>

# Search knowledge base
python tiny_code_rag.py search "query" --kb <type>

# Summarize document
python tiny_code_rag.py summarize <file> --type extractive --length 300

# Ask questions
python tiny_code_rag.py ask "question" --kb <type>

# Setup genetics corpus
python tiny_code_rag.py setup-genetics --max-pages 50
```

## Environment Variables

Configure TinyCode behavior through environment variables:

```bash
# Ollama configuration
export OLLAMA_MODEL=tinyllama:latest
export OLLAMA_HOST=localhost
export OLLAMA_PORT=11434

# Safety configuration
export SAFETY_LEVEL=moderate
export REQUIRE_CONFIRMATION=true

# RAG configuration
export RAG_INDEX_PATH=./data/index
export EMBEDDING_MODEL=all-MiniLM-L6-v2

# Performance tuning
export OLLAMA_NUM_PARALLEL=1
export MAX_TOKENS=2048
export TEMPERATURE=0.7
```

## Keyboard Shortcuts

When in interactive mode:

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | Exit application |
| `Ctrl+L` | Clear screen |
| `Tab` | Auto-complete commands |
| `↑/↓` | Navigate command history |

## Power Prompts

Effective prompt templates for common tasks:

### Code Generation
- "Create a Python class for [PURPOSE] with [FEATURES]"
- "Write a REST API endpoint for [OPERATION]"
- "Generate unit tests for [MODULE]"
- "Build a database schema for [DOMAIN]"

### Code Analysis
- "Review this code for security issues"
- "Analyze performance bottlenecks"
- "Check for best practices compliance"
- "Find potential bugs and fixes"

### Documentation
- "Generate API documentation for [MODULE]"
- "Create README for this project"
- "Add inline documentation to this code"
- "Write user guide for [FEATURE]"

### Optimization
- "Optimize this code for performance"
- "Refactor for better maintainability"
- "Add error handling to this function"
- "Implement caching strategy"

## Command Chaining

You can chain commands for complex workflows:

```bash
# Example: Complete development cycle with enhanced features
/mode propose
/plan "Implement user authentication with git integration"
/approve 1
/mode execute
/execute_plan 1
/test auth.py
/review auth.py
/git-add auth.py
/git-commit -m "Add user authentication"

# Example: Enhanced file operations workflow
/find "*.py" --max 50
/grep "TODO" --type py --line-numbers
/multi-edit "*.py" "TODO:" "FIXME:"
/git-status
/git-diff

# Example: System monitoring workflow
/processes --filter python
/sysinfo
/monitor 1234
/env PYTHON_PATH

# Example: Plugin development workflow
/plugin-info utilities
/utilities hash sha256 "test"
/plugin-reload utilities
/plugins
```

## Troubleshooting Commands

### Check System Health
```bash
# Verify Ollama connection
curl http://localhost:11434/api/tags

# Check model availability
ollama list

# Verify offline models
python scripts/verify_offline_models.py

# Test plugin system
python test_plugin_system.py

# Test enhanced features
/sysinfo
/git-info
/plugins
/errors --limit 5

# Test RAG system
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Enhanced Troubleshooting
```bash
# Check error logs and recovery
/errors --severity HIGH
/error-stats
/recover TC_1234567890

# Monitor system resources
/processes --filter ollama
/sysinfo
/monitor <ollama_pid>

# Validate git integration
/git-status
/git-info
/git-branches

# Test plugin functionality
/plugin-info utilities
/utilities timestamp iso
/plugin-reload utilities
```

### Performance Optimization
```bash
# Monitor system resources
htop

# Optimize Ollama
export OLLAMA_NUM_PARALLEL=1

# Clear model cache
rm -rf ~/.ollama/models/.cache

# Check disk space
df -h data/
```

## See Also

- [Modes Guide](modes.md) - Detailed explanation of the three-mode system
- [Git Integration](git-integration.md) - Advanced git workflow automation
- [Workflows](workflows.md) - Common workflow patterns including enhanced features
- [Safety Features](safety.md) - Understanding safety mechanisms
- [Plugin System](../advanced/plugin-system.md) - Plugin development and management
- [System Integration](../advanced/system-integration.md) - System monitoring and management
- [Error Handling](../reference/error-handling.md) - Error recovery and analytics
- [RAG System](../advanced/rag-system.md) - Deep dive into RAG capabilities