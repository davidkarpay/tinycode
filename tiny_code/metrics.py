"""Metrics collection and resource tracking system for TinyCode"""

import time
import json
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
import os

@dataclass
class CommandMetric:
    """Metrics for a single command execution"""
    command_name: str
    timestamp: float
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    memory_usage_mb: float = 0
    cpu_percent: float = 0
    files_modified: int = 0
    files_read: int = 0

@dataclass
class SessionMetrics:
    """Metrics for an entire session"""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    total_commands: int = 0
    successful_commands: int = 0
    failed_commands: int = 0
    total_execution_time: float = 0
    files_modified: int = 0
    files_read: int = 0
    bash_commands: int = 0
    llm_requests: int = 0
    peak_memory_mb: float = 0
    total_cpu_time: float = 0

@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time"""
    timestamp: float
    memory_usage_mb: float
    cpu_percent: float
    disk_usage_percent: float
    open_files: int
    network_connections: int

class MetricsCollector:
    """Collects and manages metrics for TinyCode operations"""

    def __init__(self, session_id: Optional[str] = None, storage_path: Optional[str] = None):
        """
        Initialize metrics collector

        Args:
            session_id: Unique identifier for this session
            storage_path: Path to store metrics data
        """
        self.session_id = session_id or f"session_{int(time.time())}"
        self.storage_path = Path(storage_path or "data/metrics")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Current session metrics
        self.session_metrics = SessionMetrics(
            session_id=self.session_id,
            start_time=time.time()
        )

        # Command history for this session
        self.command_history: List[CommandMetric] = []

        # Resource monitoring
        self.resource_snapshots: deque = deque(maxlen=1000)  # Keep last 1000 snapshots
        self.monitoring_enabled = True
        self.monitoring_interval = 5.0  # seconds

        # Limits and warnings
        self.memory_warning_mb = 512
        self.cpu_warning_percent = 80
        self.command_count_warning = 100
        self.execution_time_warning = 300  # 5 minutes

        # Callbacks for warnings
        self.warning_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []

        # Start resource monitoring
        self._start_resource_monitoring()

    def record_command(self, command_name: str, execution_time: float,
                      success: bool, error_message: Optional[str] = None,
                      files_modified: int = 0, files_read: int = 0) -> None:
        """Record a command execution"""
        # Get current resource usage
        try:
            process = psutil.Process()
            memory_usage = process.memory_info().rss / (1024 * 1024)  # Convert to MB
            cpu_percent = process.cpu_percent()
        except Exception:
            memory_usage = 0
            cpu_percent = 0

        # Create command metric
        metric = CommandMetric(
            command_name=command_name,
            timestamp=time.time(),
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            memory_usage_mb=memory_usage,
            cpu_percent=cpu_percent,
            files_modified=files_modified,
            files_read=files_read
        )

        # Add to history
        self.command_history.append(metric)

        # Update session metrics
        self.session_metrics.total_commands += 1
        if success:
            self.session_metrics.successful_commands += 1
        else:
            self.session_metrics.failed_commands += 1

        self.session_metrics.total_execution_time += execution_time
        self.session_metrics.files_modified += files_modified
        self.session_metrics.files_read += files_read

        if command_name.startswith("bash") or command_name in ["run", "execute"]:
            self.session_metrics.bash_commands += 1

        # Update peak memory
        if memory_usage > self.session_metrics.peak_memory_mb:
            self.session_metrics.peak_memory_mb = memory_usage

        # Check for warnings
        self._check_warnings(metric)

        # Persist metrics periodically
        if self.session_metrics.total_commands % 10 == 0:
            self.save_session_metrics()

    def record_llm_request(self, tokens_used: int = 0, response_time: float = 0) -> None:
        """Record an LLM request"""
        self.session_metrics.llm_requests += 1
        # Could extend to track token usage if available

    def record_resource_snapshot(self) -> ResourceSnapshot:
        """Record current resource usage"""
        try:
            # System-wide metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            disk = psutil.disk_usage('/')

            # Process-specific metrics
            process = psutil.Process()
            open_files = len(process.open_files())

            # Network connections (system-wide)
            try:
                network_connections = len(psutil.net_connections())
            except Exception:
                network_connections = 0

            snapshot = ResourceSnapshot(
                timestamp=time.time(),
                memory_usage_mb=memory.used / (1024 * 1024),
                cpu_percent=cpu_percent,
                disk_usage_percent=disk.percent,
                open_files=open_files,
                network_connections=network_connections
            )

            self.resource_snapshots.append(snapshot)
            return snapshot

        except Exception as e:
            # If we can't get system metrics, create a minimal snapshot
            return ResourceSnapshot(
                timestamp=time.time(),
                memory_usage_mb=0,
                cpu_percent=0,
                disk_usage_percent=0,
                open_files=0,
                network_connections=0
            )

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session metrics"""
        current_time = time.time()
        session_duration = current_time - self.session_metrics.start_time

        # Calculate success rate
        success_rate = 0
        if self.session_metrics.total_commands > 0:
            success_rate = self.session_metrics.successful_commands / self.session_metrics.total_commands

        # Calculate average execution time
        avg_execution_time = 0
        if self.session_metrics.total_commands > 0:
            avg_execution_time = self.session_metrics.total_execution_time / self.session_metrics.total_commands

        # Get recent command distribution
        recent_commands = self.command_history[-20:] if self.command_history else []
        command_distribution = defaultdict(int)
        for cmd in recent_commands:
            command_distribution[cmd.command_name] += 1

        # Get current resource usage
        latest_snapshot = self.resource_snapshots[-1] if self.resource_snapshots else None

        return {
            "session_id": self.session_id,
            "session_duration_minutes": session_duration / 60,
            "total_commands": self.session_metrics.total_commands,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "files_modified": self.session_metrics.files_modified,
            "files_read": self.session_metrics.files_read,
            "bash_commands": self.session_metrics.bash_commands,
            "llm_requests": self.session_metrics.llm_requests,
            "peak_memory_mb": self.session_metrics.peak_memory_mb,
            "command_distribution": dict(command_distribution),
            "current_resources": asdict(latest_snapshot) if latest_snapshot else None,
            "warnings_triggered": self._get_current_warnings()
        }

    def get_performance_insights(self) -> List[str]:
        """Get performance insights and recommendations"""
        insights = []

        # Check command success rate
        if self.session_metrics.total_commands > 5:
            success_rate = self.session_metrics.successful_commands / self.session_metrics.total_commands
            if success_rate < 0.8:
                insights.append(f"Low success rate ({success_rate:.1%}). Consider reviewing error messages for patterns.")

        # Check memory usage
        if self.session_metrics.peak_memory_mb > self.memory_warning_mb:
            insights.append(f"High memory usage detected ({self.session_metrics.peak_memory_mb:.1f}MB). Consider processing smaller chunks of data.")

        # Check command frequency
        if self.session_metrics.total_commands > self.command_count_warning:
            insights.append(f"High command count ({self.session_metrics.total_commands}). Consider combining operations or using batch processing.")

        # Check execution time
        if self.session_metrics.total_execution_time > self.execution_time_warning:
            avg_time = self.session_metrics.total_execution_time / self.session_metrics.total_commands
            insights.append(f"Long total execution time. Average command time: {avg_time:.2f}s")

        # Check for repeated failed commands
        if len(self.command_history) > 10:
            recent_failures = [cmd for cmd in self.command_history[-10:] if not cmd.success]
            if len(recent_failures) > 5:
                insights.append("Many recent failures detected. Consider reviewing your approach.")

        # Resource usage trends
        if len(self.resource_snapshots) > 10:
            recent_snapshots = list(self.resource_snapshots)[-10:]
            avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
            if avg_cpu > self.cpu_warning_percent:
                insights.append(f"High CPU usage detected ({avg_cpu:.1f}%). Consider optimizing operations.")

        return insights if insights else ["Performance looks good! No issues detected."]

    def save_session_metrics(self) -> None:
        """Save current session metrics to file"""
        try:
            metrics_file = self.storage_path / f"{self.session_id}.json"
            summary = self.get_session_summary()

            # Add command history
            summary["command_history"] = [asdict(cmd) for cmd in self.command_history]

            # Add resource snapshots (recent ones only)
            recent_snapshots = list(self.resource_snapshots)[-100:]  # Last 100 snapshots
            summary["resource_snapshots"] = [asdict(snapshot) for snapshot in recent_snapshots]

            with open(metrics_file, 'w') as f:
                json.dump(summary, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save metrics: {e}")

    def load_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load metrics from a previous session"""
        try:
            metrics_file = self.storage_path / f"{session_id}.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def get_historical_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of metrics over the last N days"""
        cutoff_time = time.time() - (days * 24 * 3600)

        total_sessions = 0
        total_commands = 0
        total_success = 0
        total_execution_time = 0

        # Scan all metric files
        for metrics_file in self.storage_path.glob("*.json"):
            try:
                with open(metrics_file, 'r') as f:
                    data = json.load(f)

                # Check if session is within time range
                session_start = data.get("session_start_time", 0)
                if session_start < cutoff_time:
                    continue

                total_sessions += 1
                total_commands += data.get("total_commands", 0)
                total_success += data.get("successful_commands", 0)
                total_execution_time += data.get("total_execution_time", 0)

            except Exception:
                continue

        success_rate = total_success / total_commands if total_commands > 0 else 0
        avg_execution_time = total_execution_time / total_commands if total_commands > 0 else 0

        return {
            "days": days,
            "total_sessions": total_sessions,
            "total_commands": total_commands,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "commands_per_session": total_commands / total_sessions if total_sessions > 0 else 0
        }

    def add_warning_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add a callback function to be called when warnings are triggered"""
        self.warning_callbacks.append(callback)

    def _check_warnings(self, metric: CommandMetric) -> None:
        """Check if any warnings should be triggered"""
        warnings = []

        # Memory warning
        if metric.memory_usage_mb > self.memory_warning_mb:
            warnings.append(("high_memory", {
                "current_mb": metric.memory_usage_mb,
                "limit_mb": self.memory_warning_mb,
                "command": metric.command_name
            }))

        # CPU warning
        if metric.cpu_percent > self.cpu_warning_percent:
            warnings.append(("high_cpu", {
                "current_percent": metric.cpu_percent,
                "limit_percent": self.cpu_warning_percent,
                "command": metric.command_name
            }))

        # Execution time warning
        if metric.execution_time > 30:  # 30 seconds
            warnings.append(("slow_command", {
                "execution_time": metric.execution_time,
                "command": metric.command_name
            }))

        # Command count warning
        if self.session_metrics.total_commands > self.command_count_warning:
            warnings.append(("high_command_count", {
                "total_commands": self.session_metrics.total_commands,
                "limit": self.command_count_warning
            }))

        # Trigger callbacks for each warning
        for warning_type, warning_data in warnings:
            for callback in self.warning_callbacks:
                try:
                    callback(warning_type, warning_data)
                except Exception:
                    pass  # Don't let callback errors break metrics collection

    def _get_current_warnings(self) -> List[Dict[str, Any]]:
        """Get list of current warnings"""
        warnings = []
        current_time = time.time()

        # Check overall session metrics
        if self.session_metrics.peak_memory_mb > self.memory_warning_mb:
            warnings.append({
                "type": "high_memory",
                "message": f"Peak memory usage: {self.session_metrics.peak_memory_mb:.1f}MB",
                "severity": "warning"
            })

        if self.session_metrics.total_commands > self.command_count_warning:
            warnings.append({
                "type": "high_command_count",
                "message": f"High command count: {self.session_metrics.total_commands}",
                "severity": "info"
            })

        session_duration = current_time - self.session_metrics.start_time
        if session_duration > 3600:  # 1 hour
            warnings.append({
                "type": "long_session",
                "message": f"Long session duration: {session_duration/3600:.1f} hours",
                "severity": "info"
            })

        return warnings

    def _start_resource_monitoring(self) -> None:
        """Start background resource monitoring"""
        def monitor():
            while self.monitoring_enabled:
                try:
                    self.record_resource_snapshot()
                    time.sleep(self.monitoring_interval)
                except Exception:
                    time.sleep(self.monitoring_interval)

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop resource monitoring and finalize session"""
        self.monitoring_enabled = False
        self.session_metrics.end_time = time.time()
        self.save_session_metrics()

    def __del__(self):
        """Cleanup when collector is destroyed"""
        try:
            self.stop_monitoring()
        except Exception:
            pass

# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector

def record_command_metric(command_name: str, execution_time: float, success: bool,
                         error_message: Optional[str] = None, **kwargs) -> None:
    """Convenience function to record a command metric"""
    collector = get_metrics_collector()
    collector.record_command(command_name, execution_time, success, error_message, **kwargs)

def get_session_summary() -> Dict[str, Any]:
    """Get summary of current session"""
    collector = get_metrics_collector()
    return collector.get_session_summary()

def get_performance_insights() -> List[str]:
    """Get performance insights for current session"""
    collector = get_metrics_collector()
    return collector.get_performance_insights()