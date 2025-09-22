# Plan-Based Execution System

This document provides a deep dive into TinyCode's plan-based execution framework, explaining how plans are generated, validated, and executed.

## Overview

The plan-based execution system is a core safety feature that ensures all modifications go through a review process before execution.

## Plan Lifecycle

```
Generate → Validate → Review → Approve → Execute → Audit
```

### 1. Plan Generation

Plans are created in Propose mode using the `/plan` command:

```python
# Plan structure
{
    "id": "plan_20240101_120000",
    "description": "User-provided task description",
    "created_at": "2024-01-01T12:00:00Z",
    "status": "pending",
    "risk_level": "MEDIUM",
    "steps": [...],
    "validation": {...},
    "metadata": {...}
}
```

### 2. Risk Assessment

Each plan is automatically assessed for risk:

| Risk Level | Criteria | Examples |
|------------|----------|----------|
| LOW | Read-only, simple creates | Creating new files, adding functions |
| MEDIUM | Modifications, refactoring | Updating existing code, changing configs |
| HIGH | Deletions, system changes | Removing files, database operations |
| CRITICAL | Security, production impact | Auth changes, API modifications |

### 3. Plan Validation

Before approval, plans go through validation:

- **Syntax Validation**: Ensures valid Python/code syntax
- **Path Validation**: Checks for path traversal attempts
- **Pattern Scanning**: Detects dangerous patterns
- **Dependency Check**: Verifies required files exist
- **Permission Check**: Ensures write access to targets

### 4. Plan Execution

Execution happens in stages with checkpoints:

```python
for step in plan.steps:
    # Pre-execution
    create_backup(step.target)
    validate_step(step)

    # Execution
    with timeout(step.timeout):
        result = execute_step(step)

    # Post-execution
    verify_result(result)
    log_audit(step, result)

    # Checkpoint
    if step.checkpoint:
        confirm_continuation()
```

## Plan Components

### Step Types

| Type | Description | Risk |
|------|-------------|------|
| `create_file` | Create new file | LOW |
| `modify_file` | Edit existing file | MEDIUM |
| `delete_file` | Remove file | HIGH |
| `execute_command` | Run system command | HIGH |
| `refactor_code` | Restructure code | MEDIUM |
| `install_package` | Add dependency | MEDIUM |

### Step Structure

```json
{
    "type": "modify_file",
    "target": "src/main.py",
    "action": "add_function",
    "content": "def new_feature():\n    pass",
    "line_range": [50, 55],
    "validation": {
        "syntax_check": true,
        "test_after": true
    },
    "rollback": {
        "enabled": true,
        "backup_id": "bak_001"
    }
}
```

## Safety Mechanisms

### Pre-Execution Checks

1. **File Existence**: Verify targets exist
2. **Write Permissions**: Check file access
3. **Syntax Validation**: Ensure valid code
4. **Dependency Resolution**: Check imports
5. **Resource Availability**: Memory/disk space

### During Execution

1. **Timeout Control**: Prevent hanging operations
2. **Resource Monitoring**: Track CPU/memory
3. **Progress Tracking**: Show step completion
4. **Error Handling**: Graceful failure recovery
5. **Checkpoint System**: Pause at critical points

### Post-Execution

1. **Result Verification**: Check expected outcomes
2. **Test Execution**: Run associated tests
3. **Audit Logging**: Record all actions
4. **Metrics Collection**: Performance data
5. **Notification**: Report completion status

## Rollback System

### Automatic Rollback Triggers

- Execution failure
- Validation error
- Timeout exceeded
- Resource limit hit
- User cancellation

### Rollback Process

```python
def rollback_plan(plan_id):
    # 1. Stop execution
    halt_execution()

    # 2. Identify affected files
    affected = get_affected_files(plan_id)

    # 3. Restore from backups
    for file in affected:
        restore_backup(file)

    # 4. Clean up artifacts
    cleanup_temp_files()

    # 5. Update status
    update_plan_status(plan_id, "rolled_back")

    # 6. Log rollback
    audit_log_rollback(plan_id)
```

## Plan Storage

Plans are stored persistently for history and audit:

```
data/plans/
├── active/           # Currently executing
├── pending/          # Awaiting approval
├── completed/        # Successfully executed
├── failed/           # Failed execution
└── archived/         # Old plans
```

### Plan Metadata

```json
{
    "execution": {
        "started": "2024-01-01T12:00:00Z",
        "completed": "2024-01-01T12:05:00Z",
        "duration": 300,
        "steps_completed": 10,
        "steps_total": 10
    },
    "resources": {
        "files_created": 2,
        "files_modified": 5,
        "files_deleted": 0,
        "lines_added": 150,
        "lines_removed": 30
    },
    "validation": {
        "pre_checks": "passed",
        "post_checks": "passed",
        "tests_run": 15,
        "tests_passed": 15
    }
}
```

## Configuration

### Plan Executor Settings

```yaml
plan_executor:
  max_plan_size: 100         # Maximum steps
  default_timeout: 300       # 5 minutes
  checkpoint_interval: 10    # Every 10 steps
  parallel_execution: false  # Sequential by default

validation:
  syntax_check: true
  security_scan: true
  dependency_check: true

rollback:
  automatic: true
  keep_backups: 30          # Days
  compress: true
```

## Advanced Features

### Parallel Execution

For independent steps:

```python
if plan.parallel_safe:
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(execute_step, step)
                  for step in plan.parallel_steps]
        results = [f.result() for f in futures]
```

### Plan Templates

Reusable plan patterns:

```python
TEMPLATES = {
    "add_crud_endpoints": {...},
    "refactor_to_pattern": {...},
    "add_testing_suite": {...}
}
```

### Plan Composition

Combining multiple plans:

```python
composite_plan = Plan.compose([
    plan_add_feature,
    plan_add_tests,
    plan_update_docs
])
```

## Monitoring and Metrics

### Key Metrics

- Plan generation time
- Approval rate
- Execution success rate
- Average execution time
- Rollback frequency
- Resource usage per plan

### Dashboards

```python
# Prometheus metrics
plan_executions_total
plan_execution_duration_seconds
plan_rollbacks_total
plan_steps_completed_total
```

## Best Practices

1. **Keep Plans Focused**: One feature per plan
2. **Use Checkpoints**: For long-running plans
3. **Test First**: Include test steps in plans
4. **Document Changes**: Add comments in code
5. **Version Control**: Commit before major plans
6. **Review Carefully**: Especially HIGH/CRITICAL risk
7. **Monitor Execution**: Watch for issues
8. **Learn from Failures**: Review failed plans

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Plan timeout | Complex operations | Increase timeout |
| Validation failure | Syntax errors | Review code changes |
| Rollback failed | Missing backup | Manual recovery |
| Resource exceeded | Large operations | Split into smaller plans |

## API Reference

### Plan Management

```python
# Create plan
plan = PlanGenerator.create(description, context)

# Validate plan
validator = PlanValidator()
validation_result = validator.validate(plan)

# Execute plan
executor = PlanExecutor(safety_config)
result = executor.execute(plan)

# Rollback plan
executor.rollback(plan_id)
```

## See Also

- [Operation Modes](../user-guide/modes.md)
- [Safety Features](../user-guide/safety.md)
- [Command Reference](../user-guide/commands.md#plan-execution-commands)