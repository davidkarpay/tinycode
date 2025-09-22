# TinyCode Plugin System

A comprehensive guide to TinyCode's modular plugin architecture that enables extensible functionality while maintaining security and consistency.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Plugin Architecture](#plugin-architecture)
- [Creating Plugins](#creating-plugins)
- [Built-in Plugins](#built-in-plugins)
- [Plugin Management](#plugin-management)
- [Security and Safety](#security-and-safety)
- [Troubleshooting](#troubleshooting)

## Overview

TinyCode's plugin system provides a modular architecture that allows developers to extend functionality through self-contained plugins. The system maintains TinyCode's safety-first approach while enabling powerful extensibility.

### Key Features

- **Hot-Reload**: Plugins can be reloaded without restarting TinyCode
- **Safety Integration**: All plugin commands respect TinyCode's safety framework
- **Dependency Management**: Plugins can declare dependencies on other plugins
- **Command Registration**: Standardized command interface with metadata
- **Auto-Discovery**: Plugins are automatically discovered and can be loaded on demand

## Quick Start

### Using Existing Plugins

```bash
# List available plugins
/plugins

# Enable a plugin
/plugin-enable utilities

# Use plugin commands
/utilities hash sha256 "hello world"
/utilities uuid v4
/utilities timestamp iso

# Get plugin information
/plugin-info utilities

# Disable when done
/plugin-disable utilities
```

### Testing Plugin System

```bash
# Test plugin system functionality
python test_plugin_system.py

# Check plugin system health
/plugins
/plugin-info utilities
/utilities timestamp iso
```

## Plugin Architecture

### Core Components

#### Plugin Base Class (`PluginBase`)
All plugins inherit from the `PluginBase` abstract class:

```python
from tiny_code.plugin_system import PluginBase, PluginMetadata, PluginCommand

class MyPlugin(PluginBase):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            description="My custom plugin",
            author="Developer Name"
        )

    def initialize(self) -> bool:
        # Plugin initialization logic
        return True
```

#### Plugin Manager (`PluginManager`)
Handles plugin lifecycle management:

- **Discovery**: Scans plugin directory for available plugins
- **Loading**: Dynamically imports and instantiates plugin classes
- **Management**: Enables/disables plugins and manages dependencies
- **Execution**: Routes plugin commands to appropriate handlers

#### Plugin Commands (`PluginCommand`)
Standardized command interface:

```python
PluginCommand(
    name="my_command",
    description="Description of what the command does",
    handler=self._my_command_handler,
    safety_level=SafetyLevel.STANDARD
)
```

### Plugin Directory Structure

```
plugins/
├── __init__.py
├── plugins.json              # Plugin configuration
├── utilities.py              # Simple single-file plugin
├── code_formatter.py         # Multi-language formatter
├── web_scraper.py           # Web content extraction
└── my_complex_plugin/       # Package-style plugin
    ├── __init__.py
    ├── plugin.py
    └── utils.py
```

## Creating Plugins

### Simple Plugin Example

Create a new file `plugins/greeting.py`:

```python
"""
Greeting Plugin - Simple example plugin
"""

from tiny_code.plugin_system import PluginBase, PluginMetadata, PluginCommand
from tiny_code.safety_config import SafetyLevel

class GreetingPlugin(PluginBase):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="greeting",
            version="1.0.0",
            description="Simple greeting commands",
            author="Your Name",
            safety_level=SafetyLevel.PERMISSIVE,
            commands=["hello", "goodbye"]
        )

    def initialize(self) -> bool:
        # Register commands
        self.register_command(PluginCommand(
            name="hello",
            description="Say hello to someone",
            handler=self._hello_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        self.register_command(PluginCommand(
            name="goodbye",
            description="Say goodbye to someone",
            handler=self._goodbye_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        return True

    def _hello_command(self, name: str = "World") -> str:
        """Handle hello command"""
        return f"👋 Hello, {name}! Welcome to TinyCode!"

    def _goodbye_command(self, name: str = "Friend") -> str:
        """Handle goodbye command"""
        return f"👋 Goodbye, {name}! Thanks for using TinyCode!"
```

### Using Your Plugin

```bash
# Enable the plugin
/plugin-enable greeting

# Use the commands
/greeting hello Alice
/greeting goodbye Bob

# Get plugin info
/plugin-info greeting
```

### Advanced Plugin Features

#### Plugin with Dependencies

```python
def get_metadata(self) -> PluginMetadata:
    return PluginMetadata(
        name="advanced_plugin",
        version="1.0.0",
        description="Plugin with dependencies",
        author="Your Name",
        dependencies=["utilities"],  # Requires utilities plugin
        commands=["advanced_cmd"]
    )
```

#### Plugin with Hooks

```python
def initialize(self) -> bool:
    # Register a hook that runs before command execution
    self.register_hook(PluginHook(
        name="before_execute",
        handler=self._before_execute_hook,
        priority=75  # Higher priority = earlier execution
    ))
    return True

def _before_execute_hook(self, command: str, *args, **kwargs):
    """Hook that runs before command execution"""
    print(f"[MyPlugin] About to execute: {command}")
```

## Built-in Plugins

### Utilities Plugin

Text processing and utility functions:

```bash
# Hash generation
/utilities hash sha256 "text to hash"
/utilities hash md5 "text to hash"

# Encoding/Decoding
/utilities encode base64 "hello world"
/utilities decode base64 "aGVsbG8gd29ybGQ="

# UUID generation
/utilities uuid v4
/utilities uuid v1

# Timestamps
/utilities timestamp iso
/utilities timestamp unix
/utilities timestamp human

# Text analysis
/utilities count-lines "sample text with\nmultiple lines"

# JSON formatting
/utilities json-format '{"key":"value","nested":{"data":"here"}}'
```

### Code Formatter Plugin

Multi-language code formatting:

```bash
# Format a Python file
/code_formatter format script.py

# Check if a file needs formatting
/code_formatter check-format app.js

# List available formatters
/code_formatter list-formatters

# Format with specific formatter
/code_formatter format code.cpp clang-format
```

Supported Languages:
- Python (black, autopep8, yapf)
- JavaScript/TypeScript (prettier, eslint)
- Rust (rustfmt)
- Go (gofmt, goimports)
- C/C++ (clang-format)
- JSON, CSS, HTML (prettier)

### Web Scraper Plugin

Web content extraction and analysis:

```bash
# Scrape webpage content
/web_scraper scrape "https://example.com"

# Extract all links
/web_scraper extract-links "https://example.com"

# Download complete page
/web_scraper download-page "https://example.com" page.html

# Extract table data
/web_scraper scrape-table "https://example.com"

# Save results to file
/web_scraper scrape "https://example.com" --output content.txt
```

## Plugin Management

### Plugin Commands

```bash
# List all plugins
/plugins

# Enable specific plugin
/plugin-enable <name>

# Disable plugin
/plugin-disable <name>

# Reload plugin (for development)
/plugin-reload <name>

# Get detailed plugin information
/plugin-info <name>
```

### Plugin Configuration

The `plugins/plugins.json` file controls plugin behavior:

```json
{
  "enabled_plugins": [
    "utilities",
    "code_formatter"
  ],
  "plugin_settings": {
    "utilities": {
      "default_hash": "sha256"
    },
    "code_formatter": {
      "default_formatter": "black"
    }
  },
  "auto_load": true
}
```

### Development Workflow

1. **Create Plugin**: Write plugin code in `plugins/` directory
2. **Test Loading**: Use `/plugin-enable <name>` to test loading
3. **Test Commands**: Verify plugin commands work correctly
4. **Hot Reload**: Use `/plugin-reload <name>` during development
5. **Production**: Add to `enabled_plugins` for automatic loading

## Security and Safety

### Safety Integration

All plugin commands are integrated with TinyCode's safety framework:

- **Safety Levels**: Commands are categorized by risk level
- **Mode Restrictions**: Commands respect operation mode limitations
- **Permission Checking**: Safety permissions apply to plugin commands
- **Audit Logging**: Plugin command execution is logged

### Security Best Practices

#### For Plugin Developers

1. **Validate Input**: Always validate command arguments
2. **Handle Errors**: Use proper exception handling
3. **Respect Safety**: Use appropriate safety levels
4. **Document Commands**: Provide clear descriptions
5. **Test Thoroughly**: Validate plugin functionality

#### For Plugin Users

1. **Review Plugins**: Understand what plugins do before enabling
2. **Check Authors**: Only use plugins from trusted sources
3. **Monitor Usage**: Use `/plugin-info` to understand capabilities
4. **Disable Unused**: Disable plugins when not needed

### Safety Levels

- **PERMISSIVE**: Read-only operations, safe utilities
- **STANDARD**: Standard operations with potential side effects
- **STRICT**: Operations that modify system state
- **PARANOID**: High-risk operations requiring explicit approval

## Troubleshooting

### Common Issues

#### Plugin Not Loading

```bash
# Check if plugin file exists
/plugins

# Try manual loading with error details
/plugin-enable <name>

# Check plugin structure
/plugin-info <name>
```

#### Command Not Working

```bash
# Verify plugin is enabled
/plugins

# Check command syntax
/plugin-info <name>

# Reload plugin
/plugin-reload <name>
```

#### Development Issues

```bash
# Test plugin system
python test_plugin_system.py

# Check for Python syntax errors
python -m py_compile plugins/my_plugin.py

# Validate plugin structure
/plugin-info my_plugin
```

### Error Messages

- **Plugin not found**: Plugin file doesn't exist or isn't discoverable
- **Failed to initialize**: Error in plugin's `initialize()` method
- **Command handler error**: Exception in plugin command execution
- **Dependency missing**: Required plugin dependency not available

### Debugging Plugin Development

1. **Check Logs**: Plugin errors are logged to TinyCode's error system
2. **Use Print Statements**: Add debug output to plugin methods
3. **Test Incrementally**: Test each command as you develop
4. **Validate Metadata**: Ensure `get_metadata()` returns correct structure
5. **Check Imports**: Verify all required imports are available

## Best Practices

### Plugin Design

- **Single Responsibility**: Each plugin should have a focused purpose
- **Clear Naming**: Use descriptive command and plugin names
- **Consistent Interface**: Follow established patterns for similar operations
- **Error Handling**: Provide helpful error messages
- **Documentation**: Include docstrings and clear descriptions

### Performance

- **Lazy Loading**: Only load plugins when needed
- **Efficient Commands**: Design commands to be fast and responsive
- **Resource Cleanup**: Properly clean up resources in `shutdown()`
- **Caching**: Cache expensive operations where appropriate

### Compatibility

- **Version Checking**: Consider TinyCode version compatibility
- **Graceful Degradation**: Handle missing dependencies gracefully
- **API Stability**: Use stable APIs from TinyCode core
- **Testing**: Test with different TinyCode configurations

## See Also

- [Command Reference](../user-guide/commands.md#plugin-management-commands) - Plugin management commands
- [Architecture](../reference/architecture.md#plugin-system) - Plugin system architecture
- [System Integration](system-integration.md) - Related system capabilities
- [Error Handling](../reference/error-handling.md) - Error handling in plugins