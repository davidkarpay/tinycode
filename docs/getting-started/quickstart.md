# TinyCode Quickstart Guide

Get up and running with TinyCode in 5 minutes! This guide assumes you've already installed TinyCode following the [Installation Guide](installation.md).

## Your First Session

### 1. Start TinyCode

Open a terminal and launch TinyCode:

```bash
python tiny_code.py
```

You'll see:
```
Welcome to Tiny Code!
Your AI coding assistant powered by TinyLlama
Type 'help' for commands, '/mode help' for mode info, 'exit' to quit
```

### 2. Understand the Three Modes

TinyCode operates in three modes for safety and control:

- **Chat Mode** (default) - Safe exploration, read-only
- **Propose Mode** - Create and review plans
- **Execute Mode** - Run approved plans

Check your current mode:
```
/mode status
```

### 3. Try Basic Commands

#### Ask a coding question:
```
How do I read a JSON file in Python?
```

#### Read a file:
```
read README.md
```

#### List directory contents:
```
ls
```

### 4. Generate Your First Code

Switch to propose mode and create a plan:

```
/mode propose
/plan "Create a simple Python function to calculate fibonacci numbers"
```

Review the generated plan:
```
/show_plan 1
```

If satisfied, approve it:
```
/approve 1
```

Switch to execute mode and run:
```
/mode execute
/execute_plan 1
```

## Essential Workflows

### Workflow 1: Analyze Existing Code

```bash
# Start in chat mode (safe exploration)
read main.py
"Explain what this code does"
"Are there any potential bugs?"
```

### Workflow 2: Fix a Bug

```bash
/mode propose
/plan "Fix the authentication bug in auth.py"
/show_plan 1
/approve 1
/mode execute
/execute_plan 1
```

### Workflow 3: Add New Feature

```bash
/mode propose
/plan "Add logging functionality to the application"
# Review the plan carefully
/approve 1
/mode execute
/execute_plan 1
```

## Key Commands to Remember

| Purpose | Command | Example |
|---------|---------|---------|
| Get help | `help` | `help` |
| Change mode | `/mode <mode>` | `/mode propose` |
| Create plan | `/plan "<task>"` | `/plan "Add error handling"` |
| List plans | `/list_plans` | `/list_plans` |
| Execute plan | `/execute_plan <id>` | `/execute_plan 1` |
| Read file | `read <file>` | `read config.py` |
| Exit | `exit` | `exit` |

## Safety First

TinyCode includes multiple safety features:

1. **Mode Separation** - Can't accidentally modify files in chat mode
2. **Plan Review** - Always review plans before execution
3. **Automatic Backups** - Creates backups before risky operations
4. **Confirmation Prompts** - Requires confirmation for dangerous actions

## Using RAG Mode

For enhanced capabilities with document search:

```bash
# Launch RAG-enhanced mode
python tiny_code_rag.py

# Add documents to knowledge base
/ingest docs/

# Search for information
/search "authentication patterns"

# Ask questions using RAG
/rag "How should I implement user authentication?"
```

## Tips for Success

### 1. Start Safe
Always begin in chat mode to explore and understand before making changes.

### 2. Use Descriptive Plans
Be specific when creating plans:
- ❌ Bad: "Fix the bug"
- ✅ Good: "Fix the null pointer exception in user_auth.py line 45"

### 3. Review Before Execution
Always review plans with `/show_plan` before approving.

### 4. Keep Context
Reference previous work in your session:
```
"Based on the function we just created, add error handling"
```

### 5. Use the Right Mode
- **Chat**: Questions, exploration, analysis
- **Propose**: Planning changes, reviewing approach
- **Execute**: Running approved plans

## Common Tasks

### Generate a Function
```
/mode propose
/plan "Create a Python function to validate email addresses with regex"
/approve 1
/mode execute
/execute_plan 1
```

### Add Tests
```
/mode propose
/plan "Generate unit tests for the validation functions in validators.py"
/approve 1
/mode execute
/execute_plan 1
```

### Refactor Code
```
/mode propose
/plan "Refactor database.py to use connection pooling for better performance"
/show_plan 1
# Review carefully
/approve 1
/mode execute
/execute_plan 1
```

### Document Code
```
/mode propose
/plan "Add comprehensive docstrings to all functions in api.py"
/approve 1
/mode execute
/execute_plan 1
```

## Troubleshooting Quick Fixes

### Issue: "Model not found"
```bash
# In another terminal:
ollama pull tinyllama
```

### Issue: "Cannot connect to Ollama"
```bash
# In another terminal:
ollama serve
```

### Issue: "Command not allowed in this mode"
```bash
# Check current mode
/mode status
# Switch to appropriate mode
/mode propose  # or /mode execute
```

## What's Next?

Now that you've completed the quickstart:

1. **Learn More Commands**: See [Command Reference](../user-guide/commands.md)
2. **Understand Modes**: Read [Modes Guide](../user-guide/modes.md)
3. **Advanced Workflows**: Explore [Workflows](../user-guide/workflows.md)
4. **RAG System**: Learn about [RAG capabilities](../advanced/rag-system.md)
5. **Safety Features**: Understand [Safety Configuration](../user-guide/safety.md)

## Getting Help

- Type `help` in TinyCode for command list
- Type `/mode help` for mode information
- Check [Troubleshooting Guide](../reference/troubleshooting.md)
- Visit [GitHub Issues](https://github.com/davidkarpay/tinycode/issues)

## Quick Reference Card

```
┌─────────────────────────────────────────┐
│          TINYCODE QUICK REFERENCE        │
├─────────────────────────────────────────┤
│ Modes:                                   │
│   /mode chat     - Safe exploration     │
│   /mode propose  - Create plans         │
│   /mode execute  - Run plans            │
│                                          │
│ Essential Commands:                      │
│   help          - Show commands         │
│   read <file>   - Read file             │
│   /plan "task"  - Create plan           │
│   /approve <id> - Approve plan          │
│   /execute_plan - Execute plan          │
│   exit          - Quit                  │
│                                          │
│ Remember: Start safe, plan first!       │
└─────────────────────────────────────────┘
```

Ready to start coding with AI assistance? Launch TinyCode and begin exploring!