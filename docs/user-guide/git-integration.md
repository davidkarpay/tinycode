# Git Integration Guide

TinyCode provides comprehensive git workflow automation and repository management capabilities, enabling seamless integration with version control workflows.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Repository Analysis](#repository-analysis)
- [Branch Management](#branch-management)
- [Workflow Automation](#workflow-automation)
- [Advanced Features](#advanced-features)
- [Integration Patterns](#integration-patterns)

## Overview

TinyCode's git integration goes beyond basic git commands, providing intelligent repository analysis, workflow automation, and seamless integration with TinyCode's planning and execution system.

### Key Features

- **Repository Analysis**: Comprehensive repository statistics and insights
- **Branch Visualization**: Visual branch management and history
- **Workflow Automation**: Automated git workflows for common tasks
- **Integration**: Seamless integration with TinyCode's plan execution
- **Safety**: Git operations respect TinyCode's safety framework

## Quick Start

### Basic Git Commands

```bash
# Check repository status with enhanced details
/git-status

# View commit history with visual graph
/git-log --graph --limit 10

# Analyze repository structure
/git-info

# List all branches (local and remote)
/git-branches --remote
```

### Integration with TinyCode Workflows

```bash
# Plan with git integration
/mode propose
/plan "Add authentication feature with proper git workflow"

# Execute plan (includes automatic git operations)
/mode execute
/execute_plan 1

# Review changes
/git-status
/git-diff
```

## Repository Analysis

### Repository Information

The `/git-info` command provides comprehensive repository analysis:

```bash
/git-info
```

Output includes:
- Repository root and current directory
- Current branch and upstream tracking
- Commit statistics (total commits, contributors)
- Branch information (local/remote counts)
- Repository size and file counts
- Recent activity summary

### Detailed Statistics

```bash
# Analyze contributors
/git-analyze --contributors

# File change analysis
/git-analyze --files

# Branch analysis
/git-analyze --branches

# Commit pattern analysis
/git-analyze --activity
```

### Status Enhancement

The enhanced `/git-status` command shows:

```bash
/git-status
```

- Current branch and tracking information
- Staged, modified, and untracked files with details
- File sizes and modification times
- Merge conflicts (if any)
- Stash information
- Ahead/behind commit counts

## Branch Management

### Branch Listing and Analysis

```bash
# List local branches
/git-branches

# Include remote branches
/git-branches --remote

# Show branch relationships
/git-branches --graph

# Analyze branch activity
/git-branches --activity
```

### Branch Information

Each branch listing includes:
- Branch name and current indicator
- Last commit message and author
- Commit date and relative time
- Tracking relationship (upstream)
- Ahead/behind commit counts

### Remote Management

```bash
# List remotes
/git-remotes

# Detailed remote information
/git-remotes --verbose

# Check remote connectivity
/git-remotes --check
```

## Workflow Automation

### Automated Workflows

TinyCode provides pre-built workflows for common git patterns:

```bash
# Feature branch workflow
/git-workflow feature-branch "new-feature"

# Hotfix workflow
/git-workflow hotfix "critical-fix"

# Release workflow
/git-workflow release "v1.2.0"

# Pull request workflow
/git-workflow pull-request "feature-branch"
```

### Workflow Components

Each workflow can include:
- Branch creation and switching
- Automated commits with standardized messages
- Push operations with upstream tracking
- Merge operations with conflict detection
- Tag creation for releases

### Custom Workflow Integration

```bash
# Use git commands in plans
/mode propose
/plan "Implement user authentication with git workflow:
1. Create feature branch
2. Implement authentication
3. Add tests
4. Commit changes
5. Push branch
6. Create pull request"
```

## Advanced Features

### Commit History Analysis

```bash
# Visual commit graph
/git-log --graph

# Detailed commit information
/git-log --verbose --limit 5

# Filter by author
/git-log --author "developer@example.com"

# Filter by date range
/git-log --since "2024-01-01" --until "2024-12-31"

# Search commit messages
/git-log --grep "authentication"
```

### Diff Analysis

```bash
# View staged changes
/git-diff --staged

# Compare branches
/git-diff main..feature-branch

# View specific file changes
/git-diff HEAD~1 auth.py

# Show word-level differences
/git-diff --word-diff
```

### Stash Management

```bash
# List stashes
/git-stashes

# Detailed stash information
/git-stashes --verbose

# Apply specific stash
/git-stash apply stash@{0}

# Create stash with message
/git-stash save "Work in progress on authentication"
```

## Integration Patterns

### Development Workflow

```bash
# 1. Start new feature
/git-workflow feature-branch "user-auth"

# 2. Implement in TinyCode
/mode propose
/plan "Implement user authentication system"
/approve 1

/mode execute
/execute_plan 1

# 3. Review and commit
/git-status
/git-diff
/git-add auth.py tests/test_auth.py
/git-commit -m "Add user authentication system

- Implement JWT-based authentication
- Add password hashing
- Include comprehensive tests
- Update API documentation"

# 4. Push and create PR
/git-push --set-upstream origin user-auth
/git-workflow pull-request "user-auth"
```

### Code Review Workflow

```bash
# Check out review branch
/git-checkout review-branch

# Analyze changes
/git-diff main..review-branch
/git-log main..review-branch

# Review file changes
/review changed_file.py

# Provide feedback through TinyCode
/mode chat
"Review this authentication implementation for security best practices"
```

### Release Workflow

```bash
# Prepare release
/git-workflow release "v1.2.0"

# Update version and changelog
/mode propose
/plan "Prepare v1.2.0 release:
1. Update version numbers
2. Generate changelog
3. Update documentation
4. Create release tag"

# Execute release plan
/mode execute
/execute_plan 1

# Verify release
/git-log --oneline -10
/git-tag --list
```

### Hotfix Workflow

```bash
# Create hotfix branch
/git-workflow hotfix "security-fix"

# Quick fix implementation
/mode execute
/plan "Apply critical security fix"

# Fast-track to production
/git-add security_fix.py
/git-commit -m "SECURITY: Fix authentication bypass vulnerability"
/git-push origin hotfix/security-fix
```

## Command Reference

### Core Git Commands

| Command | Description | Options |
|---------|-------------|---------|
| `/git-status` | Enhanced status with details | - |
| `/git-log` | Commit history with graph | `--graph`, `--limit`, `--author` |
| `/git-branches` | Branch management | `--remote`, `--graph` |
| `/git-remotes` | Remote repository info | `--verbose`, `--check` |
| `/git-stashes` | Stash management | `--verbose` |
| `/git-diff` | Advanced diff viewer | `--staged`, `--word-diff` |
| `/git-info` | Repository analysis | - |
| `/git-workflow` | Automated workflows | Feature, hotfix, release |
| `/git-analyze` | Repository analytics | `--contributors`, `--files` |

### Workflow Commands

| Workflow | Description | Usage |
|----------|-------------|-------|
| `feature-branch` | Create feature branch | `/git-workflow feature-branch "name"` |
| `hotfix` | Create hotfix branch | `/git-workflow hotfix "fix-name"` |
| `release` | Prepare release | `/git-workflow release "version"` |
| `pull-request` | PR preparation | `/git-workflow pull-request "branch"` |

## Best Practices

### Repository Management

1. **Regular Status Checks**: Use `/git-status` frequently
2. **Branch Analysis**: Understand branch relationships with `/git-branches`
3. **Commit History**: Keep track of changes with `/git-log --graph`
4. **Repository Health**: Monitor with `/git-info` and `/git-analyze`

### Integration Workflow

1. **Plan with Git**: Include git operations in execution plans
2. **Safety First**: Review changes with `/git-diff` before committing
3. **Descriptive Commits**: Use TinyCode to generate meaningful commit messages
4. **Branch Strategy**: Use consistent branching with workflow automation

### Collaboration

1. **Remote Sync**: Regular `/git-remotes --check` for connectivity
2. **Conflict Resolution**: Use TinyCode's analysis for merge conflicts
3. **Code Review**: Leverage TinyCode for reviewing changes
4. **Documentation**: Keep git workflow documented in plans

## Troubleshooting

### Common Issues

```bash
# Check git configuration
/git-info

# Verify remote connectivity
/git-remotes --check

# Analyze merge conflicts
/git-status
/git-diff

# Review recent changes
/git-log --limit 5
```

### Integration Problems

```bash
# Verify TinyCode git integration
/git-status

# Check repository state
/git-info

# Validate branch configuration
/git-branches --remote
```

## See Also

- [Command Reference](commands.md#git-integration-commands) - Complete git command reference
- [Workflows](workflows.md) - Workflow patterns with git integration
- [Plan Execution](../advanced/plan-execution.md) - Planning with git operations
- [Architecture](../reference/architecture.md#git-integration) - Git integration architecture