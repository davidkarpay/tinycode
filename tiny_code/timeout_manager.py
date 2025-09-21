"""Timeout management for safe execution control"""

import signal
import time
import threading
from contextlib import contextmanager
from typing import Optional, Callable, Any
from dataclasses import dataclass
from rich.console import Console

console = Console()

class TimeoutError(Exception):
    """Raised when execution times out"""
    pass

@dataclass
class TimeoutContext:
    """Context information for timeout management"""
    operation_name: str
    timeout_seconds: int
    start_time: float
    warning_threshold: float = 0.8  # Warn at 80% of timeout

class TimeoutManager:
    """Manages execution timeouts with graceful handling"""

    def __init__(self):
        self.active_timeouts = {}
        self.timeout_handlers = {}

    @contextmanager
    def timeout_context(self,
                       operation_name: str,
                       timeout_seconds: int,
                       warning_callback: Optional[Callable] = None,
                       cleanup_callback: Optional[Callable] = None):
        """Context manager for timeout control"""

        if timeout_seconds <= 0:
            # No timeout requested
            yield
            return

        context = TimeoutContext(
            operation_name=operation_name,
            timeout_seconds=timeout_seconds,
            start_time=time.time()
        )

        # Set up signal handler for UNIX systems
        old_handler = None
        if hasattr(signal, 'SIGALRM'):
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Operation '{operation_name}' timed out after {timeout_seconds}s")

            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

        # Start warning timer in separate thread
        warning_timer = None
        if warning_callback:
            warning_time = timeout_seconds * context.warning_threshold
            warning_timer = threading.Timer(warning_time, warning_callback)
            warning_timer.start()

        try:
            self.active_timeouts[operation_name] = context
            yield context

        except TimeoutError:
            console.print(f"[red]⏰ Timeout: {operation_name} exceeded {timeout_seconds}s limit[/red]")
            if cleanup_callback:
                try:
                    cleanup_callback()
                    console.print("[yellow]Cleanup completed[/yellow]")
                except Exception as e:
                    console.print(f"[red]Cleanup failed: {e}[/red]")
            raise

        finally:
            # Clean up
            if hasattr(signal, 'SIGALRM') and old_handler is not None:
                signal.alarm(0)  # Cancel alarm
                signal.signal(signal.SIGALRM, old_handler)

            if warning_timer and warning_timer.is_alive():
                warning_timer.cancel()

            self.active_timeouts.pop(operation_name, None)

    def get_remaining_time(self, operation_name: str) -> Optional[float]:
        """Get remaining time for an active operation"""
        context = self.active_timeouts.get(operation_name)
        if not context:
            return None

        elapsed = time.time() - context.start_time
        remaining = context.timeout_seconds - elapsed
        return max(0, remaining)

    def is_operation_running(self, operation_name: str) -> bool:
        """Check if an operation is currently running with timeout"""
        return operation_name in self.active_timeouts

    def cancel_timeout(self, operation_name: str):
        """Cancel a timeout for an operation"""
        if operation_name in self.active_timeouts:
            # This will be handled by the context manager cleanup
            pass

class ExecutionTimeoutManager(TimeoutManager):
    """Specialized timeout manager for plan execution"""

    def __init__(self, safety_config):
        super().__init__()
        self.safety_config = safety_config

    def get_default_timeout(self) -> int:
        """Get default timeout from safety configuration"""
        return self.safety_config.get_timeout_seconds()

    @contextmanager
    def execution_timeout(self,
                         plan_id: str,
                         timeout_override: Optional[int] = None,
                         cleanup_callback: Optional[Callable] = None):
        """Timeout context specifically for plan execution"""

        timeout_seconds = timeout_override or self.get_default_timeout()
        operation_name = f"plan_execution_{plan_id}"

        def warning_callback():
            remaining = self.get_remaining_time(operation_name)
            if remaining and remaining > 0:
                console.print(f"[yellow]⚠️  Execution warning: {remaining:.0f}s remaining for plan {plan_id}[/yellow]")

        with self.timeout_context(
            operation_name=operation_name,
            timeout_seconds=timeout_seconds,
            warning_callback=warning_callback,
            cleanup_callback=cleanup_callback
        ) as context:
            yield context

    @contextmanager
    def action_timeout(self,
                      action_id: str,
                      action_timeout: int = 60,
                      cleanup_callback: Optional[Callable] = None):
        """Timeout context for individual actions"""

        operation_name = f"action_{action_id}"

        def warning_callback():
            remaining = self.get_remaining_time(operation_name)
            if remaining and remaining > 0:
                console.print(f"[yellow]⚠️  Action warning: {remaining:.0f}s remaining for action {action_id}[/yellow]")

        with self.timeout_context(
            operation_name=operation_name,
            timeout_seconds=action_timeout,
            warning_callback=warning_callback,
            cleanup_callback=cleanup_callback
        ) as context:
            yield context

    def show_active_operations(self):
        """Display currently active timeout operations"""
        if not self.active_timeouts:
            console.print("[dim]No active timeout operations[/dim]")
            return

        from rich.table import Table
        table = Table(title="Active Timeout Operations")
        table.add_column("Operation", style="cyan")
        table.add_column("Elapsed", style="yellow")
        table.add_column("Remaining", style="green")
        table.add_column("Timeout", style="red")

        for op_name, context in self.active_timeouts.items():
            elapsed = time.time() - context.start_time
            remaining = max(0, context.timeout_seconds - elapsed)

            table.add_row(
                op_name,
                f"{elapsed:.1f}s",
                f"{remaining:.1f}s",
                f"{context.timeout_seconds}s"
            )

        console.print(table)