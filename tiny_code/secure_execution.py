"""Secure command execution with timeouts, resource limits, and structured output"""

import os
import signal
import subprocess
import resource
import time
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from .sandbox import PathValidator, create_default_sandbox, SecurityError

class CommandSafety(Enum):
    """Safety levels for command execution"""
    SAFE = "safe"           # Read-only commands
    MODERATE = "moderate"   # Commands with limited write access
    DANGEROUS = "dangerous" # Commands that can modify system state
    BLOCKED = "blocked"     # Explicitly forbidden commands

@dataclass
class ExecutionResult:
    """Structured result of command execution"""
    stdout: str
    stderr: str
    exit_code: int
    timeout: bool
    execution_time: float
    memory_peak_mb: float
    cpu_time: float
    error_message: Optional[str] = None
    safety_warnings: List[str] = None

    def __post_init__(self):
        if self.safety_warnings is None:
            self.safety_warnings = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM consumption"""
        return asdict(self)

    def is_success(self) -> bool:
        """Check if execution was successful"""
        return self.exit_code == 0 and not self.timeout and not self.error_message

class CommandValidator:
    """Validates commands against security policies"""

    # Safe commands that are generally read-only
    SAFE_COMMANDS = {
        'ls', 'dir', 'cat', 'head', 'tail', 'grep', 'find', 'which', 'whereis',
        'pwd', 'whoami', 'id', 'date', 'uptime', 'df', 'du', 'free', 'ps',
        'top', 'htop', 'lscpu', 'lsblk', 'mount', 'env', 'printenv',
        'python', 'python3', 'node', 'npm', 'yarn', 'pip', 'pip3',
        'git status', 'git log', 'git diff', 'git show', 'git branch',
        'curl', 'wget', 'ping', 'nslookup', 'dig',
    }

    # Commands that can modify files but are generally safe
    MODERATE_COMMANDS = {
        'mkdir', 'touch', 'cp', 'mv', 'chmod', 'chown',
        'git add', 'git commit', 'git push', 'git pull',
        'npm install', 'pip install', 'yarn install',
    }

    # Dangerous commands that should require explicit approval
    DANGEROUS_COMMANDS = {
        'rm', 'rmdir', 'dd', 'fdisk', 'mkfs', 'mount', 'umount',
        'sudo', 'su', 'passwd', 'useradd', 'userdel', 'groupadd',
        'systemctl', 'service', 'init', 'shutdown', 'reboot',
        'iptables', 'ufw', 'firewall-cmd',
        'format', 'diskpart',
    }

    # Explicitly blocked commands
    BLOCKED_COMMANDS = {
        'rm -rf /', 'rm -rf *', ':(){ :|:& };:', 'chmod -R 777 /',
        'mv / /dev/null', 'dd if=/dev/random of=/dev/sda',
        'mkfs.ext4 /dev/sda', 'del /f /s /q C:\\*',
    }

    @classmethod
    def classify_command(cls, command: str) -> CommandSafety:
        """Classify command safety level"""
        command_lower = command.lower().strip()

        # Check for explicitly blocked commands
        for blocked in cls.BLOCKED_COMMANDS:
            if blocked in command_lower:
                return CommandSafety.BLOCKED

        # Extract the base command (first word)
        base_command = command_lower.split()[0] if command_lower else ""

        # Check against command lists
        if any(safe_cmd in command_lower for safe_cmd in cls.SAFE_COMMANDS):
            return CommandSafety.SAFE
        elif any(mod_cmd in command_lower for mod_cmd in cls.MODERATE_COMMANDS):
            return CommandSafety.MODERATE
        elif any(danger_cmd in command_lower for danger_cmd in cls.DANGEROUS_COMMANDS):
            return CommandSafety.DANGEROUS
        elif base_command in cls.DANGEROUS_COMMANDS:
            return CommandSafety.DANGEROUS

        # Default to moderate for unknown commands
        return CommandSafety.MODERATE

    @classmethod
    def get_safety_warnings(cls, command: str) -> List[str]:
        """Get safety warnings for a command"""
        warnings = []
        command_lower = command.lower()

        # Check for common dangerous patterns
        if 'rm' in command_lower and '-rf' in command_lower:
            warnings.append("Command contains 'rm -rf' which can delete files permanently")

        if 'sudo' in command_lower:
            warnings.append("Command uses 'sudo' which requires elevated privileges")

        if any(char in command for char in ['&', '|', ';', '>', '<', '`', '$(']):
            warnings.append("Command contains shell operators - verify this is intentional")

        if '/dev/' in command_lower:
            warnings.append("Command accesses device files - this could be dangerous")

        if 'curl' in command_lower or 'wget' in command_lower:
            warnings.append("Command downloads from internet - verify the source is trusted")

        return warnings

class SecureExecutor:
    """Executes commands with security controls and resource limits"""

    def __init__(self, working_directory: str, max_execution_time: int = 30,
                 max_memory_mb: int = 512, enable_network: bool = True):
        """
        Initialize secure executor

        Args:
            working_directory: Directory to execute commands in
            max_execution_time: Maximum execution time in seconds
            max_memory_mb: Maximum memory usage in MB
            enable_network: Whether to allow network access
        """
        self.working_directory = Path(working_directory).resolve()
        self.max_execution_time = max_execution_time
        self.max_memory_mb = max_memory_mb
        self.enable_network = enable_network
        self.validator = create_default_sandbox(str(self.working_directory))

        # Ensure working directory exists
        if not self.working_directory.exists():
            raise ValueError(f"Working directory does not exist: {self.working_directory}")

    def execute_command(self, command: str, allow_dangerous: bool = False,
                       timeout_override: Optional[int] = None) -> ExecutionResult:
        """
        Execute a command with security controls

        Args:
            command: Command to execute
            allow_dangerous: Whether to allow dangerous commands
            timeout_override: Override default timeout

        Returns:
            ExecutionResult with structured output
        """
        start_time = time.time()
        timeout = timeout_override or self.max_execution_time

        # Validate command safety
        safety_level = CommandValidator.classify_command(command)
        warnings = CommandValidator.get_safety_warnings(command)

        # Block dangerous commands unless explicitly allowed
        if safety_level == CommandSafety.BLOCKED:
            return ExecutionResult(
                stdout="",
                stderr="",
                exit_code=1,
                timeout=False,
                execution_time=0,
                memory_peak_mb=0,
                cpu_time=0,
                error_message=f"Command blocked for security: {command}",
                safety_warnings=["Command is explicitly blocked for security reasons"]
            )

        if safety_level == CommandSafety.DANGEROUS and not allow_dangerous:
            return ExecutionResult(
                stdout="",
                stderr="",
                exit_code=1,
                timeout=False,
                execution_time=0,
                memory_peak_mb=0,
                cpu_time=0,
                error_message=f"Dangerous command requires explicit approval: {command}",
                safety_warnings=warnings + ["Use allow_dangerous=True to execute this command"]
            )

        try:
            # Set up resource limits
            def limit_resources():
                # Set memory limit
                memory_limit = self.max_memory_mb * 1024 * 1024  # Convert to bytes
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

                # Set CPU time limit (slightly higher than wall time)
                cpu_limit = timeout + 10
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))

                # Limit number of processes
                resource.setrlimit(resource.RLIMIT_NPROC, (50, 50))

                # Limit file size (100MB)
                file_limit = 100 * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))

            # Execute command
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.working_directory),
                preexec_fn=limit_resources if os.name != 'nt' else None,
                start_new_session=True  # Create new process group for cleanup
            )

            # Monitor resource usage
            memory_peak = 0
            cpu_time = 0
            timed_out = False

            try:
                # Wait for completion with timeout
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode

                # Get resource usage
                if hasattr(process, 'pid'):
                    try:
                        proc = psutil.Process(process.pid)
                        memory_info = proc.memory_info()
                        memory_peak = memory_info.rss / (1024 * 1024)  # Convert to MB
                        cpu_time = proc.cpu_times().user + proc.cpu_times().system
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

            except subprocess.TimeoutExpired:
                # Kill the process and its children
                timed_out = True
                try:
                    if os.name != 'nt':
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    else:
                        process.terminate()

                    # Wait a bit for graceful termination
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        if os.name != 'nt':
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        else:
                            process.kill()

                except (OSError, ProcessLookupError):
                    pass

                stdout, stderr = process.communicate()
                exit_code = process.returncode if process.returncode is not None else -1

            execution_time = time.time() - start_time

            # Enhance error messages for LLM consumption
            if timed_out:
                error_message = (
                    f"Command timed out after {timeout} seconds. "
                    "Consider breaking the operation into smaller steps or optimizing the command."
                )
            elif exit_code != 0:
                error_message = f"Command failed with exit code {exit_code}."
                if stderr:
                    error_message += f" Error: {stderr.strip()}"
            else:
                error_message = None

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                timeout=timed_out,
                execution_time=execution_time,
                memory_peak_mb=memory_peak,
                cpu_time=cpu_time,
                error_message=error_message,
                safety_warnings=warnings
            )

        except Exception as e:
            return ExecutionResult(
                stdout="",
                stderr="",
                exit_code=1,
                timeout=False,
                execution_time=time.time() - start_time,
                memory_peak_mb=0,
                cpu_time=0,
                error_message=f"Execution error: {e}",
                safety_warnings=warnings
            )

    def execute_command_safe(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command and return dictionary result for LLM consumption"""
        result = self.execute_command(command, **kwargs)
        return result.to_dict()

def create_secure_executor(working_directory: str, **kwargs) -> SecureExecutor:
    """Create a SecureExecutor with default settings"""
    return SecureExecutor(working_directory, **kwargs)

def execute_bash_safe(command: str, working_directory: str, timeout: int = 30,
                     allow_dangerous: bool = False) -> str:
    """
    Convenience function to execute bash command safely and return formatted result

    Returns formatted string suitable for LLM consumption
    """
    executor = create_secure_executor(working_directory, max_execution_time=timeout)
    result = executor.execute_command(command, allow_dangerous=allow_dangerous)

    if result.timeout:
        return f"Error: Command timed out after {timeout} seconds. Consider breaking into smaller operations."

    if result.error_message:
        return f"Error: {result.error_message}"

    if result.safety_warnings:
        warning_text = "; ".join(result.safety_warnings)
        return f"Output: {result.stdout}\nWarnings: {warning_text}"

    return f"Output: {result.stdout}" if result.stdout else "Command completed successfully (no output)"