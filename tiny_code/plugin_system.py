"""
Plugin System for TinyCode

Provides a modular plugin architecture that allows dynamic loading and management
of extensions to enhance TinyCode's capabilities.
"""

import os
import sys
import json
import importlib
import importlib.util
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import inspect
import traceback
from datetime import datetime

from .safety_config import SafetyLevel


@dataclass
class PluginMetadata:
    """Metadata for a plugin"""
    name: str
    version: str
    description: str
    author: str
    requires_tinyllama: bool = True
    safety_level: SafetyLevel = SafetyLevel.STANDARD
    dependencies: List[str] = None
    hooks: List[str] = None
    commands: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.hooks is None:
            self.hooks = []
        if self.commands is None:
            self.commands = []


@dataclass
class PluginCommand:
    """Command provided by a plugin"""
    name: str
    description: str
    handler: Callable
    safety_level: SafetyLevel
    requires_mode: Optional[str] = None
    category: str = "plugin"


@dataclass
class PluginHook:
    """Hook provided by a plugin"""
    name: str
    handler: Callable
    priority: int = 50  # 0-100, higher = earlier execution


class PluginBase(ABC):
    """Base class for all TinyCode plugins"""

    def __init__(self, agent=None):
        self.agent = agent
        self.enabled = True
        self._commands = {}
        self._hooks = {}

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        return True

    def shutdown(self):
        """Clean up plugin resources"""
        pass

    def register_command(self, command: PluginCommand):
        """Register a command with the plugin"""
        self._commands[command.name] = command

    def register_hook(self, hook: PluginHook):
        """Register a hook with the plugin"""
        if hook.name not in self._hooks:
            self._hooks[hook.name] = []
        self._hooks[hook.name].append(hook)

    def get_commands(self) -> Dict[str, PluginCommand]:
        """Get all commands provided by this plugin"""
        return self._commands.copy()

    def get_hooks(self) -> Dict[str, List[PluginHook]]:
        """Get all hooks provided by this plugin"""
        return self._hooks.copy()


class PluginManager:
    """Manages loading, unloading, and execution of plugins"""

    def __init__(self, agent=None, plugin_dir: str = "plugins"):
        self.agent = agent
        self.plugin_dir = Path(plugin_dir)
        self.loaded_plugins: Dict[str, PluginBase] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.enabled_plugins: set = set()
        self.command_registry: Dict[str, PluginCommand] = {}
        self.hook_registry: Dict[str, List[PluginHook]] = {}

        # Create plugin directory if it doesn't exist
        self.plugin_dir.mkdir(exist_ok=True)

        # Load plugin configuration
        self.config_file = self.plugin_dir / "plugins.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load plugin configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load plugin config: {e}")

        return {
            "enabled_plugins": [],
            "plugin_settings": {},
            "auto_load": True
        }

    def _save_config(self):
        """Save plugin configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save plugin config: {e}")

    def discover_plugins(self) -> List[str]:
        """Discover available plugins in the plugin directory"""
        plugins = []

        for item in self.plugin_dir.iterdir():
            if item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
                plugins.append(item.stem)
            elif item.is_dir() and (item / '__init__.py').exists():
                plugins.append(item.name)

        return plugins

    def load_plugin(self, plugin_name: str, enable: bool = True) -> bool:
        """Load a plugin by name"""
        try:
            # Check if already loaded
            if plugin_name in self.loaded_plugins:
                return True

            # Try to import the plugin module
            plugin_path = self.plugin_dir / f"{plugin_name}.py"
            package_path = self.plugin_dir / plugin_name / "__init__.py"

            if plugin_path.exists():
                # Single file plugin
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            elif package_path.exists():
                # Package plugin
                spec = importlib.util.spec_from_file_location(
                    plugin_name,
                    package_path
                )
            else:
                print(f"Plugin {plugin_name} not found")
                return False

            if spec is None or spec.loader is None:
                print(f"Failed to create spec for plugin {plugin_name}")
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, PluginBase) and
                    obj != PluginBase):
                    plugin_class = obj
                    break

            if plugin_class is None:
                print(f"No plugin class found in {plugin_name}")
                return False

            # Instantiate the plugin
            plugin_instance = plugin_class(self.agent)
            metadata = plugin_instance.get_metadata()

            # Check dependencies
            for dep in metadata.dependencies:
                if dep not in self.loaded_plugins and not self.load_plugin(dep, False):
                    print(f"Failed to load dependency {dep} for plugin {plugin_name}")
                    return False

            # Initialize the plugin
            if not plugin_instance.initialize():
                print(f"Failed to initialize plugin {plugin_name}")
                return False

            # Register the plugin
            self.loaded_plugins[plugin_name] = plugin_instance
            self.plugin_metadata[plugin_name] = metadata

            # Register commands and hooks
            self._register_plugin_components(plugin_name, plugin_instance)

            if enable:
                self.enable_plugin(plugin_name)

            print(f"Successfully loaded plugin: {plugin_name}")
            return True

        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")
            traceback.print_exc()
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        try:
            if plugin_name not in self.loaded_plugins:
                return True

            # Disable first
            self.disable_plugin(plugin_name)

            # Shutdown the plugin
            plugin = self.loaded_plugins[plugin_name]
            plugin.shutdown()

            # Unregister commands and hooks
            self._unregister_plugin_components(plugin_name)

            # Remove from loaded plugins
            del self.loaded_plugins[plugin_name]
            del self.plugin_metadata[plugin_name]

            print(f"Successfully unloaded plugin: {plugin_name}")
            return True

        except Exception as e:
            print(f"Error unloading plugin {plugin_name}: {e}")
            return False

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a loaded plugin"""
        if plugin_name not in self.loaded_plugins:
            return False

        self.enabled_plugins.add(plugin_name)
        self.loaded_plugins[plugin_name].enabled = True

        # Update config
        if plugin_name not in self.config["enabled_plugins"]:
            self.config["enabled_plugins"].append(plugin_name)
            self._save_config()

        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        if plugin_name in self.enabled_plugins:
            self.enabled_plugins.remove(plugin_name)

        if plugin_name in self.loaded_plugins:
            self.loaded_plugins[plugin_name].enabled = False

        # Update config
        if plugin_name in self.config["enabled_plugins"]:
            self.config["enabled_plugins"].remove(plugin_name)
            self._save_config()

        return True

    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin"""
        enabled = plugin_name in self.enabled_plugins

        if not self.unload_plugin(plugin_name):
            return False

        return self.load_plugin(plugin_name, enabled)

    def _register_plugin_components(self, plugin_name: str, plugin: PluginBase):
        """Register commands and hooks from a plugin"""
        # Register commands
        for cmd_name, command in plugin.get_commands().items():
            full_name = f"{plugin_name}:{cmd_name}"
            self.command_registry[full_name] = command

        # Register hooks
        for hook_name, hooks in plugin.get_hooks().items():
            if hook_name not in self.hook_registry:
                self.hook_registry[hook_name] = []

            for hook in hooks:
                # Add plugin name to hook for tracking
                hook.plugin_name = plugin_name
                self.hook_registry[hook_name].append(hook)

            # Sort hooks by priority (higher priority first)
            self.hook_registry[hook_name].sort(key=lambda h: h.priority, reverse=True)

    def _unregister_plugin_components(self, plugin_name: str):
        """Unregister commands and hooks from a plugin"""
        # Unregister commands
        to_remove = [name for name in self.command_registry
                    if name.startswith(f"{plugin_name}:")]
        for name in to_remove:
            del self.command_registry[name]

        # Unregister hooks
        for hook_name, hooks in self.hook_registry.items():
            self.hook_registry[hook_name] = [
                h for h in hooks if getattr(h, 'plugin_name', '') != plugin_name
            ]

    def execute_command(self, command_name: str, *args, **kwargs) -> Any:
        """Execute a plugin command"""
        if command_name not in self.command_registry:
            raise ValueError(f"Command {command_name} not found")

        command = self.command_registry[command_name]
        plugin_name = command_name.split(':')[0]

        if plugin_name not in self.enabled_plugins:
            raise ValueError(f"Plugin {plugin_name} is not enabled")

        return command.handler(*args, **kwargs)

    def execute_hooks(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all hooks for a given hook name"""
        results = []

        if hook_name not in self.hook_registry:
            return results

        for hook in self.hook_registry[hook_name]:
            plugin_name = getattr(hook, 'plugin_name', '')

            if plugin_name and plugin_name not in self.enabled_plugins:
                continue

            try:
                result = hook.handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Error executing hook {hook_name} from {plugin_name}: {e}")

        return results

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a plugin"""
        if plugin_name not in self.plugin_metadata:
            return None

        metadata = self.plugin_metadata[plugin_name]
        return {
            **asdict(metadata),
            "loaded": plugin_name in self.loaded_plugins,
            "enabled": plugin_name in self.enabled_plugins,
            "commands": list(self.loaded_plugins[plugin_name].get_commands().keys())
                       if plugin_name in self.loaded_plugins else [],
            "hooks": list(self.loaded_plugins[plugin_name].get_hooks().keys())
                    if plugin_name in self.loaded_plugins else []
        }

    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all discovered plugins with their status"""
        discovered = self.discover_plugins()
        result = {}

        for plugin_name in discovered:
            if plugin_name in self.plugin_metadata:
                result[plugin_name] = self.get_plugin_info(plugin_name)
            else:
                result[plugin_name] = {
                    "loaded": False,
                    "enabled": False,
                    "discovered": True
                }

        return result

    def auto_load_plugins(self):
        """Auto-load plugins based on configuration"""
        if not self.config.get("auto_load", True):
            return

        for plugin_name in self.config.get("enabled_plugins", []):
            if plugin_name not in self.loaded_plugins:
                self.load_plugin(plugin_name, True)


# Example plugin template
class ExamplePlugin(PluginBase):
    """Example plugin demonstrating the plugin interface"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="example",
            version="1.0.0",
            description="Example plugin for demonstration",
            author="TinyCode Team",
            commands=["hello"],
            hooks=["before_execute"]
        )

    def initialize(self) -> bool:
        # Register a command
        self.register_command(PluginCommand(
            name="hello",
            description="Say hello from the plugin",
            handler=self._hello_command,
            safety_level=SafetyLevel.PERMISSIVE
        ))

        # Register a hook
        self.register_hook(PluginHook(
            name="before_execute",
            handler=self._before_execute_hook,
            priority=75
        ))

        return True

    def _hello_command(self, name: str = "World") -> str:
        """Example command handler"""
        return f"Hello, {name}! This is from the example plugin."

    def _before_execute_hook(self, command: str, *args, **kwargs):
        """Example hook handler"""
        print(f"[ExamplePlugin] About to execute: {command}")


# Built-in plugins directory structure:
# plugins/
# ├── __init__.py
# ├── plugins.json
# ├── example.py
# ├── git_enhanced/
# │   ├── __init__.py
# │   └── plugin.py
# └── web_scraper/
#     ├── __init__.py
#     ├── plugin.py
#     └── utils.py