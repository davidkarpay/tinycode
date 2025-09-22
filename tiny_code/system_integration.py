"""
System Integration Tools for TinyCode
Provides environment variable management, process monitoring, and system utilities
"""

import os
import sys
import psutil
import subprocess
import platform
import shutil
import socket
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum
import json
import time
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.live import Live

console = Console()

class ProcessStatus(Enum):
    """Process status types"""
    RUNNING = "running"
    SLEEPING = "sleeping"
    DISK_SLEEP = "disk-sleep"
    STOPPED = "stopped"
    TRACING_STOP = "tracing-stop"
    ZOMBIE = "zombie"
    DEAD = "dead"
    WAKE_KILL = "wake-kill"
    WAKING = "waking"
    IDLE = "idle"
    LOCKED = "locked"
    WAITING = "waiting"

@dataclass
class ProcessInfo:
    """Information about a system process"""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    create_time: datetime
    cmdline: List[str]
    parent_pid: Optional[int]
    username: Optional[str]

@dataclass
class EnvironmentVariable:
    """Information about an environment variable"""
    name: str
    value: str
    is_path: bool
    is_sensitive: bool

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_total: int
    memory_available: int
    memory_percent: float
    disk_total: int
    disk_free: int
    disk_percent: float
    network_sent: int
    network_recv: int
    boot_time: datetime
    load_average: Optional[Tuple[float, float, float]]

@dataclass
class ServiceInfo:
    """Information about a system service"""
    name: str
    status: str
    port: Optional[int]
    pid: Optional[int]
    description: str

class SystemIntegration:
    """Advanced system integration tools with monitoring and management capabilities"""

    def __init__(self):
        self.sensitive_env_patterns = [
            'password', 'secret', 'key', 'token', 'credential', 'auth',
            'api_key', 'private', 'cert', 'ssl', 'tls'
        ]

    def get_environment_variables(self, filter_pattern: Optional[str] = None,
                                show_sensitive: bool = False) -> List[EnvironmentVariable]:
        """Get environment variables with filtering and sensitivity detection"""
        variables = []

        for name, value in os.environ.items():
            # Filter by pattern if provided
            if filter_pattern and filter_pattern.lower() not in name.lower():
                continue

            # Detect if this is a PATH-like variable
            is_path = name.upper().endswith('PATH') or ':' in value or ';' in value

            # Detect sensitive variables
            is_sensitive = any(pattern.lower() in name.lower() for pattern in self.sensitive_env_patterns)

            # Skip sensitive vars unless explicitly requested
            if is_sensitive and not show_sensitive:
                value = "[HIDDEN]"

            variables.append(EnvironmentVariable(
                name=name,
                value=value,
                is_path=is_path,
                is_sensitive=is_sensitive
            ))

        return sorted(variables, key=lambda x: x.name)

    def set_environment_variable(self, name: str, value: str,
                                persistent: bool = False) -> bool:
        """Set an environment variable (session or persistent)"""
        try:
            # Set for current session
            os.environ[name] = value

            if persistent:
                # For persistent vars, we'd typically modify shell profiles
                # This is a simplified implementation - real implementation would
                # detect shell type and modify appropriate config files
                console.print("[yellow]Note: Persistent env vars require shell profile modification[/yellow]")
                console.print(f"[dim]Add this to your shell profile: export {name}='{value}'[/dim]")

            return True
        except Exception as e:
            console.print(f"[red]Error setting environment variable: {e}[/red]")
            return False

    def get_system_metrics(self) -> SystemMetrics:
        """Get comprehensive system performance metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()

        # Disk usage (for root filesystem)
        disk = psutil.disk_usage('/')

        # Network I/O
        network = psutil.net_io_counters()

        # Boot time
        boot_time = datetime.fromtimestamp(psutil.boot_time())

        # Load average (Unix-like systems only)
        load_avg = None
        try:
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
        except:
            pass

        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_total=memory.total,
            memory_available=memory.available,
            memory_percent=memory.percent,
            disk_total=disk.total,
            disk_free=disk.free,
            disk_percent=disk.percent,
            network_sent=network.bytes_sent,
            network_recv=network.bytes_recv,
            boot_time=boot_time,
            load_average=load_avg
        )

    def get_processes(self, filter_name: Optional[str] = None,
                     sort_by: str = 'cpu', limit: int = 20) -> List[ProcessInfo]:
        """Get running processes with filtering and sorting"""
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent',
                                       'memory_percent', 'memory_info', 'create_time',
                                       'cmdline', 'ppid', 'username']):
            try:
                info = proc.info

                # Filter by name if provided
                if filter_name and filter_name.lower() not in info['name'].lower():
                    continue

                # Convert memory to MB
                memory_mb = info['memory_info'].rss / 1024 / 1024 if info['memory_info'] else 0

                # Create time
                create_time = datetime.fromtimestamp(info['create_time'])

                processes.append(ProcessInfo(
                    pid=info['pid'],
                    name=info['name'],
                    status=info['status'],
                    cpu_percent=info['cpu_percent'] or 0,
                    memory_percent=info['memory_percent'] or 0,
                    memory_mb=memory_mb,
                    create_time=create_time,
                    cmdline=info['cmdline'] or [],
                    parent_pid=info['ppid'],
                    username=info['username']
                ))

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort processes
        if sort_by == 'cpu':
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
        elif sort_by == 'memory':
            processes.sort(key=lambda x: x.memory_percent, reverse=True)
        elif sort_by == 'name':
            processes.sort(key=lambda x: x.name)
        elif sort_by == 'pid':
            processes.sort(key=lambda x: x.pid)

        return processes[:limit]

    def kill_process(self, pid: int, force: bool = False) -> bool:
        """Kill a process by PID"""
        try:
            proc = psutil.Process(pid)
            if force:
                proc.kill()
            else:
                proc.terminate()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            console.print(f"[red]Error killing process {pid}: {e}[/red]")
            return False

    def monitor_process(self, pid: int, duration: int = 30) -> Dict[str, Any]:
        """Monitor a specific process for a duration"""
        try:
            proc = psutil.Process(pid)
            metrics = {
                'timestamps': [],
                'cpu_percent': [],
                'memory_mb': [],
                'memory_percent': []
            }

            start_time = time.time()
            while time.time() - start_time < duration:
                try:
                    timestamp = datetime.now()
                    cpu = proc.cpu_percent()
                    memory_info = proc.memory_info()
                    memory_percent = proc.memory_percent()

                    metrics['timestamps'].append(timestamp)
                    metrics['cpu_percent'].append(cpu)
                    metrics['memory_mb'].append(memory_info.rss / 1024 / 1024)
                    metrics['memory_percent'].append(memory_percent)

                    time.sleep(1)
                except psutil.NoSuchProcess:
                    break

            return metrics

        except psutil.NoSuchProcess:
            return {}

    def get_network_connections(self, process_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get network connections, optionally filtered by process"""
        connections = []

        for conn in psutil.net_connections(kind='inet'):
            try:
                # Get process info if available
                proc_name = "unknown"
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        proc_name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # Filter by process name if provided
                if process_name and process_name.lower() not in proc_name.lower():
                    continue

                connections.append({
                    'pid': conn.pid,
                    'process': proc_name,
                    'family': conn.family.name if conn.family else 'unknown',
                    'type': conn.type.name if conn.type else 'unknown',
                    'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else 'N/A',
                    'remote_addr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else 'N/A',
                    'status': conn.status
                })

            except Exception:
                continue

        return connections

    def check_port(self, port: int, host: str = 'localhost') -> bool:
        """Check if a port is open"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception:
            return False

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        info = {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'architecture': platform.architecture(),
            },
            'python': {
                'version': sys.version,
                'executable': sys.executable,
                'path': sys.path[:5],  # First 5 paths
            },
            'hardware': {
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            },
            'disk_usage': {}
        }

        # Get disk usage for all mounted filesystems
        for disk in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(disk.mountpoint)
                info['disk_usage'][disk.mountpoint] = {
                    'total_gb': round(usage.total / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2),
                    'percent': round((usage.used / usage.total) * 100, 1)
                }
            except PermissionError:
                continue

        return info

    def run_command(self, command: str, shell: bool = True,
                   timeout: int = 30, capture_output: bool = True) -> Dict[str, Any]:
        """Run a system command with comprehensive result capture"""
        try:
            start_time = time.time()

            if shell:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=capture_output,
                    text=True,
                    timeout=timeout
                )
            else:
                result = subprocess.run(
                    command.split(),
                    capture_output=capture_output,
                    text=True,
                    timeout=timeout
                )

            end_time = time.time()

            return {
                'command': command,
                'returncode': result.returncode,
                'stdout': result.stdout if capture_output else '',
                'stderr': result.stderr if capture_output else '',
                'execution_time': round(end_time - start_time, 3),
                'success': result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                'command': command,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'execution_time': timeout,
                'success': False
            }
        except Exception as e:
            return {
                'command': command,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': 0,
                'success': False
            }

    def find_executables(self, pattern: str) -> List[Dict[str, str]]:
        """Find executable files in PATH matching a pattern"""
        executables = []

        # Get PATH directories
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)

        for path_dir in path_dirs:
            if not os.path.isdir(path_dir):
                continue

            try:
                for file_name in os.listdir(path_dir):
                    if pattern.lower() in file_name.lower():
                        full_path = os.path.join(path_dir, file_name)
                        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                            executables.append({
                                'name': file_name,
                                'path': full_path,
                                'directory': path_dir
                            })
            except PermissionError:
                continue

        return sorted(executables, key=lambda x: x['name'])

    def check_dependencies(self, dependencies: List[str]) -> Dict[str, Dict[str, Any]]:
        """Check if system dependencies are available"""
        results = {}

        for dep in dependencies:
            result = {
                'available': False,
                'path': None,
                'version': None,
                'error': None
            }

            # Check if executable exists in PATH
            path = shutil.which(dep)
            if path:
                result['available'] = True
                result['path'] = path

                # Try to get version
                try:
                    version_result = subprocess.run(
                        [dep, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if version_result.returncode == 0:
                        # Extract first line of version output
                        version_line = version_result.stdout.split('\n')[0]
                        result['version'] = version_line.strip()
                except:
                    # Try alternative version commands
                    for version_cmd in ['-v', '-V', 'version']:
                        try:
                            version_result = subprocess.run(
                                [dep, version_cmd],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if version_result.returncode == 0:
                                version_line = version_result.stdout.split('\n')[0]
                                result['version'] = version_line.strip()
                                break
                        except:
                            continue
            else:
                result['error'] = f"'{dep}' not found in PATH"

            results[dep] = result

        return results

    def get_development_environment_info(self) -> Dict[str, Any]:
        """Get information about the development environment"""
        common_tools = [
            'python', 'python3', 'pip', 'pip3', 'node', 'npm', 'yarn',
            'git', 'docker', 'docker-compose', 'java', 'javac', 'go',
            'rust', 'cargo', 'ruby', 'gem', 'php', 'composer'
        ]

        tool_status = self.check_dependencies(common_tools)

        # Get virtual environment info
        venv_info = {
            'active': 'VIRTUAL_ENV' in os.environ,
            'path': os.environ.get('VIRTUAL_ENV'),
            'prompt': os.environ.get('VIRTUAL_ENV_PROMPT')
        }

        # Get common environment variables
        important_vars = [
            'PATH', 'PYTHONPATH', 'NODE_PATH', 'JAVA_HOME', 'GOPATH',
            'VIRTUAL_ENV', 'CONDA_DEFAULT_ENV'
        ]

        env_vars = {}
        for var in important_vars:
            if var in os.environ:
                env_vars[var] = os.environ[var]

        return {
            'tools': tool_status,
            'virtual_environment': venv_info,
            'environment_variables': env_vars,
            'current_directory': os.getcwd(),
            'user': os.environ.get('USER') or os.environ.get('USERNAME'),
            'shell': os.environ.get('SHELL'),
            'term': os.environ.get('TERM')
        }

    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.1f} PB"

    def get_resource_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of current resource usage"""
        metrics = self.get_system_metrics()

        # Get top processes by CPU and memory
        top_cpu = self.get_processes(sort_by='cpu', limit=5)
        top_memory = self.get_processes(sort_by='memory', limit=5)

        return {
            'system_metrics': metrics,
            'top_cpu_processes': [
                {
                    'name': p.name,
                    'pid': p.pid,
                    'cpu_percent': p.cpu_percent,
                    'memory_mb': round(p.memory_mb, 1)
                }
                for p in top_cpu
            ],
            'top_memory_processes': [
                {
                    'name': p.name,
                    'pid': p.pid,
                    'cpu_percent': p.cpu_percent,
                    'memory_mb': round(p.memory_mb, 1)
                }
                for p in top_memory
            ]
        }