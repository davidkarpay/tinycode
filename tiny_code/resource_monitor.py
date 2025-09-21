"""Resource monitoring and management for TinyCode production deployment"""

import os
import sys
import time
import threading
import psutil
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ResourceThresholds:
    """Resource limit thresholds"""
    max_file_handles: int = 100
    max_memory_mb: int = 2048
    max_cpu_percent: float = 80.0
    warning_threshold: float = 0.8  # 80% of max
    cleanup_threshold: float = 0.9  # 90% of max

@dataclass
class ResourceStats:
    """Current resource usage statistics"""
    open_files: int
    memory_mb: float
    cpu_percent: float
    timestamp: datetime
    warnings: List[str]

class FileHandleManager:
    """Manages file handles with automatic cleanup"""

    def __init__(self, max_handles: int = 100):
        self.max_handles = max_handles
        self.open_handles: Dict[str, any] = {}
        self.handle_history: List[Dict] = []
        self.lock = threading.Lock()

    @contextmanager
    def managed_file(self, filepath: str, mode: str = 'r', **kwargs):
        """Context manager for file operations with handle tracking"""
        handle_id = f"{filepath}:{mode}:{id(threading.current_thread())}"

        with self.lock:
            if len(self.open_handles) >= self.max_handles:
                self._cleanup_stale_handles()

                # If still at limit, raise error
                if len(self.open_handles) >= self.max_handles:
                    raise ResourceError(
                        f"Maximum file handles ({self.max_handles}) exceeded. "
                        f"Currently open: {len(self.open_handles)}"
                    )

        try:
            # Open file
            file_handle = open(filepath, mode, **kwargs)

            with self.lock:
                self.open_handles[handle_id] = {
                    'handle': file_handle,
                    'filepath': filepath,
                    'mode': mode,
                    'opened_at': datetime.now(),
                    'thread_id': threading.current_thread().ident
                }

            logger.debug(f"Opened file handle: {handle_id}")
            yield file_handle

        finally:
            # Clean up
            try:
                file_handle.close()
            except:
                pass

            with self.lock:
                if handle_id in self.open_handles:
                    handle_info = self.open_handles.pop(handle_id)
                    self.handle_history.append({
                        'filepath': handle_info['filepath'],
                        'mode': handle_info['mode'],
                        'opened_at': handle_info['opened_at'],
                        'closed_at': datetime.now(),
                        'duration': datetime.now() - handle_info['opened_at']
                    })

            logger.debug(f"Closed file handle: {handle_id}")

    def _cleanup_stale_handles(self):
        """Clean up stale file handles from dead threads"""
        active_threads = {t.ident for t in threading.enumerate()}
        stale_handles = []

        for handle_id, handle_info in self.open_handles.items():
            if handle_info['thread_id'] not in active_threads:
                stale_handles.append(handle_id)

        for handle_id in stale_handles:
            try:
                handle_info = self.open_handles.pop(handle_id)
                handle_info['handle'].close()
                logger.warning(f"Cleaned up stale file handle: {handle_id}")
            except Exception as e:
                logger.error(f"Error cleaning up stale handle {handle_id}: {e}")

    def get_stats(self) -> Dict:
        """Get file handle statistics"""
        with self.lock:
            return {
                'open_handles': len(self.open_handles),
                'max_handles': self.max_handles,
                'utilization': len(self.open_handles) / self.max_handles,
                'handle_details': [
                    {
                        'filepath': info['filepath'],
                        'mode': info['mode'],
                        'opened_at': info['opened_at'].isoformat(),
                        'duration': str(datetime.now() - info['opened_at'])
                    }
                    for info in self.open_handles.values()
                ],
                'recent_history': self.handle_history[-10:]  # Last 10 operations
            }

    def force_cleanup(self):
        """Force cleanup of all open handles"""
        with self.lock:
            for handle_id, handle_info in list(self.open_handles.items()):
                try:
                    handle_info['handle'].close()
                    logger.warning(f"Force closed file handle: {handle_id}")
                except Exception as e:
                    logger.error(f"Error force closing handle {handle_id}: {e}")

            self.open_handles.clear()

class ResourceError(Exception):
    """Exception raised when resource limits are exceeded"""
    pass

class ResourceMonitor:
    """Monitors system resources and enforces limits"""

    def __init__(self, thresholds: Optional[ResourceThresholds] = None):
        self.thresholds = thresholds or ResourceThresholds()
        self.file_manager = FileHandleManager(self.thresholds.max_file_handles)
        self.process = psutil.Process()
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks: List[Callable] = []
        self.stats_history: List[ResourceStats] = []
        self.lock = threading.Lock()

        # Resource usage tracking
        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024
        self.peak_memory = self.baseline_memory
        self.total_files_opened = 0

    def add_callback(self, callback: Callable[[ResourceStats], None]):
        """Add callback for resource warnings"""
        self.callbacks.append(callback)

    def start_monitoring(self, interval: float = 5.0):
        """Start background resource monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Resource monitoring started")

    def stop_monitoring(self):
        """Stop background resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Resource monitoring stopped")

    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                stats = self.get_current_stats()
                self._check_thresholds(stats)

                with self.lock:
                    self.stats_history.append(stats)
                    # Keep only last 1000 stats (about 83 minutes at 5s intervals)
                    if len(self.stats_history) > 1000:
                        self.stats_history = self.stats_history[-1000:]

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                time.sleep(interval)

    def get_current_stats(self) -> ResourceStats:
        """Get current resource usage statistics"""
        try:
            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # CPU usage
            cpu_percent = self.process.cpu_percent()

            # File handles (process-wide)
            try:
                open_files = len(self.process.open_files())
            except (psutil.AccessDenied, OSError):
                # Fall back to our managed count
                open_files = len(self.file_manager.open_handles)

            # Update peak memory
            if memory_mb > self.peak_memory:
                self.peak_memory = memory_mb

            warnings = []

            # Check thresholds
            if memory_mb > self.thresholds.max_memory_mb * self.thresholds.warning_threshold:
                warnings.append(f"High memory usage: {memory_mb:.1f}MB")

            if cpu_percent > self.thresholds.max_cpu_percent * self.thresholds.warning_threshold:
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")

            if open_files > self.thresholds.max_file_handles * self.thresholds.warning_threshold:
                warnings.append(f"High file handle usage: {open_files}")

            return ResourceStats(
                open_files=open_files,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                timestamp=datetime.now(),
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Error getting resource stats: {e}")
            return ResourceStats(
                open_files=0,
                memory_mb=0,
                cpu_percent=0,
                timestamp=datetime.now(),
                warnings=[f"Error getting stats: {e}"]
            )

    def _check_thresholds(self, stats: ResourceStats):
        """Check resource thresholds and trigger callbacks"""
        critical_warnings = []

        # Check memory
        if stats.memory_mb > self.thresholds.max_memory_mb * self.thresholds.cleanup_threshold:
            critical_warnings.append(f"CRITICAL: Memory usage {stats.memory_mb:.1f}MB exceeds {self.thresholds.max_memory_mb * self.thresholds.cleanup_threshold:.1f}MB")
            self._trigger_cleanup("memory")

        # Check file handles
        if stats.open_files > self.thresholds.max_file_handles * self.thresholds.cleanup_threshold:
            critical_warnings.append(f"CRITICAL: File handles {stats.open_files} exceeds {int(self.thresholds.max_file_handles * self.thresholds.cleanup_threshold)}")
            self._trigger_cleanup("file_handles")

        # Check CPU (just warn, don't cleanup)
        if stats.cpu_percent > self.thresholds.max_cpu_percent:
            critical_warnings.append(f"CRITICAL: CPU usage {stats.cpu_percent:.1f}% exceeds {self.thresholds.max_cpu_percent}%")

        # Trigger callbacks for warnings
        if stats.warnings or critical_warnings:
            for callback in self.callbacks:
                try:
                    callback(stats)
                except Exception as e:
                    logger.error(f"Error in resource callback: {e}")

        if critical_warnings:
            logger.critical(f"Resource thresholds exceeded: {critical_warnings}")

    def _trigger_cleanup(self, resource_type: str):
        """Trigger cleanup for specific resource type"""
        if resource_type == "memory":
            self._cleanup_memory()
        elif resource_type == "file_handles":
            self._cleanup_file_handles()

    def _cleanup_memory(self):
        """Trigger memory cleanup"""
        try:
            import gc
            collected = gc.collect()
            logger.warning(f"Memory cleanup triggered, collected {collected} objects")
        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")

    def _cleanup_file_handles(self):
        """Trigger file handle cleanup"""
        try:
            self.file_manager._cleanup_stale_handles()
            logger.warning("File handle cleanup triggered")
        except Exception as e:
            logger.error(f"Error during file handle cleanup: {e}")

    @contextmanager
    def managed_file(self, filepath: str, mode: str = 'r', **kwargs):
        """Context manager for managed file operations"""
        self.total_files_opened += 1
        with self.file_manager.managed_file(filepath, mode, **kwargs) as f:
            yield f

    def get_comprehensive_stats(self) -> Dict:
        """Get comprehensive resource statistics"""
        current_stats = self.get_current_stats()

        return {
            'current': {
                'memory_mb': current_stats.memory_mb,
                'cpu_percent': current_stats.cpu_percent,
                'open_files': current_stats.open_files,
                'warnings': current_stats.warnings,
                'timestamp': current_stats.timestamp.isoformat()
            },
            'thresholds': {
                'max_memory_mb': self.thresholds.max_memory_mb,
                'max_file_handles': self.thresholds.max_file_handles,
                'max_cpu_percent': self.thresholds.max_cpu_percent,
                'warning_threshold': self.thresholds.warning_threshold,
                'cleanup_threshold': self.thresholds.cleanup_threshold
            },
            'historical': {
                'baseline_memory_mb': self.baseline_memory,
                'peak_memory_mb': self.peak_memory,
                'total_files_opened': self.total_files_opened,
                'monitoring_active': self.monitoring
            },
            'file_manager': self.file_manager.get_stats(),
            'recent_stats': [
                {
                    'memory_mb': s.memory_mb,
                    'cpu_percent': s.cpu_percent,
                    'open_files': s.open_files,
                    'timestamp': s.timestamp.isoformat(),
                    'warnings': len(s.warnings)
                }
                for s in self.stats_history[-10:]  # Last 10 readings
            ]
        }

    def emergency_cleanup(self):
        """Perform emergency resource cleanup"""
        logger.critical("Performing emergency resource cleanup")

        # Force close all file handles
        self.file_manager.force_cleanup()

        # Force garbage collection
        import gc
        collected = gc.collect()
        logger.critical(f"Emergency cleanup: collected {collected} objects")

        # Get updated stats
        stats = self.get_current_stats()
        logger.critical(f"Post-cleanup stats: Memory={stats.memory_mb:.1f}MB, Files={stats.open_files}")

# Global resource monitor instance
_resource_monitor = None

def get_resource_monitor() -> ResourceMonitor:
    """Get global resource monitor instance"""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
        _resource_monitor.start_monitoring()
    return _resource_monitor

# Example usage and testing
if __name__ == "__main__":
    # Test resource monitoring
    monitor = ResourceMonitor()

    def warning_callback(stats: ResourceStats):
        print(f"WARNING: {stats.warnings}")

    monitor.add_callback(warning_callback)
    monitor.start_monitoring(interval=1.0)

    try:
        # Test file handle management
        with monitor.managed_file('test_file.txt', 'w') as f:
            f.write("Test content")

        # Show stats
        stats = monitor.get_comprehensive_stats()
        print("Resource Statistics:")
        print(f"Memory: {stats['current']['memory_mb']:.1f}MB")
        print(f"Open Files: {stats['current']['open_files']}")
        print(f"CPU: {stats['current']['cpu_percent']:.1f}%")

        time.sleep(5)

    finally:
        monitor.stop_monitoring()