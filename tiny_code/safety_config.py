"""Safety configuration system for TinyCode execution"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from enum import Enum

class SafetyLevel(Enum):
    """Safety levels for execution"""
    PERMISSIVE = "permissive"    # Minimal restrictions
    STANDARD = "standard"        # Default safety level
    STRICT = "strict"            # High security restrictions
    PARANOID = "paranoid"        # Maximum security

@dataclass
class ExecutionLimits:
    """Execution limits configuration"""
    max_file_size_mb: int = 10                    # Maximum file size to create/modify
    max_files_per_plan: int = 50                  # Maximum files per execution plan
    max_execution_time_seconds: int = 300         # Maximum execution time (5 minutes)
    max_backup_retention_days: int = 30           # Days to keep backups
    max_plan_complexity_score: int = 100          # Maximum plan complexity
    allowed_file_extensions: List[str] = None     # Allowed file extensions
    forbidden_paths: List[str] = None             # Forbidden path patterns
    require_confirmation_above_risk: str = "MEDIUM"  # Risk level requiring confirmation

    def __post_init__(self):
        if self.allowed_file_extensions is None:
            self.allowed_file_extensions = [
                ".py", ".js", ".ts", ".html", ".css", ".md", ".txt", ".json",
                ".yaml", ".yml", ".toml", ".cfg", ".ini", ".xml", ".sql",
                ".sh", ".bat", ".ps1", ".dockerfile", ".gitignore"
            ]

        if self.forbidden_paths is None:
            self.forbidden_paths = [
                "/etc/*", "/usr/*", "/bin/*", "/sbin/*", "/boot/*",
                "*/node_modules/*", "*/.git/*", "*/venv/*", "*/__pycache__/*",
                "*.pyc", "*.exe", "*.dll", "*.so", "*.dylib"
            ]

@dataclass
class SafetyConfig:
    """Complete safety configuration"""
    safety_level: SafetyLevel = SafetyLevel.STANDARD
    execution_limits: ExecutionLimits = None
    audit_enabled: bool = True
    backup_enabled: bool = True
    rollback_enabled: bool = True
    confirmation_prompts: bool = True
    dry_run_default: bool = False
    path_validation: bool = True
    content_scanning: bool = True

    def __post_init__(self):
        if self.execution_limits is None:
            self.execution_limits = ExecutionLimits()

        # Adjust limits based on safety level
        self._apply_safety_level_adjustments()

    def _apply_safety_level_adjustments(self):
        """Apply safety level specific adjustments"""
        if self.safety_level == SafetyLevel.PERMISSIVE:
            self.execution_limits.max_file_size_mb = 100
            self.execution_limits.max_files_per_plan = 200
            self.execution_limits.max_execution_time_seconds = 1800  # 30 minutes
            self.confirmation_prompts = False
            self.content_scanning = False

        elif self.safety_level == SafetyLevel.STRICT:
            self.execution_limits.max_file_size_mb = 5
            self.execution_limits.max_files_per_plan = 20
            self.execution_limits.max_execution_time_seconds = 120  # 2 minutes
            self.execution_limits.require_confirmation_above_risk = "LOW"
            self.dry_run_default = True

        elif self.safety_level == SafetyLevel.PARANOID:
            self.execution_limits.max_file_size_mb = 1
            self.execution_limits.max_files_per_plan = 5
            self.execution_limits.max_execution_time_seconds = 60   # 1 minute
            self.execution_limits.require_confirmation_above_risk = "NONE"
            self.dry_run_default = True
            self.confirmation_prompts = True
            # More restrictive file extensions for paranoid mode
            self.execution_limits.allowed_file_extensions = [".py", ".txt", ".md", ".json"]

class SafetyConfigManager:
    """Manages safety configuration persistence and validation"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".tiny_code_safety.json"
        self.config = self._load_config()

    def _load_config(self) -> SafetyConfig:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)

                # Convert safety level string to enum
                safety_level = SafetyLevel(data.get('safety_level', 'standard'))

                # Reconstruct ExecutionLimits
                limits_data = data.get('execution_limits', {})
                execution_limits = ExecutionLimits(**limits_data)

                # Reconstruct SafetyConfig
                config_data = {k: v for k, v in data.items() if k not in ['safety_level', 'execution_limits']}
                config = SafetyConfig(
                    safety_level=safety_level,
                    execution_limits=execution_limits,
                    **config_data
                )

                return config

            except Exception as e:
                print(f"Warning: Failed to load safety config: {e}")
                print("Using default safety configuration")

        return SafetyConfig()

    def save_config(self):
        """Save current configuration to file"""
        try:
            # Convert to serializable format
            config_dict = asdict(self.config)
            config_dict['safety_level'] = self.config.safety_level.value

            with open(self.config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to save safety config: {e}")

    def update_safety_level(self, level: SafetyLevel):
        """Update safety level and apply adjustments"""
        self.config.safety_level = level
        self.config._apply_safety_level_adjustments()
        self.save_config()

    def validate_execution_request(self, plan_data: Dict[str, Any]) -> List[str]:
        """Validate execution request against safety constraints"""
        violations = []

        # Check number of actions/files
        num_actions = len(plan_data.get('actions', []))
        if num_actions > self.config.execution_limits.max_files_per_plan:
            violations.append(f"Too many actions: {num_actions} > {self.config.execution_limits.max_files_per_plan}")

        # Check file extensions and paths
        if self.config.path_validation:
            for action in plan_data.get('actions', []):
                target = action.get('target', '')
                if target:
                    violations.extend(self._validate_file_path(target))

        # Check plan complexity
        complexity = plan_data.get('complexity_score', 0)
        if complexity > self.config.execution_limits.max_plan_complexity_score:
            violations.append(f"Plan too complex: {complexity} > {self.config.execution_limits.max_plan_complexity_score}")

        return violations

    def _validate_file_path(self, file_path: str) -> List[str]:
        """Validate individual file path"""
        violations = []

        # Check forbidden paths
        import fnmatch
        for forbidden in self.config.execution_limits.forbidden_paths:
            if fnmatch.fnmatch(file_path, forbidden):
                violations.append(f"Forbidden path: {file_path} matches {forbidden}")

        # Check file extension
        if '.' in file_path:
            ext = '.' + file_path.split('.')[-1].lower()
            if ext not in self.config.execution_limits.allowed_file_extensions:
                violations.append(f"Forbidden file extension: {ext} in {file_path}")

        return violations

    def should_require_confirmation(self, risk_level: str) -> bool:
        """Check if risk level requires confirmation"""
        if not self.config.confirmation_prompts:
            return False

        risk_hierarchy = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        required_level = risk_hierarchy.get(self.config.execution_limits.require_confirmation_above_risk, 2)
        current_level = risk_hierarchy.get(risk_level, 0)

        return current_level >= required_level

    def get_timeout_seconds(self) -> int:
        """Get execution timeout in seconds"""
        return self.config.execution_limits.max_execution_time_seconds

    def is_dry_run_default(self) -> bool:
        """Check if dry run should be default"""
        return self.config.dry_run_default

    def show_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for display"""
        return {
            "safety_level": self.config.safety_level.value,
            "max_files": self.config.execution_limits.max_files_per_plan,
            "max_file_size_mb": self.config.execution_limits.max_file_size_mb,
            "timeout_seconds": self.config.execution_limits.max_execution_time_seconds,
            "confirmation_required_above": self.config.execution_limits.require_confirmation_above_risk,
            "backup_enabled": self.config.backup_enabled,
            "audit_enabled": self.config.audit_enabled,
            "dry_run_default": self.config.dry_run_default,
            "allowed_extensions": len(self.config.execution_limits.allowed_file_extensions),
            "forbidden_patterns": len(self.config.execution_limits.forbidden_paths)
        }