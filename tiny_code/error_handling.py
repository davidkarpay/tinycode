"""
Enhanced Error Handling and Recovery Mechanisms for TinyCode
Provides robust error handling, graceful degradation, and recovery features
"""

import os
import sys
import traceback
import logging
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import contextmanager
import functools
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

console = Console()

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Minor issues, functionality mostly intact
    MEDIUM = "medium"     # Moderate issues, some features affected
    HIGH = "high"         # Major issues, significant functionality lost
    CRITICAL = "critical" # Critical issues, system may be unstable

class ErrorCategory(Enum):
    """Categories of errors"""
    SYSTEM = "system"           # System-level errors (permissions, resources)
    NETWORK = "network"         # Network connectivity issues
    FILE_IO = "file_io"         # File system operations
    GIT = "git"                 # Git operations
    DEPENDENCY = "dependency"   # Missing dependencies
    CONFIGURATION = "configuration"  # Configuration issues
    USER_INPUT = "user_input"   # Invalid user input
    INTERNAL = "internal"       # Internal code errors
    EXTERNAL = "external"       # External service failures

@dataclass
class ErrorInfo:
    """Comprehensive error information"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    user_action: Optional[str] = None
    recovery_suggestion: Optional[str] = None
    auto_recoverable: bool = False
    recovery_attempted: bool = False
    recovery_successful: bool = False

@dataclass
class RecoveryStrategy:
    """Strategy for recovering from errors"""
    name: str
    description: str
    applicable_categories: List[ErrorCategory]
    severity_threshold: ErrorSeverity
    auto_execute: bool
    recovery_function: Callable
    prerequisites: List[str] = field(default_factory=list)
    timeout_seconds: int = 30

class ErrorRecoveryManager:
    """Comprehensive error handling and recovery system"""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or Path.home() / '.tiny_code')
        self.data_dir.mkdir(exist_ok=True)

        self.error_log_file = self.data_dir / 'error_log.db'
        self.recovery_log_file = self.data_dir / 'recovery_log.json'

        self._init_error_database()
        self._init_recovery_strategies()
        self._setup_logging()

    def _init_error_database(self):
        """Initialize the error tracking database"""
        with sqlite3.connect(str(self.error_log_file)) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    context TEXT,
                    stack_trace TEXT,
                    user_action TEXT,
                    recovery_suggestion TEXT,
                    auto_recoverable BOOLEAN DEFAULT FALSE,
                    recovery_attempted BOOLEAN DEFAULT FALSE,
                    recovery_successful BOOLEAN DEFAULT FALSE
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_errors_timestamp
                ON errors(timestamp)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_errors_category_severity
                ON errors(category, severity)
            ''')

    def _init_recovery_strategies(self):
        """Initialize recovery strategies"""
        self.recovery_strategies = [
            RecoveryStrategy(
                name="dependency_install",
                description="Automatically install missing dependencies",
                applicable_categories=[ErrorCategory.DEPENDENCY],
                severity_threshold=ErrorSeverity.MEDIUM,
                auto_execute=False,  # Ask user first
                recovery_function=self._recover_missing_dependency,
                prerequisites=["pip", "internet_connection"]
            ),
            RecoveryStrategy(
                name="git_repository_reset",
                description="Reset git repository to clean state",
                applicable_categories=[ErrorCategory.GIT],
                severity_threshold=ErrorSeverity.HIGH,
                auto_execute=False,
                recovery_function=self._recover_git_repository,
                prerequisites=["git"]
            ),
            RecoveryStrategy(
                name="file_permission_fix",
                description="Fix file permission issues",
                applicable_categories=[ErrorCategory.FILE_IO, ErrorCategory.SYSTEM],
                severity_threshold=ErrorSeverity.MEDIUM,
                auto_execute=True,
                recovery_function=self._recover_file_permissions
            ),
            RecoveryStrategy(
                name="network_retry",
                description="Retry network operations with backoff",
                applicable_categories=[ErrorCategory.NETWORK],
                severity_threshold=ErrorSeverity.LOW,
                auto_execute=True,
                recovery_function=self._recover_network_issue,
                timeout_seconds=60
            ),
            RecoveryStrategy(
                name="configuration_reset",
                description="Reset configuration to defaults",
                applicable_categories=[ErrorCategory.CONFIGURATION],
                severity_threshold=ErrorSeverity.HIGH,
                auto_execute=False,
                recovery_function=self._recover_configuration
            ),
            RecoveryStrategy(
                name="cleanup_temp_files",
                description="Clean up temporary files and caches",
                applicable_categories=[ErrorCategory.FILE_IO, ErrorCategory.SYSTEM],
                severity_threshold=ErrorSeverity.LOW,
                auto_execute=True,
                recovery_function=self._recover_cleanup_temp_files
            ),
            RecoveryStrategy(
                name="restart_services",
                description="Restart external services",
                applicable_categories=[ErrorCategory.EXTERNAL],
                severity_threshold=ErrorSeverity.HIGH,
                auto_execute=False,
                recovery_function=self._recover_restart_services
            )
        ]

    def _setup_logging(self):
        """Setup enhanced logging"""
        log_file = self.data_dir / 'detailed_error.log'

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(str(log_file)),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger('TinyCodeErrorHandler')

    def handle_error(self, error: Exception, context: Dict[str, Any] = None,
                    user_action: str = None, auto_recover: bool = True) -> ErrorInfo:
        """Handle an error with comprehensive logging and recovery"""
        # Generate unique error ID
        error_id = f"TC_{int(time.time() * 1000)}_{hash(str(error)) % 10000:04d}"

        # Categorize and assess severity
        category = self._categorize_error(error, context)
        severity = self._assess_severity(error, category, context)

        # Create error info
        error_info = ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=str(error),
            details=self._extract_error_details(error),
            context=context or {},
            stack_trace=traceback.format_exc(),
            user_action=user_action,
            recovery_suggestion=self._generate_recovery_suggestion(error, category, severity),
            auto_recoverable=self._is_auto_recoverable(category, severity)
        )

        # Log the error
        self._log_error(error_info)

        # Display error to user
        self._display_error(error_info)

        # Attempt recovery if appropriate
        if auto_recover and error_info.auto_recoverable:
            self._attempt_recovery(error_info)
        elif auto_recover:
            self._suggest_recovery(error_info)

        return error_info

    def _categorize_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorCategory:
        """Categorize an error based on its type and context"""
        error_type = type(error).__name__
        error_message = str(error).lower()

        # Network-related errors
        if any(keyword in error_message for keyword in
               ['connection', 'network', 'timeout', 'unreachable', 'dns']):
            return ErrorCategory.NETWORK

        # File I/O errors
        if any(keyword in error_message for keyword in
               ['permission denied', 'file not found', 'directory', 'no space']):
            return ErrorCategory.FILE_IO

        # Git errors
        if any(keyword in error_message for keyword in
               ['git', 'repository', 'branch', 'commit', 'merge']):
            return ErrorCategory.GIT

        # Dependency errors
        if any(keyword in error_message for keyword in
               ['module', 'import', 'not found', 'dependency']):
            return ErrorCategory.DEPENDENCY

        # System errors
        if error_type in ['OSError', 'SystemError', 'EnvironmentError']:
            return ErrorCategory.SYSTEM

        # Configuration errors
        if any(keyword in error_message for keyword in
               ['config', 'setting', 'invalid', 'missing']):
            return ErrorCategory.CONFIGURATION

        # User input errors
        if error_type in ['ValueError', 'KeyError', 'IndexError'] and context and 'user_input' in context:
            return ErrorCategory.USER_INPUT

        # External service errors
        if any(keyword in error_message for keyword in
               ['api', 'service', 'external', 'remote']):
            return ErrorCategory.EXTERNAL

        # Default to internal error
        return ErrorCategory.INTERNAL

    def _assess_severity(self, error: Exception, category: ErrorCategory,
                        context: Dict[str, Any] = None) -> ErrorSeverity:
        """Assess the severity of an error"""
        error_message = str(error).lower()

        # Critical severity indicators
        if any(keyword in error_message for keyword in
               ['corrupt', 'fatal', 'critical', 'system failure']):
            return ErrorSeverity.CRITICAL

        # High severity based on category
        if category in [ErrorCategory.SYSTEM, ErrorCategory.CONFIGURATION]:
            if any(keyword in error_message for keyword in
                   ['cannot', 'failed', 'error', 'denied']):
                return ErrorSeverity.HIGH

        # Medium severity for operational issues
        if category in [ErrorCategory.GIT, ErrorCategory.DEPENDENCY, ErrorCategory.EXTERNAL]:
            return ErrorSeverity.MEDIUM

        # Low severity for recoverable issues
        if category in [ErrorCategory.USER_INPUT, ErrorCategory.FILE_IO]:
            return ErrorSeverity.LOW

        # Network issues are typically medium unless connection completely fails
        if category == ErrorCategory.NETWORK:
            if 'timeout' in error_message:
                return ErrorSeverity.MEDIUM
            return ErrorSeverity.HIGH

        return ErrorSeverity.MEDIUM

    def _extract_error_details(self, error: Exception) -> str:
        """Extract detailed information from an error"""
        details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'module': getattr(error, '__module__', 'unknown'),
        }

        # Add specific details for common error types
        if hasattr(error, 'errno'):
            details['error_code'] = error.errno

        if hasattr(error, 'filename'):
            details['filename'] = error.filename

        if hasattr(error, 'response'):  # HTTP errors
            details['http_status'] = getattr(error.response, 'status_code', None)

        return json.dumps(details, indent=2)

    def _generate_recovery_suggestion(self, error: Exception, category: ErrorCategory,
                                    severity: ErrorSeverity) -> str:
        """Generate a recovery suggestion for the error"""
        suggestions = {
            ErrorCategory.DEPENDENCY: "Try installing the missing dependency with pip install <package>",
            ErrorCategory.FILE_IO: "Check file permissions and available disk space",
            ErrorCategory.GIT: "Verify git repository status and try git status",
            ErrorCategory.NETWORK: "Check internet connection and try again",
            ErrorCategory.CONFIGURATION: "Verify configuration settings or reset to defaults",
            ErrorCategory.USER_INPUT: "Please check your input and try again",
            ErrorCategory.SYSTEM: "Check system resources and permissions",
            ErrorCategory.EXTERNAL: "External service may be unavailable, try again later",
            ErrorCategory.INTERNAL: "This appears to be an internal error, please report it"
        }

        base_suggestion = suggestions.get(category, "Please try the operation again")

        # Add severity-specific advice
        if severity == ErrorSeverity.CRITICAL:
            return f"{base_suggestion}. Consider restarting the application."
        elif severity == ErrorSeverity.HIGH:
            return f"{base_suggestion}. You may need administrator privileges."

        return base_suggestion

    def _is_auto_recoverable(self, category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """Determine if an error can be automatically recovered"""
        # Only attempt auto-recovery for low-medium severity errors
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            return False

        # Safe categories for auto-recovery
        safe_categories = [
            ErrorCategory.NETWORK,
            ErrorCategory.FILE_IO,
            ErrorCategory.EXTERNAL
        ]

        return category in safe_categories

    def _log_error(self, error_info: ErrorInfo):
        """Log error to database and file"""
        # Log to database
        with sqlite3.connect(str(self.error_log_file)) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO errors
                (error_id, timestamp, severity, category, message, details, context,
                 stack_trace, user_action, recovery_suggestion, auto_recoverable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                error_info.error_id,
                error_info.timestamp.isoformat(),
                error_info.severity.value,
                error_info.category.value,
                error_info.message,
                error_info.details,
                json.dumps(error_info.context),
                error_info.stack_trace,
                error_info.user_action,
                error_info.recovery_suggestion,
                error_info.auto_recoverable
            ))

        # Log to file
        self.logger.error(
            f"Error {error_info.error_id}: [{error_info.category.value}] "
            f"{error_info.message}",
            extra={
                'error_id': error_info.error_id,
                'severity': error_info.severity.value,
                'category': error_info.category.value
            }
        )

    def _display_error(self, error_info: ErrorInfo):
        """Display error information to the user"""
        # Choose color based on severity
        severity_colors = {
            ErrorSeverity.LOW: "yellow",
            ErrorSeverity.MEDIUM: "yellow",
            ErrorSeverity.HIGH: "red",
            ErrorSeverity.CRITICAL: "bright_red"
        }

        color = severity_colors.get(error_info.severity, "red")

        error_panel = Panel.fit(
            f"[bold {color}]Error: {error_info.message}[/bold {color}]\n\n"
            f"[dim]Error ID: {error_info.error_id}[/dim]\n"
            f"[dim]Category: {error_info.category.value}[/dim]\n"
            f"[dim]Severity: {error_info.severity.value}[/dim]\n\n"
            f"[bold]Suggestion:[/bold] {error_info.recovery_suggestion}",
            title=f"{error_info.severity.value.title()} Error",
            border_style=color
        )

        console.print(error_panel)

    def _attempt_recovery(self, error_info: ErrorInfo):
        """Attempt automatic recovery"""
        applicable_strategies = [
            strategy for strategy in self.recovery_strategies
            if (error_info.category in strategy.applicable_categories and
                error_info.severity.value in [s.value for s in ErrorSeverity
                                             if s.value <= strategy.severity_threshold.value])
        ]

        for strategy in applicable_strategies:
            if strategy.auto_execute:
                console.print(f"[yellow]Attempting automatic recovery: {strategy.description}[/yellow]")

                try:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console
                    ) as progress:
                        task = progress.add_task(f"Executing {strategy.name}...", total=None)

                        success = strategy.recovery_function(error_info)

                        if success:
                            console.print(f"[green]✓ Recovery successful: {strategy.description}[/green]")
                            error_info.recovery_attempted = True
                            error_info.recovery_successful = True
                            self._update_error_recovery_status(error_info)
                            return True
                        else:
                            console.print(f"[red]✗ Recovery failed: {strategy.description}[/red]")

                except Exception as e:
                    console.print(f"[red]Recovery strategy failed: {e}[/red]")
                    continue

        error_info.recovery_attempted = True
        error_info.recovery_successful = False
        self._update_error_recovery_status(error_info)
        return False

    def _suggest_recovery(self, error_info: ErrorInfo):
        """Suggest recovery options to the user"""
        applicable_strategies = [
            strategy for strategy in self.recovery_strategies
            if error_info.category in strategy.applicable_categories
        ]

        if not applicable_strategies:
            return

        console.print(f"[bold yellow]Available Recovery Options:[/bold yellow]")

        for i, strategy in enumerate(applicable_strategies, 1):
            console.print(f"  {i}. {strategy.description}")

        console.print("  0. Skip recovery")

        try:
            choice = console.input("\n[bold]Select recovery option (0-{}): [/bold]".format(len(applicable_strategies)))
            choice_num = int(choice)

            if choice_num == 0:
                return

            if 1 <= choice_num <= len(applicable_strategies):
                strategy = applicable_strategies[choice_num - 1]

                if Confirm.ask(f"Execute recovery strategy: {strategy.description}?"):
                    console.print(f"[yellow]Executing recovery: {strategy.description}[/yellow]")

                    success = strategy.recovery_function(error_info)

                    if success:
                        console.print(f"[green]✓ Recovery successful![/green]")
                        error_info.recovery_attempted = True
                        error_info.recovery_successful = True
                    else:
                        console.print(f"[red]✗ Recovery failed[/red]")
                        error_info.recovery_attempted = True
                        error_info.recovery_successful = False

                    self._update_error_recovery_status(error_info)

        except (ValueError, KeyboardInterrupt):
            console.print("[yellow]Recovery cancelled[/yellow]")

    def _update_error_recovery_status(self, error_info: ErrorInfo):
        """Update error recovery status in database"""
        with sqlite3.connect(str(self.error_log_file)) as conn:
            conn.execute('''
                UPDATE errors
                SET recovery_attempted = ?, recovery_successful = ?
                WHERE error_id = ?
            ''', (error_info.recovery_attempted, error_info.recovery_successful, error_info.error_id))

    # Recovery strategy implementations

    def _recover_missing_dependency(self, error_info: ErrorInfo) -> bool:
        """Recover from missing dependency"""
        import subprocess

        try:
            # Extract package name from error message
            message = error_info.message.lower()
            if 'no module named' in message:
                package_name = message.split("'")[1] if "'" in message else None
                if package_name:
                    result = subprocess.run([sys.executable, '-m', 'pip', 'install', package_name],
                                          capture_output=True, text=True, timeout=120)
                    return result.returncode == 0
        except Exception:
            pass

        return False

    def _recover_git_repository(self, error_info: ErrorInfo) -> bool:
        """Recover git repository issues"""
        import subprocess

        try:
            # Try basic git operations to fix common issues
            commands = [
                ['git', 'status'],
                ['git', 'clean', '-fd'],  # Clean untracked files
                ['git', 'reset', '--hard', 'HEAD']  # Reset to last commit
            ]

            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    continue

            return True
        except Exception:
            return False

    def _recover_file_permissions(self, error_info: ErrorInfo) -> bool:
        """Recover from file permission issues"""
        try:
            # Extract filename from context or error
            filename = error_info.context.get('filename')
            if not filename and hasattr(error_info, 'details'):
                import json
                try:
                    details = json.loads(error_info.details)
                    filename = details.get('filename')
                except:
                    pass

            if filename and os.path.exists(filename):
                # Try to make file readable/writable
                os.chmod(filename, 0o666)
                return True
        except Exception:
            pass

        return False

    def _recover_network_issue(self, error_info: ErrorInfo) -> bool:
        """Recover from network issues with retry logic"""
        import time

        # Simple retry with exponential backoff
        for attempt in range(3):
            time.sleep(2 ** attempt)  # 2, 4, 8 seconds

            # Test basic connectivity
            try:
                import urllib.request
                urllib.request.urlopen('https://www.google.com', timeout=10)
                return True
            except:
                continue

        return False

    def _recover_configuration(self, error_info: ErrorInfo) -> bool:
        """Recover from configuration issues"""
        # This would reset configuration to defaults
        # Implementation depends on specific configuration system
        return False

    def _recover_cleanup_temp_files(self, error_info: ErrorInfo) -> bool:
        """Clean up temporary files"""
        import tempfile
        import shutil

        try:
            temp_dir = Path(tempfile.gettempdir())
            tiny_code_temp = temp_dir / 'tiny_code_temp'

            if tiny_code_temp.exists():
                shutil.rmtree(tiny_code_temp)

            # Clean up .tiny_code cache if it exists
            cache_dir = self.data_dir / 'cache'
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                cache_dir.mkdir()

            return True
        except Exception:
            return False

    def _recover_restart_services(self, error_info: ErrorInfo) -> bool:
        """Restart external services"""
        # This would restart external services like Docker, etc.
        # Implementation depends on specific services
        return False

    # Error analysis and reporting methods

    def get_error_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get error statistics for analysis"""
        with sqlite3.connect(str(self.error_log_file)) as conn:
            cursor = conn.execute('''
                SELECT
                    category,
                    severity,
                    COUNT(*) as count,
                    SUM(CASE WHEN recovery_successful THEN 1 ELSE 0 END) as successful_recoveries
                FROM errors
                WHERE timestamp > datetime('now', '-{} days')
                GROUP BY category, severity
                ORDER BY count DESC
            '''.format(days))

            stats = []
            total_errors = 0
            total_recoveries = 0

            for row in cursor.fetchall():
                category, severity, count, recoveries = row
                stats.append({
                    'category': category,
                    'severity': severity,
                    'count': count,
                    'successful_recoveries': recoveries,
                    'recovery_rate': (recoveries / count) * 100 if count > 0 else 0
                })
                total_errors += count
                total_recoveries += recoveries

            return {
                'total_errors': total_errors,
                'total_recoveries': total_recoveries,
                'overall_recovery_rate': (total_recoveries / total_errors) * 100 if total_errors > 0 else 0,
                'by_category_severity': stats
            }

    def get_recent_errors(self, limit: int = 20) -> List[ErrorInfo]:
        """Get recent errors"""
        with sqlite3.connect(str(self.error_log_file)) as conn:
            cursor = conn.execute('''
                SELECT * FROM errors
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

            errors = []
            for row in cursor.fetchall():
                context = {}
                try:
                    context = json.loads(row[7]) if row[7] else {}
                except:
                    pass

                errors.append(ErrorInfo(
                    error_id=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    severity=ErrorSeverity(row[3]),
                    category=ErrorCategory(row[4]),
                    message=row[5],
                    details=row[6] or "",
                    context=context,
                    stack_trace=row[8],
                    user_action=row[9],
                    recovery_suggestion=row[10],
                    auto_recoverable=bool(row[11]),
                    recovery_attempted=bool(row[12]),
                    recovery_successful=bool(row[13])
                ))

            return errors

# Decorator for automatic error handling
def handle_errors(category: ErrorCategory = ErrorCategory.INTERNAL,
                 auto_recover: bool = True,
                 user_action: str = None):
    """Decorator for automatic error handling"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get the error manager (assumes it's available in context)
                error_manager = getattr(args[0], 'error_manager', None) if args else None

                if error_manager and hasattr(error_manager, 'handle_error'):
                    context = {
                        'function': func.__name__,
                        'args': str(args)[:200],  # Limit length
                        'kwargs': str(kwargs)[:200]
                    }

                    error_manager.handle_error(
                        e, context=context, user_action=user_action, auto_recover=auto_recover
                    )
                else:
                    # Fallback to basic error display
                    console.print(f"[red]Error in {func.__name__}: {e}[/red]")

                raise  # Re-raise the exception

        return wrapper
    return decorator

@contextmanager
def error_context(error_manager: ErrorRecoveryManager, operation: str,
                  category: ErrorCategory = ErrorCategory.INTERNAL,
                  auto_recover: bool = True):
    """Context manager for error handling"""
    try:
        yield
    except Exception as e:
        context = {'operation': operation}
        error_manager.handle_error(e, context=context, user_action=operation, auto_recover=auto_recover)
        raise