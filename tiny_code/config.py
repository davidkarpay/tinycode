"""Centralized configuration management for TinyCode with environment variable support"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

class ConfigSource(Enum):
    """Sources of configuration in order of precedence"""
    CLI_ARGS = "cli_args"          # Highest precedence
    ENV_VARS = "environment"
    CONFIG_FILE = "config_file"
    DEFAULTS = "defaults"          # Lowest precedence

@dataclass
class SecurityConfig:
    """Security-related configuration"""
    # Sandbox settings
    working_directory: str = "."
    max_file_size_mb: int = 10
    allow_symlinks: bool = False
    forbidden_paths: List[str] = field(default_factory=lambda: [
        "/etc/*", "/usr/*", "/bin/*", "/sbin/*", "/boot/*",
        "*/node_modules/*", "*/.git/*", "*/venv/*", "*/__pycache__/*"
    ])

    # Command execution
    bash_timeout_seconds: int = 30
    max_memory_mb: int = 512
    enable_network: bool = True
    allow_dangerous_commands: bool = False
    command_whitelist: List[str] = field(default_factory=list)
    command_blacklist: List[str] = field(default_factory=lambda: [
        "rm -rf /", "dd if=/dev/random", ":(){ :|:& };:"
    ])

    # Resource limits
    max_open_files: int = 100
    max_processes: int = 50
    cpu_limit_percent: float = 80.0

@dataclass
class LLMConfig:
    """LLM-related configuration"""
    # Model settings
    default_model: str = "tinyllama:latest"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout_seconds: int = 60

    # API settings
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    api_timeout: float = 30.0
    max_retries: int = 3

    # Response settings
    stream_responses: bool = True
    include_model_info: bool = True

@dataclass
class MetricsConfig:
    """Metrics and monitoring configuration"""
    # Collection settings
    enable_metrics: bool = True
    metrics_storage_path: str = "data/metrics"
    resource_monitoring_interval: float = 5.0
    max_history_entries: int = 1000

    # Warning thresholds
    memory_warning_mb: float = 512
    cpu_warning_percent: float = 80
    command_count_warning: int = 100
    execution_time_warning: float = 300

    # Export settings
    auto_save_interval: int = 10  # commands
    export_format: str = "json"  # json, csv, prometheus

@dataclass
class TestingConfig:
    """Testing-related configuration"""
    # Test discovery
    auto_discover_tests: bool = True
    test_patterns: List[str] = field(default_factory=lambda: [
        "test_*.py", "*_test.py", "tests/", "spec/", "__tests__/"
    ])

    # Test execution
    run_tests_after_changes: bool = True
    test_timeout_seconds: int = 60
    parallel_test_execution: bool = False
    coverage_reporting: bool = True

    # Framework detection
    preferred_test_framework: str = "auto"  # auto, pytest, unittest, jest, etc.

@dataclass
class UIConfig:
    """User interface configuration"""
    # Console output
    colored_output: bool = True
    verbose_mode: bool = False
    show_timestamps: bool = True
    max_output_lines: int = 1000

    # Progress indicators
    show_progress_bars: bool = True
    spinner_style: str = "dots"

    # Error display
    show_stack_traces: bool = False
    truncate_long_errors: bool = True
    max_error_length: int = 500

@dataclass
class TinyCodeConfig:
    """Complete TinyCode configuration"""
    # Sub-configurations
    security: SecurityConfig = field(default_factory=SecurityConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    testing: TestingConfig = field(default_factory=TestingConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    # Global settings
    debug_mode: bool = False
    log_level: str = "INFO"
    config_version: str = "1.0"

    # Runtime settings (not serialized)
    config_file_path: Optional[str] = None
    _sources: Dict[str, ConfigSource] = field(default_factory=dict, init=False)

    def get_setting_source(self, key: str) -> ConfigSource:
        """Get the source of a configuration setting"""
        return self._sources.get(key, ConfigSource.DEFAULTS)

    def update_from_dict(self, data: Dict[str, Any], source: ConfigSource) -> None:
        """Update configuration from dictionary with source tracking"""
        for key, value in data.items():
            if hasattr(self, key):
                # Handle nested configurations
                if key in ['security', 'llm', 'metrics', 'testing', 'ui']:
                    config_obj = getattr(self, key)
                    if isinstance(value, dict):
                        for nested_key, nested_value in value.items():
                            if hasattr(config_obj, nested_key):
                                setattr(config_obj, nested_key, nested_value)
                                self._sources[f"{key}.{nested_key}"] = source
                else:
                    setattr(self, key, value)
                    self._sources[key] = source

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Validate security settings
        if self.security.max_file_size_mb <= 0:
            errors.append("security.max_file_size_mb must be positive")

        if self.security.bash_timeout_seconds <= 0:
            errors.append("security.bash_timeout_seconds must be positive")

        if not Path(self.security.working_directory).exists():
            errors.append(f"security.working_directory does not exist: {self.security.working_directory}")

        # Validate LLM settings
        if self.llm.temperature < 0 or self.llm.temperature > 2:
            errors.append("llm.temperature must be between 0 and 2")

        if self.llm.max_tokens <= 0:
            errors.append("llm.max_tokens must be positive")

        # Validate metrics settings
        if self.metrics.resource_monitoring_interval <= 0:
            errors.append("metrics.resource_monitoring_interval must be positive")

        # Validate UI settings
        if self.ui.max_output_lines <= 0:
            errors.append("ui.max_output_lines must be positive")

        return errors

class ConfigManager:
    """Manages TinyCode configuration with multiple sources"""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file
        self.config = TinyCodeConfig()
        self._env_prefix = "TINYCODE_"

        # Load configuration in order of precedence
        self._load_defaults()
        self._load_config_file()
        self._load_environment_variables()

    def _load_defaults(self) -> None:
        """Load default configuration"""
        # Defaults are already set in the dataclass definitions
        pass

    def _load_config_file(self) -> None:
        """Load configuration from file"""
        config_paths = []

        # Add explicit config file if provided
        if self.config_file:
            config_paths.append(self.config_file)

        # Add standard config file locations
        config_paths.extend([
            "tinycode.yaml",
            "tinycode.yml",
            "tinycode.json",
            ".tinycode.yaml",
            ".tinycode.yml",
            ".tinycode.json",
            os.path.expanduser("~/.tinycode/config.yaml"),
            os.path.expanduser("~/.config/tinycode/config.yaml")
        ])

        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    data = self._load_file(config_path)
                    if data:
                        self.config.update_from_dict(data, ConfigSource.CONFIG_FILE)
                        self.config.config_file_path = config_path
                        logging.info(f"Loaded configuration from {config_path}")
                        break
                except Exception as e:
                    logging.warning(f"Failed to load config from {config_path}: {e}")

    def _load_environment_variables(self) -> None:
        """Load configuration from environment variables"""
        env_vars = {}

        for key, value in os.environ.items():
            if key.startswith(self._env_prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(self._env_prefix):].lower()

                # Handle nested keys (e.g., TINYCODE_SECURITY_MAX_FILE_SIZE_MB)
                parts = config_key.split('_')
                if len(parts) >= 2:
                    section = parts[0]
                    setting = '_'.join(parts[1:])

                    if section not in env_vars:
                        env_vars[section] = {}
                    env_vars[section][setting] = self._parse_env_value(value)
                else:
                    env_vars[config_key] = self._parse_env_value(value)

        if env_vars:
            self.config.update_from_dict(env_vars, ConfigSource.ENV_VARS)

    def _load_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from file (YAML or JSON)"""
        path = Path(file_path)

        with open(path, 'r') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                return json.load(f)
            else:
                # Try to detect format by content
                content = f.read()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return yaml.safe_load(content)

    def _parse_env_value(self, value: str) -> Union[str, int, float, bool, List[str]]:
        """Parse environment variable value to appropriate type"""
        # Handle boolean values
        if value.lower() in ['true', 'yes', '1', 'on']:
            return True
        elif value.lower() in ['false', 'no', '0', 'off']:
            return False

        # Handle numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Handle list values (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',')]

        # Return as string
        return value

    def save_config(self, file_path: Optional[str] = None) -> None:
        """Save current configuration to file"""
        if file_path is None:
            file_path = self.config.config_file_path or "tinycode.yaml"

        path = Path(file_path)
        config_dict = self.config.to_dict()

        # Remove runtime fields
        config_dict.pop('_sources', None)
        config_dict.pop('config_file_path', None)

        with open(path, 'w') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_dict, f, indent=2)

        logging.info(f"Configuration saved to {file_path}")

    def validate_config(self) -> bool:
        """Validate current configuration"""
        errors = self.config.validate()
        if errors:
            for error in errors:
                logging.error(f"Configuration error: {error}")
            return False
        return True

    def get_config(self) -> TinyCodeConfig:
        """Get current configuration"""
        return self.config

    def update_config(self, updates: Dict[str, Any], source: ConfigSource = ConfigSource.CLI_ARGS) -> None:
        """Update configuration with new values"""
        self.config.update_from_dict(updates, source)

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration with sources"""
        summary = {
            "config_file": self.config.config_file_path,
            "validation_errors": self.config.validate(),
            "setting_sources": {
                key: source.value for key, source in self.config._sources.items()
            },
            "environment_variables": {
                key: value for key, value in os.environ.items()
                if key.startswith(self._env_prefix)
            }
        }
        return summary

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config = TinyCodeConfig()
        self._load_config_file()
        self._load_environment_variables()

# Global configuration instance
_global_config: Optional[ConfigManager] = None

def get_config() -> TinyCodeConfig:
    """Get the global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config.config

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager"""
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config

def initialize_config(config_file: Optional[str] = None) -> ConfigManager:
    """Initialize global configuration"""
    global _global_config
    _global_config = ConfigManager(config_file)
    return _global_config

def create_default_config_file(file_path: str = "tinycode.yaml") -> None:
    """Create a default configuration file with comments"""
    config_template = """# TinyCode Configuration File
# This file configures the behavior of TinyCode AI coding assistant

# Security settings
security:
  working_directory: "."              # Directory to restrict operations to
  max_file_size_mb: 10               # Maximum file size for operations
  allow_symlinks: false              # Whether to allow symbolic links
  bash_timeout_seconds: 30           # Timeout for bash commands
  max_memory_mb: 512                 # Memory limit for processes
  enable_network: true               # Allow network access
  allow_dangerous_commands: false    # Allow potentially dangerous commands

# LLM settings
llm:
  default_model: "tinyllama:latest"  # Default Ollama model
  temperature: 0.7                   # Response randomness (0.0-2.0)
  max_tokens: 2048                   # Maximum response length
  timeout_seconds: 60                # LLM request timeout
  stream_responses: true             # Stream responses for better UX

# Metrics and monitoring
metrics:
  enable_metrics: true               # Enable metrics collection
  metrics_storage_path: "data/metrics"  # Where to store metrics
  memory_warning_mb: 512             # Memory usage warning threshold
  cpu_warning_percent: 80            # CPU usage warning threshold

# Testing configuration
testing:
  auto_discover_tests: true          # Automatically find test files
  run_tests_after_changes: true      # Run tests after code modifications
  test_timeout_seconds: 60           # Timeout for test execution
  coverage_reporting: true           # Enable coverage reporting

# User interface
ui:
  colored_output: true               # Use colored console output
  verbose_mode: false                # Show detailed operation logs
  show_progress_bars: true           # Show progress indicators
  show_stack_traces: false           # Show full stack traces on errors

# Global settings
debug_mode: false                    # Enable debug logging
log_level: "INFO"                    # Logging level (DEBUG, INFO, WARNING, ERROR)
"""

    with open(file_path, 'w') as f:
        f.write(config_template)

    print(f"Default configuration file created: {file_path}")
    print("Edit this file to customize TinyCode behavior.")
    print("You can also use environment variables with TINYCODE_ prefix.")

if __name__ == "__main__":
    # Command-line interface for configuration management
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "create":
        file_path = sys.argv[2] if len(sys.argv) > 2 else "tinycode.yaml"
        create_default_config_file(file_path)
    else:
        # Show current configuration
        config_manager = get_config_manager()
        summary = config_manager.get_config_summary()
        print(json.dumps(summary, indent=2))