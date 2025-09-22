# TinyCode Safety Features

TinyCode implements multiple layers of safety features to prevent accidental damage and ensure secure operation. This guide covers all safety mechanisms and how to configure them.

## Table of Contents

- [Safety Philosophy](#safety-philosophy)
- [Safety Levels](#safety-levels)
- [Protection Mechanisms](#protection-mechanisms)
- [Backup System](#backup-system)
- [Audit Logging](#audit-logging)
- [Timeout Controls](#timeout-controls)
- [Resource Monitoring](#resource-monitoring)
- [Configuration](#configuration)
- [Best Practices](#best-practices)

## Safety Philosophy

TinyCode follows a "defense in depth" approach with multiple safety layers:

1. **Mode Separation** - Isolates capabilities by operation mode
2. **Plan Review** - Requires explicit approval before execution
3. **Risk Assessment** - Automatic risk evaluation of all operations
4. **Validation** - Pre-execution checks for dangerous patterns
5. **Backups** - Automatic backups before modifications
6. **Audit Trail** - Complete logging with integrity verification
7. **Resource Limits** - Prevents runaway operations

## Safety Levels

### Overview

Four configurable safety levels balance security with usability:

| Level | Confirmations | Backups | Validation | Use Case |
|-------|--------------|---------|------------|----------|
| PERMISSIVE | Minimal | On request | Basic | Development/Testing |
| MODERATE | Medium+ risk | Automatic | Standard | Normal development |
| STRICT | All changes | Always | Enhanced | Production code |
| PARANOID | Everything | Multiple | Maximum | Critical systems |

### PERMISSIVE

**When to use**: Local development, testing, experimentation

```python
# Configuration
SAFETY_CONFIG = {
    "level": "PERMISSIVE",
    "require_confirmation": False,
    "auto_backup": False,
    "validation": "basic"
}
```

**Behavior**:
- No confirmation for low-risk operations
- Warnings only for dangerous patterns
- Manual backup creation
- Fast workflow with minimal interruption

### MODERATE (Default)

**When to use**: Standard development work

```python
# Configuration
SAFETY_CONFIG = {
    "level": "MODERATE",
    "require_confirmation": "medium",
    "auto_backup": True,
    "validation": "standard"
}
```

**Behavior**:
- Confirmation for medium and high-risk operations
- Automatic backups for file modifications
- Standard validation checks
- Balanced safety and productivity

### STRICT

**When to use**: Working on production code, important projects

```python
# Configuration
SAFETY_CONFIG = {
    "level": "STRICT",
    "require_confirmation": "low",
    "auto_backup": True,
    "validation": "enhanced",
    "audit": True
}
```

**Behavior**:
- Confirmation for all file modifications
- Automatic backups before any change
- Enhanced validation with pattern matching
- Full audit logging
- Double confirmation for deletions

### PARANOID

**When to use**: Critical systems, compliance environments

```python
# Configuration
SAFETY_CONFIG = {
    "level": "PARANOID",
    "require_confirmation": "all",
    "auto_backup": True,
    "backup_count": 3,
    "validation": "maximum",
    "audit": True,
    "hash_chain": True
}
```

**Behavior**:
- Confirmation for every operation
- Multiple backup strategies
- Maximum validation with security scanning
- Hash-chain integrity for audit logs
- Read-only mode by default
- Requires explicit unlock for modifications

## Protection Mechanisms

### Path Traversal Protection

Prevents access to system directories and parent paths:

```python
# Blocked patterns
BLOCKED_PATHS = [
    "/etc", "/usr", "/bin", "/sbin",
    "/System", "/Windows",
    "../", "/.."
]

# Example protection
"/etc/passwd" → Blocked
"../../secrets" → Blocked
"./src/main.py" → Allowed
```

### Dangerous Pattern Detection

Scans for potentially harmful patterns:

```python
DANGEROUS_PATTERNS = [
    # File operations
    "rm -rf /", "del /f /s /q",

    # Database operations
    "DROP TABLE", "DROP DATABASE",
    "TRUNCATE", "DELETE FROM",

    # Code injection
    "eval(", "exec(", "subprocess.call(",
    "__import__", "compile(",

    # Credentials
    "password=", "api_key=", "token=",

    # System modifications
    "chmod 777", "chown -R"
]
```

### File Size Limits

Prevents creation of excessively large files:

```python
FILE_LIMITS = {
    "max_file_size": 10_000_000,  # 10MB
    "max_line_length": 10_000,
    "max_lines": 100_000
}
```

### Command Restrictions

System commands are filtered and restricted:

```python
# Allowed commands
SAFE_COMMANDS = [
    "ls", "pwd", "echo", "date",
    "python", "pip list", "git status"
]

# Blocked commands
BLOCKED_COMMANDS = [
    "sudo", "su", "rm -rf",
    "format", "fdisk", "dd"
]
```

## Backup System

### Automatic Backups

Before any file modification:

```
Original: src/main.py
Backup: data/backups/2024-01-01_120000/main.py.bak
```

### Backup Structure

```
data/backups/
├── 2024-01-01_120000/          # Timestamp
│   ├── manifest.json            # Backup metadata
│   ├── main.py.bak             # Original files
│   └── config.yaml.bak
├── 2024-01-01_130000/
│   └── ...
```

### Backup Commands

```bash
# List available backups
/backup list

# Create manual backup
/backup create "Before major refactor"

# Restore from backup
/backup restore <backup_id>

# Show backup details
/backup show <backup_id>
```

### Backup Retention

```python
BACKUP_CONFIG = {
    "auto_backup": True,
    "retention_days": 30,
    "max_backups": 100,
    "compress": True
}
```

## Audit Logging

### Log Structure

Every action is logged with:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "action": "file_modify",
  "user": "current_user",
  "mode": "EXECUTE",
  "details": {
    "file": "src/main.py",
    "operation": "write",
    "lines_changed": 25
  },
  "risk_level": "MEDIUM",
  "confirmed": true,
  "hash": "sha256:abc123...",
  "previous_hash": "sha256:def456..."
}
```

### Hash Chain Integrity

Each log entry includes hash of previous entry:

```python
current_hash = sha256(
    previous_hash +
    json.dumps(current_entry)
)
```

This creates a tamper-evident chain.

### Audit Commands

```bash
# View recent audit log
/audit show

# Verify audit log integrity
/audit verify

# Export audit log
/audit export audit_report.json

# Search audit log
/audit search "file_modify"
```

### Log Location

```
data/audit_logs/
├── 2024-01-01.log
├── 2024-01-02.log
└── audit.db  # SQLite database
```

## Timeout Controls

### Plan-Level Timeouts

Maximum execution time for entire plan:

```python
TIMEOUT_CONFIG = {
    "plan_timeout": 300,  # 5 minutes
    "action_timeout": 30,  # 30 seconds per action
    "warning_threshold": 0.8  # Warn at 80% of timeout
}
```

### Action-Level Timeouts

Individual action limits:

```python
ACTION_TIMEOUTS = {
    "file_read": 5,
    "file_write": 10,
    "command_execute": 30,
    "network_request": 60
}
```

### Timeout Handling

```bash
# If timeout occurs:
⚠️ Operation timed out after 30 seconds
Rolling back changes...
✅ Rollback complete
```

## Resource Monitoring

### System Resources

Monitors and limits resource usage:

```python
RESOURCE_LIMITS = {
    "max_memory_mb": 1024,
    "max_cpu_percent": 80,
    "max_disk_io_mbps": 100,
    "max_open_files": 100
}
```

### File Handle Management

Automatic cleanup of file handles:

```python
with ResourceMonitor() as monitor:
    # Operations here
    # Automatic cleanup on exit
```

### Resource Commands

```bash
# Check current resource usage
/resource status

# Set resource limits
/resource limit memory 512

# Show resource history
/resource history
```

## Configuration

### Environment Variables

```bash
# Safety level
export SAFETY_LEVEL=strict

# Confirmations
export REQUIRE_CONFIRMATION=true
export CONFIRMATION_TIMEOUT=30

# Backups
export AUTO_BACKUP=true
export BACKUP_PATH=./data/backups

# Audit
export AUDIT_ENABLED=true
export AUDIT_PATH=./data/audit_logs

# Timeouts
export PLAN_TIMEOUT=300
export ACTION_TIMEOUT=30
```

### Configuration File

Create `config/safety.yaml`:

```yaml
safety:
  level: strict
  confirmation:
    require: true
    timeout: 30

backup:
  automatic: true
  path: ./data/backups
  retention_days: 30
  compression: true

audit:
  enabled: true
  path: ./data/audit_logs
  hash_chain: true
  export_format: json

validation:
  dangerous_patterns: true
  path_traversal: true
  file_size_limit: 10MB

timeouts:
  plan: 300
  action: 30
  network: 60

resources:
  max_memory: 1024MB
  max_cpu: 80
  max_files: 100
```

### Runtime Configuration

```bash
# Check current configuration
/config show

# Update configuration
/config set safety.level paranoid

# Reset to defaults
/config reset
```

## Best Practices

### 1. Choose Appropriate Safety Level

- **Development**: PERMISSIVE or MODERATE
- **Staging**: STRICT
- **Production**: STRICT or PARANOID
- **Learning**: PARANOID

### 2. Regular Backups

Even with automatic backups:
```bash
# Before major changes
git commit -m "Before TinyCode refactoring"
/backup create "Manual backup before refactor"
```

### 3. Review Audit Logs

Regularly check for unusual activity:
```bash
/audit show --last 100
/audit verify
```

### 4. Test in Safe Mode First

```bash
# Test changes in Chat mode
/mode chat
"What would happen if we refactored this?"

# Then plan
/mode propose
/plan "Refactor as discussed"
```

### 5. Use Version Control

```bash
# Always commit before major operations
git add .
git commit -m "Before AI-assisted modifications"
```

### 6. Set Resource Limits

For long-running operations:
```bash
/resource limit memory 512
/timeout set plan 600
```

### 7. Enable Audit Trail

For compliance and debugging:
```bash
export AUDIT_ENABLED=true
export AUDIT_HASH_CHAIN=true
```

## Emergency Procedures

### Stopping Runaway Operations

```bash
# Interrupt with Ctrl+C
^C
Operation interrupted!
Rolling back...

# Kill specific process
/process kill <pid>
```

### Recovery from Errors

```bash
# Check recent backups
/backup list --recent 5

# Restore specific backup
/backup restore <backup_id>

# Manual recovery
cp data/backups/latest/*.bak ./src/
```

### Integrity Verification

```bash
# Verify audit log hasn't been tampered
/audit verify

# Check file integrity
/integrity check src/

# Verify backup integrity
/backup verify <backup_id>
```

## Safety Indicators

### Visual Cues

The interface provides visual safety indicators:

- 🟢 **Green**: Safe operation (Chat mode)
- 🟡 **Yellow**: Caution required (Propose mode)
- 🔴 **Red**: Dangerous operation (Execute mode)
- ⚠️ **Warning**: Risk detected
- 🛡️ **Shield**: Safety feature active

### Status Messages

```
✅ Safe mode active
⚠️ Medium risk operation - confirmation required
🛡️ Backup created: backup_001
🔒 Audit logging enabled
⏱️ Timeout: 30s remaining
```

## Compliance Features

### SOC 2 Compliance

- Audit trails with integrity verification
- Access controls via mode system
- Automatic backup and recovery
- Resource monitoring and limits

### GDPR Compliance

- No external data transmission
- Local processing only
- Audit log export capabilities
- Data retention controls

### Industry Standards

- ISO 27001 security controls
- NIST cybersecurity framework alignment
- OWASP secure coding practices

## See Also

- [Modes Guide](modes.md) - Understanding operation modes
- [Backup and Recovery](../reference/troubleshooting.md#backup-and-recovery)
- [Audit System](../advanced/plan-execution.md#plan-storage)
- [Configuration Reference](../reference/configuration.md)