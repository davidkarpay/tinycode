"""Sandboxing system for TinyCode with path validation and security controls"""

import os
import re
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class SandboxViolationType(Enum):
    """Types of sandbox violations"""
    PATH_TRAVERSAL = "path_traversal"
    OUTSIDE_WORKING_DIR = "outside_working_dir"
    FORBIDDEN_PATH = "forbidden_path"
    SYMLINK_ESCAPE = "symlink_escape"
    INVALID_CHARACTERS = "invalid_characters"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"

@dataclass
class SandboxViolation:
    """Represents a sandbox security violation"""
    violation_type: SandboxViolationType
    attempted_path: str
    working_directory: str
    message: str
    suggestions: List[str]

@dataclass
class SandboxConfig:
    """Configuration for sandbox security settings"""
    working_directory: str
    max_file_size_mb: int = 10
    forbidden_paths: List[str] = None
    forbidden_patterns: List[str] = None
    allow_symlinks: bool = False
    case_sensitive: bool = True

    def __post_init__(self):
        """Initialize default forbidden paths and patterns"""
        if self.forbidden_paths is None:
            self.forbidden_paths = [
                "/etc", "/usr", "/bin", "/sbin", "/boot", "/sys", "/proc",
                "/dev", "/var/log", "/tmp", "/root", "/home/*/.ssh",
            ]

        if self.forbidden_patterns is None:
            self.forbidden_patterns = [
                r".*\.\..*",  # Path traversal patterns
                r"/\.git/.*", # Git directories
                r"/node_modules/.*", # Node modules
                r"/venv/.*", # Virtual environments
                r".*/__pycache__/.*", # Python cache
                r".*\.pyc$", # Compiled Python
                r".*\.(exe|dll|so|dylib)$", # Executables
            ]

class PathValidator:
    """Validates file paths against sandbox security policies"""

    def __init__(self, config: SandboxConfig):
        self.config = config
        self.working_dir = Path(config.working_directory).resolve()

        # Validate working directory exists and is accessible
        if not self.working_dir.exists():
            raise ValueError(f"Working directory does not exist: {self.working_dir}")
        if not self.working_dir.is_dir():
            raise ValueError(f"Working directory is not a directory: {self.working_dir}")

        # Compile forbidden patterns for performance
        self.forbidden_patterns_compiled = [
            re.compile(pattern, re.IGNORECASE if not config.case_sensitive else 0)
            for pattern in config.forbidden_patterns
        ]

    def validate_path(self, path: Union[str, Path], operation: str = "access") -> Optional[SandboxViolation]:
        """
        Validate a path against sandbox security policies.

        Args:
            path: Path to validate
            operation: Type of operation (read, write, execute, etc.)

        Returns:
            SandboxViolation if path is invalid, None if valid
        """
        try:
            # Convert to Path object and handle relative paths
            path_obj = Path(path)

            # Check for invalid characters that could indicate injection attempts
            path_str = str(path)
            if self._contains_invalid_characters(path_str):
                return SandboxViolation(
                    violation_type=SandboxViolationType.INVALID_CHARACTERS,
                    attempted_path=path_str,
                    working_directory=str(self.working_dir),
                    message=f"Path contains invalid or suspicious characters: {path_str}",
                    suggestions=["Use only alphanumeric characters, hyphens, underscores, and forward slashes"]
                )

            # Check forbidden patterns before resolving
            for pattern in self.forbidden_patterns_compiled:
                if pattern.search(path_str):
                    return SandboxViolation(
                        violation_type=SandboxViolationType.FORBIDDEN_PATH,
                        attempted_path=path_str,
                        working_directory=str(self.working_dir),
                        message=f"Path matches forbidden pattern: {path_str}",
                        suggestions=["Choose a path that doesn't match system or cache directories"]
                    )

            # Resolve the absolute path
            if path_obj.is_absolute():
                abs_path = path_obj.resolve()
            else:
                abs_path = (self.working_dir / path_obj).resolve()

            # Check for symlink escapes if symlinks are not allowed
            if not self.config.allow_symlinks and abs_path.is_symlink():
                # Follow the symlink and check if it escapes
                try:
                    resolved_path = abs_path.resolve()
                    if not self._is_within_working_directory(resolved_path):
                        return SandboxViolation(
                            violation_type=SandboxViolationType.SYMLINK_ESCAPE,
                            attempted_path=path_str,
                            working_directory=str(self.working_dir),
                            message=f"Symlink points outside working directory: {path_str} -> {resolved_path}",
                            suggestions=["Use direct paths instead of symlinks", "Copy the target file to the working directory"]
                        )
                except (OSError, RuntimeError):
                    return SandboxViolation(
                        violation_type=SandboxViolationType.SYMLINK_ESCAPE,
                        attempted_path=path_str,
                        working_directory=str(self.working_dir),
                        message=f"Symlink is broken or creates a loop: {path_str}",
                        suggestions=["Remove the broken symlink", "Create a direct file instead"]
                    )

            # Primary security check: ensure path is within working directory
            if not self._is_within_working_directory(abs_path):
                return SandboxViolation(
                    violation_type=SandboxViolationType.OUTSIDE_WORKING_DIR,
                    attempted_path=path_str,
                    working_directory=str(self.working_dir),
                    message=f"Path is outside working directory: {abs_path}",
                    suggestions=[
                        f"Use paths relative to {self.working_dir}",
                        "Check for '../' path traversal attempts",
                        "Ensure the path starts within the project directory"
                    ]
                )

            # Check explicit forbidden paths
            abs_path_str = str(abs_path)
            for forbidden in self.config.forbidden_paths:
                if self._matches_forbidden_path(abs_path_str, forbidden):
                    return SandboxViolation(
                        violation_type=SandboxViolationType.FORBIDDEN_PATH,
                        attempted_path=path_str,
                        working_directory=str(self.working_dir),
                        message=f"Path is explicitly forbidden: {abs_path_str}",
                        suggestions=["Choose a path in the project workspace", "Avoid system directories"]
                    )

            # Check file size limits for write operations
            if operation in ("write", "create", "modify") and abs_path.exists():
                try:
                    file_size_mb = abs_path.stat().st_size / (1024 * 1024)
                    if file_size_mb > self.config.max_file_size_mb:
                        return SandboxViolation(
                            violation_type=SandboxViolationType.FILE_SIZE_EXCEEDED,
                            attempted_path=path_str,
                            working_directory=str(self.working_dir),
                            message=f"File size ({file_size_mb:.1f}MB) exceeds limit ({self.config.max_file_size_mb}MB)",
                            suggestions=[
                                f"Use files smaller than {self.config.max_file_size_mb}MB",
                                "Split large files into smaller chunks",
                                "Process the file in streaming mode"
                            ]
                        )
                except OSError:
                    # If we can't stat the file, allow the operation to proceed
                    # The underlying operation will handle the error appropriately
                    pass

            return None  # Path is valid

        except Exception as e:
            # If path resolution fails, treat as invalid
            return SandboxViolation(
                violation_type=SandboxViolationType.PATH_TRAVERSAL,
                attempted_path=str(path),
                working_directory=str(self.working_dir),
                message=f"Path resolution failed: {e}",
                suggestions=["Use a valid file path", "Check for special characters or encoding issues"]
            )

    def get_safe_path(self, path: Union[str, Path]) -> Path:
        """
        Get a safe path within the working directory, raising an exception if invalid.

        Args:
            path: Path to validate and convert

        Returns:
            Safe absolute path within working directory

        Raises:
            SecurityError: If path violates sandbox policies
        """
        violation = self.validate_path(path)
        if violation:
            raise SecurityError(f"Sandbox violation: {violation.message}")

        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj.resolve()
        else:
            return (self.working_dir / path_obj).resolve()

    def list_accessible_files(self, pattern: str = "*") -> List[str]:
        """
        List files accessible within the working directory.

        Args:
            pattern: Glob pattern to match files

        Returns:
            List of accessible file paths relative to working directory
        """
        try:
            accessible_files = []
            for path in self.working_dir.rglob(pattern):
                if path.is_file():
                    relative_path = path.relative_to(self.working_dir)
                    if self.validate_path(relative_path) is None:
                        accessible_files.append(str(relative_path))
            return sorted(accessible_files)
        except Exception:
            return []

    def _is_within_working_directory(self, path: Path) -> bool:
        """Check if a path is within the working directory using prefix matching"""
        try:
            # Convert both paths to absolute and resolve any symlinks
            abs_path = path.resolve()
            abs_working_dir = self.working_dir.resolve()

            # Use the same logic as Go's strings.HasPrefix for path checking
            abs_path_str = str(abs_path)
            abs_working_dir_str = str(abs_working_dir)

            # Ensure working directory ends with separator for exact matching
            if not abs_working_dir_str.endswith(os.sep):
                abs_working_dir_str += os.sep

            # Check if path starts with working directory
            return abs_path_str.startswith(abs_working_dir_str) or abs_path == abs_working_dir

        except (OSError, RuntimeError):
            return False

    def _contains_invalid_characters(self, path_str: str) -> bool:
        """Check for characters that could indicate injection attempts"""
        # Check for null bytes, control characters, and suspicious patterns
        if '\x00' in path_str:
            return True

        # Check for unusual control characters (but allow normal path separators)
        for char in path_str:
            if ord(char) < 32 and char not in ['\t', '\n', '\r']:
                return True

        # Check for suspicious patterns that might indicate injection
        suspicious_patterns = [
            'file://', 'http://', 'https://', 'ftp://',  # URL schemes
            '\\\\', '\\x', '\\u',  # Escape sequences
            '$(', '`',  # Command injection
            '&', '|', ';', '>', '<',  # Shell operators (in paths)
        ]

        for pattern in suspicious_patterns:
            if pattern in path_str:
                return True

        return False

    def _matches_forbidden_path(self, path: str, forbidden: str) -> bool:
        """Check if a path matches a forbidden path pattern"""
        # Handle wildcard patterns
        if '*' in forbidden:
            pattern = forbidden.replace('*', '.*')
            return bool(re.match(pattern, path, re.IGNORECASE if not self.config.case_sensitive else 0))

        # Exact match or prefix match for directories
        if not self.config.case_sensitive:
            path = path.lower()
            forbidden = forbidden.lower()

        return path == forbidden or path.startswith(forbidden + os.sep)

class SecurityError(Exception):
    """Exception raised for sandbox security violations"""
    pass

def create_default_sandbox(working_directory: str) -> PathValidator:
    """Create a PathValidator with default security settings"""
    config = SandboxConfig(working_directory=working_directory)
    return PathValidator(config)

def validate_path_safe(path: Union[str, Path], working_directory: str, operation: str = "access") -> str:
    """
    Convenience function to validate a path and return error message if invalid.

    Args:
        path: Path to validate
        working_directory: Working directory for validation
        operation: Type of operation

    Returns:
        Empty string if valid, error message if invalid
    """
    try:
        validator = create_default_sandbox(working_directory)
        violation = validator.validate_path(path, operation)
        if violation:
            return f"Security Error: {violation.message}. Suggestions: {', '.join(violation.suggestions)}"
        return ""
    except Exception as e:
        return f"Path validation error: {e}"