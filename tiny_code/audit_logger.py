"""Comprehensive audit logging system for TinyCode"""

import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from rich.console import Console

console = Console()

class AuditEventType(Enum):
    """Types of audit events"""
    PLAN_CREATED = "plan_created"
    PLAN_APPROVED = "plan_approved"
    PLAN_REJECTED = "plan_rejected"
    PLAN_EXECUTED = "plan_executed"
    ACTION_EXECUTED = "action_executed"
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    COMMAND_EXECUTED = "command_executed"
    BACKUP_CREATED = "backup_created"
    ROLLBACK_EXECUTED = "rollback_executed"
    SAFETY_VIOLATION = "safety_violation"
    TIMEOUT_OCCURRED = "timeout_occurred"
    ERROR_OCCURRED = "error_occurred"
    MODE_CHANGED = "mode_changed"
    CONFIG_CHANGED = "config_changed"

class AuditSeverity(Enum):
    """Severity levels for audit events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Individual audit event"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_context: Dict[str, Any]
    operation_context: Dict[str, Any]
    details: Dict[str, Any]
    hash_chain: str
    previous_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class AuditSummary:
    """Summary of audit log analysis"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    time_range: Dict[str, str]
    integrity_status: str
    recent_critical_events: List[Dict[str, Any]]

class AuditLogger:
    """Comprehensive audit logging with hash chain integrity"""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path("data/audit_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.current_log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self.index_file = self.log_dir / "audit_index.json"
        self.integrity_file = self.log_dir / "integrity_chain.json"

        self.last_hash = self._load_last_hash()
        self.session_id = self._generate_session_id()

        # Initialize audit session
        self._log_session_start()

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return hashlib.sha256(f"{datetime.now().isoformat()}{time.time()}".encode()).hexdigest()[:16]

    def _load_last_hash(self) -> Optional[str]:
        """Load the last hash from integrity chain"""
        try:
            if self.integrity_file.exists():
                with open(self.integrity_file, 'r') as f:
                    data = json.load(f)
                    return data.get('last_hash')
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load integrity chain: {e}[/yellow]")
        return None

    def _save_integrity_hash(self, event_hash: str):
        """Save hash to integrity chain"""
        try:
            integrity_data = {
                'last_hash': event_hash,
                'updated_at': datetime.now().isoformat(),
                'session_id': self.session_id
            }
            with open(self.integrity_file, 'w') as f:
                json.dump(integrity_data, f, indent=2)
        except Exception as e:
            console.print(f"[red]Error saving integrity hash: {e}[/red]")

    def _calculate_event_hash(self, event: AuditEvent) -> str:
        """Calculate hash for event including chain integrity"""
        event_data = event.to_dict()
        # Remove hash_chain from calculation to avoid circular dependency
        event_data.pop('hash_chain', None)

        # Include previous hash for chain integrity
        chain_data = f"{json.dumps(event_data, sort_keys=True)}{self.last_hash or ''}"
        return hashlib.sha256(chain_data.encode()).hexdigest()

    def _log_session_start(self):
        """Log audit session start"""
        self.log_event(
            event_type=AuditEventType.CONFIG_CHANGED,
            severity=AuditSeverity.INFO,
            details={
                "action": "audit_session_started",
                "session_id": self.session_id,
                "log_file": str(self.current_log_file)
            }
        )

    def log_event(self,
                  event_type: AuditEventType,
                  severity: AuditSeverity = AuditSeverity.INFO,
                  operation_context: Optional[Dict[str, Any]] = None,
                  details: Optional[Dict[str, Any]] = None,
                  user_context: Optional[Dict[str, Any]] = None) -> str:
        """Log an audit event"""

        # Generate event ID
        event_id = hashlib.sha256(f"{datetime.now().isoformat()}{event_type.value}{time.time()}".encode()).hexdigest()[:16]

        # Create event
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
            user_context=user_context or {},
            operation_context=operation_context or {},
            details=details or {},
            hash_chain="",  # Will be calculated
            previous_hash=self.last_hash
        )

        # Calculate hash chain
        event.hash_chain = self._calculate_event_hash(event)

        # Write to log file
        try:
            with open(self.current_log_file, 'a') as f:
                f.write(json.dumps(event.to_dict()) + '\n')

            # Update integrity chain
            self._save_integrity_hash(event.hash_chain)
            self.last_hash = event.hash_chain

            # Update index
            self._update_index(event)

        except Exception as e:
            console.print(f"[red]Error writing audit log: {e}[/red]")

        return event_id

    def _update_index(self, event: AuditEvent):
        """Update audit log index"""
        try:
            index_data = {}
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    index_data = json.load(f)

            # Update statistics
            stats = index_data.setdefault('statistics', {
                'total_events': 0,
                'events_by_type': {},
                'events_by_severity': {},
                'last_updated': None
            })

            stats['total_events'] += 1
            stats['events_by_type'][event.event_type.value] = stats['events_by_type'].get(event.event_type.value, 0) + 1
            stats['events_by_severity'][event.severity.value] = stats['events_by_severity'].get(event.severity.value, 0) + 1
            stats['last_updated'] = datetime.now().isoformat()

            # Track recent critical events
            if event.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
                recent_critical = index_data.setdefault('recent_critical', [])
                recent_critical.append({
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'severity': event.severity.value,
                    'timestamp': event.timestamp.isoformat(),
                    'details': event.details
                })
                # Keep only last 50 critical events
                index_data['recent_critical'] = recent_critical[-50:]

            with open(self.index_file, 'w') as f:
                json.dump(index_data, f, indent=2)

        except Exception as e:
            console.print(f"[red]Error updating audit index: {e}[/red]")

    def log_plan_event(self, plan_id: str, event_type: AuditEventType, details: Dict[str, Any]):
        """Log plan-related events"""
        self.log_event(
            event_type=event_type,
            severity=AuditSeverity.INFO,
            operation_context={'plan_id': plan_id},
            details=details
        )

    def log_execution_event(self, plan_id: str, action_id: str, event_type: AuditEventType, details: Dict[str, Any]):
        """Log execution-related events"""
        severity = AuditSeverity.ERROR if event_type == AuditEventType.ERROR_OCCURRED else AuditSeverity.INFO

        self.log_event(
            event_type=event_type,
            severity=severity,
            operation_context={'plan_id': plan_id, 'action_id': action_id},
            details=details
        )

    def log_safety_violation(self, violation_type: str, details: Dict[str, Any]):
        """Log safety violations"""
        self.log_event(
            event_type=AuditEventType.SAFETY_VIOLATION,
            severity=AuditSeverity.WARNING,
            details={'violation_type': violation_type, **details}
        )

    def log_file_operation(self, file_path: str, operation: str, details: Dict[str, Any]):
        """Log file operations"""
        event_type_map = {
            'create': AuditEventType.FILE_CREATED,
            'modify': AuditEventType.FILE_MODIFIED,
            'delete': AuditEventType.FILE_DELETED
        }

        event_type = event_type_map.get(operation, AuditEventType.FILE_MODIFIED)

        self.log_event(
            event_type=event_type,
            severity=AuditSeverity.INFO,
            operation_context={'file_path': file_path, 'operation': operation},
            details=details
        )

    def verify_integrity(self) -> bool:
        """Verify audit log integrity using hash chain"""
        try:
            if not self.current_log_file.exists():
                return True  # Empty log is valid

            events = []
            with open(self.current_log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))

            if not events:
                return True

            # Verify hash chain
            previous_hash = None
            for event_data in events:
                expected_hash = self._calculate_hash_for_verification(event_data, previous_hash)
                if expected_hash != event_data.get('hash_chain'):
                    console.print(f"[red]Integrity violation detected in event {event_data.get('event_id')}[/red]")
                    return False
                previous_hash = event_data['hash_chain']

            return True

        except Exception as e:
            console.print(f"[red]Error verifying integrity: {e}[/red]")
            return False

    def _calculate_hash_for_verification(self, event_data: Dict[str, Any], previous_hash: Optional[str]) -> str:
        """Calculate hash for integrity verification"""
        # Create a copy without hash_chain
        verify_data = {k: v for k, v in event_data.items() if k != 'hash_chain'}
        chain_data = f"{json.dumps(verify_data, sort_keys=True)}{previous_hash or ''}"
        return hashlib.sha256(chain_data.encode()).hexdigest()

    def get_audit_summary(self, days: int = 7) -> AuditSummary:
        """Get audit summary for specified number of days"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    index_data = json.load(f)

                stats = index_data.get('statistics', {})
                recent_critical = index_data.get('recent_critical', [])

                return AuditSummary(
                    total_events=stats.get('total_events', 0),
                    events_by_type=stats.get('events_by_type', {}),
                    events_by_severity=stats.get('events_by_severity', {}),
                    time_range={
                        'start': 'N/A',
                        'end': stats.get('last_updated', 'N/A')
                    },
                    integrity_status='VERIFIED' if self.verify_integrity() else 'COMPROMISED',
                    recent_critical_events=recent_critical[-10:]  # Last 10 critical events
                )

        except Exception as e:
            console.print(f"[red]Error generating audit summary: {e}[/red]")

        return AuditSummary(
            total_events=0,
            events_by_type={},
            events_by_severity={},
            time_range={'start': 'N/A', 'end': 'N/A'},
            integrity_status='ERROR',
            recent_critical_events=[]
        )

    def show_audit_summary(self):
        """Display audit summary with Rich formatting"""
        summary = self.get_audit_summary()

        from rich.table import Table
        from rich.panel import Panel

        # Main statistics table
        stats_table = Table(title="Audit Log Summary")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="yellow")

        stats_table.add_row("Total Events", str(summary.total_events))
        stats_table.add_row("Integrity Status",
                           f"[green]{summary.integrity_status}[/green]" if summary.integrity_status == 'VERIFIED'
                           else f"[red]{summary.integrity_status}[/red]")
        stats_table.add_row("Log Directory", str(self.log_dir))

        # Events by type
        if summary.events_by_type:
            stats_table.add_row("", "")  # Separator
            stats_table.add_row("[bold]Events by Type", "")
            for event_type, count in summary.events_by_type.items():
                stats_table.add_row(f"  {event_type.replace('_', ' ').title()}", str(count))

        # Events by severity
        if summary.events_by_severity:
            stats_table.add_row("", "")  # Separator
            stats_table.add_row("[bold]Events by Severity", "")
            for severity, count in summary.events_by_severity.items():
                color = {
                    'info': '[blue]',
                    'warning': '[yellow]',
                    'error': '[red]',
                    'critical': '[bold red]'
                }.get(severity, '[white]')
                stats_table.add_row(f"  {color}{severity.title()}[/]", str(count))

        console.print(stats_table)

        # Recent critical events
        if summary.recent_critical_events:
            console.print()
            critical_table = Table(title="Recent Critical Events")
            critical_table.add_column("Event ID", style="dim")
            critical_table.add_column("Type", style="cyan")
            critical_table.add_column("Severity", style="red")
            critical_table.add_column("Time", style="yellow")

            for event in summary.recent_critical_events[-5:]:  # Show last 5
                critical_table.add_row(
                    event['event_id'][:8],
                    event['event_type'].replace('_', ' ').title(),
                    event['severity'].upper(),
                    event['timestamp'][:19].replace('T', ' ')
                )

            console.print(critical_table)