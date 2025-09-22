# TinyCode Operation Modes

TinyCode implements a three-mode operation system designed to provide safety boundaries while maintaining powerful capabilities. This guide explains each mode in detail.

## Table of Contents

- [Overview](#overview)
- [Chat Mode](#chat-mode)
- [Propose Mode](#propose-mode)
- [Execute Mode](#execute-mode)
- [Mode Transitions](#mode-transitions)
- [Safety Levels](#safety-levels)
- [Best Practices](#best-practices)

## Overview

The three-mode system separates exploration, planning, and execution to prevent accidental modifications and ensure deliberate, safe operations.

```
┌─────────────┐    /mode propose    ┌─────────────┐    /approve     ┌─────────────┐
│ CHAT MODE   │ ──────────────────> │ PROPOSE     │ ─────────────> │ EXECUTE     │
│ (Read-only) │                     │ (Planning)  │                │ (Changes)   │
│ - Safe Q&A  │ <────────────────── │ - Generate  │ <───────────── │ - Run plans │
│ - Analysis  │    /mode chat       │   plans     │   /mode chat   │ - Backups   │
└─────────────┘                     └─────────────┘                └─────────────┘
```

## Chat Mode

### Purpose
Chat Mode is the default, safest mode for exploration and learning. It's designed for:
- Asking questions about code
- Reading and analyzing files
- Understanding system architecture
- Getting coding help
- Exploring without risk

### Capabilities
✅ **Can do:**
- Read files and directories
- Analyze code structure
- Answer coding questions
- Explain concepts
- Search documentation
- Provide recommendations

❌ **Cannot do:**
- Modify any files
- Create new files
- Delete content
- Execute system commands
- Make any permanent changes

### Commands Available
- All read-only file operations (`read`, `ls`, `cat`)
- Analysis commands (`/analyze`, `/explain`)
- Search and query operations
- Help and documentation access
- Mode switching (`/mode propose`, `/mode execute`)

### Use Cases
```bash
# Ask about best practices
"What's the best way to handle errors in Python?"

# Analyze existing code
read main.py
"Are there any security issues in this code?"

# Explore project structure
ls src/
tree

# Get implementation ideas
"How would you implement a rate limiter?"
```

### Example Session
```bash
$ python tiny_code.py
> /mode status
Current mode: CHAT (Safe exploration mode)

> read config.py
[File contents displayed]

> "What does this configuration do?"
[Explanation provided]

> "How can I improve this?"
[Suggestions provided without modifications]
```

## Propose Mode

### Purpose
Propose Mode is for planning and designing changes before implementation. It allows you to:
- Generate detailed execution plans
- Review proposed changes
- Assess risk levels
- Approve or reject plans
- Design architecture

### Capabilities
✅ **Can do:**
- Create execution plans
- Review existing plans
- Approve/reject plans
- Read files for context
- Design solutions
- Estimate complexity

❌ **Cannot do:**
- Execute plans directly
- Modify files
- Run system commands
- Make permanent changes

### Commands Available
- `/plan "<task>"` - Generate new plan
- `/list_plans` - Show all plans
- `/show_plan <id>` - View plan details
- `/approve <id>` - Approve plan for execution
- `/reject <id>` - Reject plan
- `/plan_status <id>` - Check plan status
- All read-only operations from Chat Mode

### Plan Structure
Generated plans include:
```json
{
  "id": "plan_001",
  "description": "Add user authentication",
  "risk_level": "MEDIUM",
  "steps": [
    {
      "action": "create_file",
      "file": "auth.py",
      "description": "Create authentication module"
    }
  ],
  "safety_checks": ["backup", "validation"],
  "estimated_time": "5 minutes"
}
```

### Risk Levels
Plans are automatically assessed for risk:
- **LOW**: Simple file creations, safe modifications
- **MEDIUM**: Multiple file changes, refactoring
- **HIGH**: Deletions, system changes
- **CRITICAL**: Database operations, security changes

### Example Session
```bash
> /mode propose
Switched to PROPOSE mode

> /plan "Add error handling to user registration"
Plan generated: ID=1
Risk Level: MEDIUM
Steps: 4

> /show_plan 1
[Detailed plan displayed]

> /approve 1
Plan 1 approved for execution

> /mode execute
Switched to EXECUTE mode
```

## Execute Mode

### Purpose
Execute Mode is where approved plans are actually implemented. This mode has full capabilities but includes extensive safety features.

### Capabilities
✅ **Can do:**
- Execute approved plans
- Create and modify files
- Run system commands (with limits)
- Perform refactoring
- Install dependencies
- Make permanent changes

⚠️ **With safety checks:**
- Automatic backups before modifications
- Validation of changes
- Timeout controls
- Resource monitoring
- Audit logging

### Commands Available
- `/execute_plan <id>` - Run approved plan
- `/rollback <id>` - Rollback executed plan
- `/backup list` - Show available backups
- `/backup restore <id>` - Restore from backup
- All file modification operations
- System commands (restricted)

### Safety Features

#### Automatic Backups
```bash
Before modification:
- Original: src/main.py
- Backup: data/backups/2024-01-01_12-00-00/main.py.bak
```

#### Validation Checks
- Path traversal protection
- Dangerous pattern detection
- File size limits
- System path restrictions

#### Audit Logging
Every action is logged with:
- Timestamp
- Action type
- Files affected
- User confirmation
- Hash chain integrity

### Example Session
```bash
> /mode execute
Switched to EXECUTE mode
⚠️ Warning: This mode can modify files

> /execute_plan 1
Executing plan: "Add error handling"
Step 1/4: Creating backup...
Step 2/4: Modifying registration.py...
Step 3/4: Adding error_handler.py...
Step 4/4: Updating tests...
✅ Plan executed successfully

> /backup list
Available backups:
1. 2024-01-01_12-00-00 (Plan 1 execution)

# If something goes wrong:
> /rollback 1
Rolling back plan 1...
✅ Rollback complete
```

## Mode Transitions

### Allowed Transitions
```
Chat → Propose → Execute
Chat ← Propose ← Execute
Chat → Execute (with warning)
```

### Transition Commands
```bash
# From any mode to Chat (safest)
/mode chat

# From Chat to planning
/mode propose

# From Propose to execution
/mode execute

# Check current mode
/mode status
```

### Transition Warnings
When switching to more powerful modes, you'll see warnings:
```
⚠️ Switching to EXECUTE mode
This mode can modify files and run commands.
Continue? (y/n):
```

## Safety Levels

TinyCode supports four configurable safety levels that affect all modes:

### PERMISSIVE
- Minimal confirmations
- Warnings only
- Fast workflow
- Best for: Development, testing

### MODERATE (Default)
- Confirmation for medium+ risk
- Basic validation
- Balanced workflow
- Best for: Standard development

### STRICT
- Confirmation for all changes
- Enhanced validation
- Automatic backups
- Best for: Production code

### PARANOID
- Confirmation for everything
- Maximum validation
- Full audit trail
- Best for: Critical systems

### Setting Safety Level
```bash
# Check current level
/safety status

# Change level
/safety set strict

# Via environment variable
export SAFETY_LEVEL=paranoid
```

## Best Practices

### 1. Start in Chat Mode
Always begin sessions in Chat Mode to understand the codebase before making changes.

### 2. Plan Before Executing
Use Propose Mode to review changes before implementation:
```bash
/mode propose
/plan "Your detailed task description"
/show_plan 1
# Review carefully
/approve 1
```

### 3. Be Specific in Plans
Provide detailed descriptions for better plans:
- ❌ "Fix bug"
- ✅ "Fix null reference error in auth.py line 45 when user email is undefined"

### 4. Review Risk Assessments
Always check the risk level before approving:
```bash
/show_plan 1
# Look for: "risk_level": "HIGH"
```

### 5. Use Appropriate Safety Levels
- Development: PERMISSIVE or MODERATE
- Staging: STRICT
- Production: PARANOID

### 6. Maintain Backups
Even with automatic backups, maintain version control:
```bash
git commit -m "Before TinyCode modifications"
```

### 7. Progressive Enhancement
Start with small changes and gradually increase complexity:
1. Read and understand
2. Make small modification
3. Test changes
4. Proceed with larger modifications

## Mode Comparison Table

| Feature | Chat | Propose | Execute |
|---------|------|---------|---------|
| Read files | ✅ | ✅ | ✅ |
| Analyze code | ✅ | ✅ | ✅ |
| Create plans | ❌ | ✅ | ❌ |
| Approve plans | ❌ | ✅ | ❌ |
| Modify files | ❌ | ❌ | ✅ |
| Create files | ❌ | ❌ | ✅ |
| Delete files | ❌ | ❌ | ✅* |
| Run commands | ❌ | ❌ | ✅* |
| Automatic backups | N/A | N/A | ✅ |
| Risk assessment | N/A | ✅ | ✅ |

*With safety restrictions and confirmations

## Common Workflows

### Research → Plan → Execute
```bash
# 1. Research in Chat Mode
/mode chat
read existing_code.py
"What patterns are used here?"

# 2. Plan in Propose Mode
/mode propose
/plan "Refactor to use the same patterns for consistency"

# 3. Execute after review
/approve 1
/mode execute
/execute_plan 1
```

### Quick Fix Workflow
```bash
# For low-risk changes
/mode propose
/plan "Fix typo in README.md"
/approve 1
/mode execute
/execute_plan 1
/mode chat  # Return to safety
```

### Experimental Workflow
```bash
# When trying new things
/mode propose
/plan "Experimental: Try new authentication method"
# Review carefully
/show_plan 1
# Create backup first
/mode execute
/backup create "Before experiment"
/execute_plan 1
# Easy rollback if needed
/rollback 1
```

## See Also

- [Command Reference](commands.md) - All available commands
- [Safety Features](safety.md) - Detailed safety mechanisms
- [Workflows](workflows.md) - Common usage patterns
- [Plan Execution](../advanced/plan-execution.md) - Deep dive into plan system