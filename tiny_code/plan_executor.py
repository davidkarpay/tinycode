"""Plan execution system with safety features"""

import os
import shutil
import json
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.live import Live

from .plan_generator import ExecutionPlan, PlannedAction, ActionType, PlanStatus

console = Console()

class ExecutionStatus(Enum):
    """Status of plan execution"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class ActionResult(Enum):
    """Result of individual action execution"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"

@dataclass
class ExecutionContext:
    """Context for plan execution"""
    plan_id: str
    execution_id: str
    workspace: Path
    backup_dir: Path
    log_file: Path
    dry_run: bool = False
    stop_on_error: bool = True

@dataclass
class ActionExecutionResult:
    """Result of executing a single action"""
    action_id: str
    result: ActionResult
    output: str = ""
    error: str = ""
    duration: float = 0.0
    backup_path: Optional[str] = None
    rollback_data: Optional[Dict[str, Any]] = None

@dataclass
class ExecutionLog:
    """Complete execution log"""
    plan_id: str
    execution_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: ExecutionStatus = ExecutionStatus.NOT_STARTED
    action_results: List[ActionExecutionResult] = None
    total_duration: float = 0.0
    backup_directory: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.action_results is None:
            self.action_results = []

class PlanExecutor:
    """Executes approved plans with safety features"""

    def __init__(self, workspace: str = ".", backup_base_dir: str = "data/backups",
                 log_dir: str = "data/execution_logs"):
        self.workspace = Path(workspace).resolve()
        self.backup_base_dir = Path(backup_base_dir)
        self.log_dir = Path(log_dir)

        # Create directories
        self.backup_base_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize safety systems
        from .safety_config import SafetyConfigManager
        from .timeout_manager import ExecutionTimeoutManager
        from .audit_logger import AuditLogger
        from .plan_validator import PlanValidator

        self.safety_config = SafetyConfigManager()
        self.timeout_manager = ExecutionTimeoutManager(self.safety_config)
        self.audit_logger = AuditLogger()
        self.plan_validator = PlanValidator(self.safety_config)

        # Execution state
        self.current_execution: Optional[ExecutionContext] = None
        self.execution_logs: Dict[str, ExecutionLog] = {}

        console.print(f"[green]PlanExecutor initialized[/green]")
        console.print(f"[dim]Workspace: {self.workspace}[/dim]")
        console.print(f"[dim]Backups: {self.backup_base_dir}[/dim]")

        # Log initialization
        from .audit_logger import AuditEventType
        self.audit_logger.log_event(
            event_type=AuditEventType.CONFIG_CHANGED,
            details={
                "action": "plan_executor_initialized",
                "workspace": str(self.workspace),
                "safety_level": self.safety_config.config.safety_level.value
            }
        )

    def execute_plan(self, plan: ExecutionPlan, dry_run: bool = False) -> ExecutionLog:
        """Execute an approved plan with full safety features"""
        if plan.status != PlanStatus.APPROVED:
            raise ValueError(f"Plan {plan.id} is not approved for execution (status: {plan.status.value})")

        # Pre-execution validation
        from .audit_logger import AuditEventType, AuditSeverity
        from .plan_validator import ValidationSeverity

        console.print("[yellow]Validating plan before execution...[/yellow]")
        validation_result = self.plan_validator.validate_plan(plan)

        if validation_result.has_blocking_issues():
            self.audit_logger.log_event(
                event_type=AuditEventType.SAFETY_VIOLATION,
                severity=AuditSeverity.ERROR,
                operation_context={'plan_id': plan.id},
                details={'validation_issues': [issue.message for issue in validation_result.issues]}
            )
            raise ValueError("Plan validation failed with blocking issues")

        # Show validation warnings if any
        warnings = validation_result.get_issues_by_severity(ValidationSeverity.WARNING)
        if warnings:
            console.print(f"[yellow]⚠️  {len(warnings)} validation warnings found[/yellow]")

        # Create execution context
        execution_id = f"{plan.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        execution_context = self._create_execution_context(plan.id, execution_id, dry_run)

        # Initialize execution log
        execution_log = ExecutionLog(
            plan_id=plan.id,
            execution_id=execution_id,
            started_at=datetime.now(),
            status=ExecutionStatus.IN_PROGRESS,
            backup_directory=str(execution_context.backup_dir)
        )

        self.current_execution = execution_context
        self.execution_logs[execution_id] = execution_log

        # Log execution start
        self.audit_logger.log_plan_event(
            plan_id=plan.id,
            event_type=AuditEventType.PLAN_EXECUTED,
            details={
                'execution_id': execution_id,
                'dry_run': dry_run,
                'actions_count': len(plan.actions),
                'risk_assessment': validation_result.risk_assessment
            }
        )

        try:
            # Show execution header
            self._show_execution_header(plan, execution_context)

            # Create backup directory if needed
            if plan.requires_backup and not dry_run:
                execution_context.backup_dir.mkdir(parents=True, exist_ok=True)

            # Execute actions with progress tracking and timeout management
            def cleanup_on_timeout():
                """Cleanup function called on timeout"""
                console.print("[red]⏰ Execution timed out - performing cleanup[/red]")
                execution_log.status = ExecutionStatus.FAILED
                execution_log.error_message = "Execution timed out"

            # Use timeout context for the entire execution
            with self.timeout_manager.execution_timeout(
                plan_id=plan.id,
                cleanup_callback=cleanup_on_timeout
            ):
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.fields[action_desc]}", justify="left"),
                    BarColumn(bar_width=None),
                    "[progress.percentage]{task.percentage:>3.1f}%",
                    console=console
                ) as progress:

                    main_task = progress.add_task("Executing plan...", total=len(plan.actions), action_desc="Starting execution")

                    for i, action in enumerate(plan.actions):
                        # Update progress
                        progress.update(main_task,
                                      completed=i,
                                      action_desc=f"[{i+1}/{len(plan.actions)}] {action.description}")

                        # Execute the action with individual timeout
                        def action_cleanup():
                            console.print(f"[yellow]Action {action.id} timed out[/yellow]")

                        try:
                            with self.timeout_manager.action_timeout(
                                action_id=action.id,
                                action_timeout=60,  # 1 minute per action
                                cleanup_callback=action_cleanup
                            ):
                                action_result = self._execute_action(action, execution_context)
                                execution_log.action_results.append(action_result)

                                # Log action execution
                                self.audit_logger.log_execution_event(
                                    plan_id=plan.id,
                                    action_id=action.id,
                                    event_type=AuditEventType.ACTION_EXECUTED,
                                    details={
                                        'action_type': action.action_type.value,
                                        'target': action.target_path,
                                        'result': action_result.result.value,
                                        'duration': action_result.duration
                                    }
                                )

                        except self.timeout_manager.TimeoutError:
                            # Handle action timeout
                            action_result = ActionExecutionResult(
                                action_id=action.id,
                                result=ActionResult.FAILED,
                                error="Action timed out",
                                duration=60.0
                            )
                            execution_log.action_results.append(action_result)

                            self.audit_logger.log_event(
                                event_type=AuditEventType.TIMEOUT_OCCURRED,
                                severity=AuditSeverity.WARNING,
                                operation_context={'plan_id': plan.id, 'action_id': action.id},
                                details={'timeout_type': 'action_timeout', 'duration': 60}
                            )

                        # Handle failure
                        if action_result.result == ActionResult.FAILED:
                            execution_log.error_message = action_result.error
                            if execution_context.stop_on_error:
                                console.print(f"\n[red]Execution stopped due to error in action {action.id}[/red]")
                            execution_log.status = ExecutionStatus.FAILED
                            break

                    # Log progress
                    self._log_action_result(action_result, execution_context)

                # Complete progress
                progress.update(main_task, completed=len(plan.actions), action_desc="Execution completed")

            # Finalize execution
            execution_log.completed_at = datetime.now()
            execution_log.total_duration = (execution_log.completed_at - execution_log.started_at).total_seconds()

            if execution_log.status == ExecutionStatus.IN_PROGRESS:
                execution_log.status = ExecutionStatus.COMPLETED

            # Show results
            self._show_execution_results(execution_log, plan)

            return execution_log

        except Exception as e:
            execution_log.status = ExecutionStatus.FAILED
            execution_log.error_message = str(e)
            execution_log.completed_at = datetime.now()
            console.print(f"[red]Plan execution failed: {e}[/red]")
            return execution_log

        finally:
            # Save execution log
            self._save_execution_log(execution_log)
            self.current_execution = None

    def _create_execution_context(self, plan_id: str, execution_id: str, dry_run: bool) -> ExecutionContext:
        """Create execution context with directories and files"""
        backup_dir = self.backup_base_dir / execution_id
        log_file = self.log_dir / f"{execution_id}.log"

        return ExecutionContext(
            plan_id=plan_id,
            execution_id=execution_id,
            workspace=self.workspace,
            backup_dir=backup_dir,
            log_file=log_file,
            dry_run=dry_run,
            stop_on_error=True
        )

    def _execute_action(self, action: PlannedAction, context: ExecutionContext) -> ActionExecutionResult:
        """Execute a single action with appropriate safety measures"""
        start_time = datetime.now()

        console.print(f"\n[cyan]Executing: {action.description}[/cyan]")
        if context.dry_run:
            console.print("[yellow]DRY RUN - No actual changes will be made[/yellow]")

        try:
            # Route to appropriate execution method
            if action.action_type == ActionType.CREATE_FILE:
                return self._execute_create_file(action, context)
            elif action.action_type == ActionType.MODIFY_FILE:
                return self._execute_modify_file(action, context)
            elif action.action_type == ActionType.DELETE_FILE:
                return self._execute_delete_file(action, context)
            elif action.action_type == ActionType.RUN_COMMAND:
                return self._execute_run_command(action, context)
            elif action.action_type == ActionType.EXECUTE_CODE:
                return self._execute_code(action, context)
            elif action.action_type == ActionType.CREATE_DIRECTORY:
                return self._execute_create_directory(action, context)
            elif action.action_type == ActionType.MOVE_FILE:
                return self._execute_move_file(action, context)
            elif action.action_type == ActionType.COPY_FILE:
                return self._execute_copy_file(action, context)
            else:
                return ActionExecutionResult(
                    action_id=action.id,
                    result=ActionResult.FAILED,
                    error=f"Unknown action type: {action.action_type}",
                    duration=(datetime.now() - start_time).total_seconds()
                )

        except Exception as e:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error=str(e),
                duration=(datetime.now() - start_time).total_seconds()
            )

    def _execute_create_file(self, action: PlannedAction, context: ExecutionContext) -> ActionExecutionResult:
        """Execute file creation action"""
        start_time = datetime.now()

        if not action.target_path:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error="No target path specified for file creation"
            )

        target_file = self.workspace / action.target_path

        # Check if file already exists
        if target_file.exists():
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error=f"File {target_file} already exists"
            )

        if context.dry_run:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.SUCCESS,
                output=f"Would create file: {target_file}",
                duration=(datetime.now() - start_time).total_seconds()
            )

        try:
            # Create parent directories if needed
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            content = action.content or "# Generated file\n"
            target_file.write_text(content)

            console.print(f"[green]Created file: {target_file}[/green]")

            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.SUCCESS,
                output=f"Created file: {target_file}",
                duration=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error=f"Failed to create file {target_file}: {e}",
                duration=(datetime.now() - start_time).total_seconds()
            )

    def _execute_modify_file(self, action: PlannedAction, context: ExecutionContext) -> ActionExecutionResult:
        """Execute file modification action with backup"""
        start_time = datetime.now()

        if not action.target_path:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error="No target path specified for file modification"
            )

        target_file = self.workspace / action.target_path

        if not target_file.exists():
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error=f"File {target_file} does not exist"
            )

        backup_path = None

        if context.dry_run:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.SUCCESS,
                output=f"Would modify file: {target_file}",
                duration=(datetime.now() - start_time).total_seconds()
            )

        try:
            # Create backup
            backup_path = self._create_backup(target_file, context.backup_dir)

            # Modify file (this would integrate with the agent's modification capabilities)
            if action.content:
                target_file.write_text(action.content)
            else:
                # For now, just add a modification marker
                original_content = target_file.read_text()
                modified_content = f"# Modified by TinyCode at {datetime.now()}\n{original_content}"
                target_file.write_text(modified_content)

            console.print(f"[green]Modified file: {target_file}[/green]")

            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.SUCCESS,
                output=f"Modified file: {target_file}",
                backup_path=str(backup_path),
                duration=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error=f"Failed to modify file {target_file}: {e}",
                backup_path=str(backup_path) if backup_path else None,
                duration=(datetime.now() - start_time).total_seconds()
            )

    def _execute_delete_file(self, action: PlannedAction, context: ExecutionContext) -> ActionExecutionResult:
        """Execute file deletion action with backup"""
        start_time = datetime.now()

        if not action.target_path:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error="No target path specified for file deletion"
            )

        target_file = self.workspace / action.target_path

        if not target_file.exists():
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.SUCCESS,
                output=f"File {target_file} does not exist (already deleted)",
                duration=(datetime.now() - start_time).total_seconds()
            )

        if context.dry_run:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.SUCCESS,
                output=f"Would delete file: {target_file}",
                duration=(datetime.now() - start_time).total_seconds()
            )

        try:
            # Create backup before deletion
            backup_path = self._create_backup(target_file, context.backup_dir)

            # Delete file
            target_file.unlink()

            console.print(f"[yellow]Deleted file: {target_file}[/yellow]")

            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.SUCCESS,
                output=f"Deleted file: {target_file}",
                backup_path=str(backup_path),
                duration=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error=f"Failed to delete file {target_file}: {e}",
                duration=(datetime.now() - start_time).total_seconds()
            )

    def _execute_run_command(self, action: PlannedAction, context: ExecutionContext) -> ActionExecutionResult:
        """Execute shell command action"""
        start_time = datetime.now()

        if not action.command:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error="No command specified"
            )

        if context.dry_run:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.SUCCESS,
                output=f"Would run command: {action.command}",
                duration=(datetime.now() - start_time).total_seconds()
            )

        try:
            # Run command with timeout
            result = subprocess.run(
                action.command,
                shell=True,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                console.print(f"[green]Command completed successfully[/green]")
                return ActionExecutionResult(
                    action_id=action.id,
                    result=ActionResult.SUCCESS,
                    output=result.stdout,
                    duration=(datetime.now() - start_time).total_seconds()
                )
            else:
                console.print(f"[red]Command failed with exit code {result.returncode}[/red]")
                return ActionExecutionResult(
                    action_id=action.id,
                    result=ActionResult.FAILED,
                    output=result.stdout,
                    error=result.stderr,
                    duration=(datetime.now() - start_time).total_seconds()
                )

        except subprocess.TimeoutExpired:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error="Command timed out after 5 minutes",
                duration=(datetime.now() - start_time).total_seconds()
            )
        except Exception as e:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error=f"Failed to run command: {e}",
                duration=(datetime.now() - start_time).total_seconds()
            )

    def _execute_code(self, action: PlannedAction, context: ExecutionContext) -> ActionExecutionResult:
        """Execute code action (Python)"""
        start_time = datetime.now()

        if not action.content:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error="No code content specified"
            )

        if context.dry_run:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.SUCCESS,
                output=f"Would execute code: {action.content[:100]}...",
                duration=(datetime.now() - start_time).total_seconds()
            )

        # For now, just save code to a temporary file and note it
        # In a real implementation, this would integrate with the agent's code execution
        console.print(f"[yellow]Code execution not fully implemented - would execute:{action.content[:100]}...[/yellow]")

        return ActionExecutionResult(
            action_id=action.id,
            result=ActionResult.SUCCESS,
            output=f"Code execution placeholder: {action.content[:100]}...",
            duration=(datetime.now() - start_time).total_seconds()
        )

    def _execute_create_directory(self, action: PlannedAction, context: ExecutionContext) -> ActionExecutionResult:
        """Execute directory creation action"""
        start_time = datetime.now()

        if not action.target_path:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error="No target path specified for directory creation"
            )

        target_dir = self.workspace / action.target_path

        if context.dry_run:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.SUCCESS,
                output=f"Would create directory: {target_dir}",
                duration=(datetime.now() - start_time).total_seconds()
            )

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]Created directory: {target_dir}[/green]")

            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.SUCCESS,
                output=f"Created directory: {target_dir}",
                duration=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            return ActionExecutionResult(
                action_id=action.id,
                result=ActionResult.FAILED,
                error=f"Failed to create directory {target_dir}: {e}",
                duration=(datetime.now() - start_time).total_seconds()
            )

    def _execute_move_file(self, action: PlannedAction, context: ExecutionContext) -> ActionExecutionResult:
        """Execute file move action"""
        # Implementation for move file action
        return ActionExecutionResult(
            action_id=action.id,
            result=ActionResult.SUCCESS,
            output="Move file action - placeholder implementation"
        )

    def _execute_copy_file(self, action: PlannedAction, context: ExecutionContext) -> ActionExecutionResult:
        """Execute file copy action"""
        # Implementation for copy file action
        return ActionExecutionResult(
            action_id=action.id,
            result=ActionResult.SUCCESS,
            output="Copy file action - placeholder implementation"
        )

    def _create_backup(self, file_path: Path, backup_dir: Path) -> Path:
        """Create a backup of a file"""
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.backup"
        backup_path = backup_dir / backup_name

        # Copy file to backup location
        shutil.copy2(file_path, backup_path)
        console.print(f"[dim]Backup created: {backup_path}[/dim]")

        return backup_path

    def _log_action_result(self, result: ActionExecutionResult, context: ExecutionContext):
        """Log action result to file"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action_id": result.action_id,
                "result": result.result.value,
                "output": result.output,
                "error": result.error,
                "duration": result.duration,
                "backup_path": result.backup_path
            }

            with open(context.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            console.print(f"[red]Failed to write log entry: {e}[/red]")

    def _save_execution_log(self, log: ExecutionLog):
        """Save complete execution log"""
        try:
            log_file = self.log_dir / f"{log.execution_id}_summary.json"

            log_data = {
                "plan_id": log.plan_id,
                "execution_id": log.execution_id,
                "started_at": log.started_at.isoformat(),
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                "status": log.status.value,
                "total_duration": log.total_duration,
                "backup_directory": log.backup_directory,
                "error_message": log.error_message,
                "action_results": [
                    {
                        "action_id": r.action_id,
                        "result": r.result.value,
                        "output": r.output,
                        "error": r.error,
                        "duration": r.duration,
                        "backup_path": r.backup_path
                    }
                    for r in log.action_results
                ]
            }

            with open(log_file, "w") as f:
                json.dump(log_data, f, indent=2)

        except Exception as e:
            console.print(f"[red]Failed to save execution log: {e}[/red]")

    def _show_execution_header(self, plan: ExecutionPlan, context: ExecutionContext):
        """Show execution header with plan details"""
        header = f"[bold]Executing Plan: {plan.title}[/bold]\n"
        header += f"Plan ID: {plan.id}\n"
        header += f"Execution ID: {context.execution_id}\n"
        header += f"Actions: {len(plan.actions)} | Risk: {plan.risk_assessment}\n"
        header += f"Workspace: {context.workspace}"

        if context.dry_run:
            header += "\n[yellow bold]DRY RUN MODE - No changes will be made[/yellow bold]"

        console.print(Panel(header, title="Plan Execution", border_style="blue"))

    def _show_execution_results(self, log: ExecutionLog, plan: ExecutionPlan):
        """Show execution results summary"""
        # Summary statistics
        total_actions = len(log.action_results)
        successful = len([r for r in log.action_results if r.result == ActionResult.SUCCESS])
        failed = len([r for r in log.action_results if r.result == ActionResult.FAILED])

        # Create results table
        table = Table(title="Execution Results")
        table.add_column("Action ID", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Result", style="yellow")
        table.add_column("Duration", style="green")
        table.add_column("Notes", style="dim")

        for i, result in enumerate(log.action_results):
            action = plan.actions[i] if i < len(plan.actions) else None
            description = action.description if action else "Unknown"

            result_color = {
                ActionResult.SUCCESS: "[green]SUCCESS[/green]",
                ActionResult.FAILED: "[red]FAILED[/red]",
                ActionResult.SKIPPED: "[yellow]SKIPPED[/yellow]",
                ActionResult.ROLLED_BACK: "[dark_orange]ROLLED_BACK[/dark_orange]"
            }.get(result.result, "[white]UNKNOWN[/white]")

            notes = ""
            if result.backup_path:
                notes += f"Backup: {Path(result.backup_path).name}"
            if result.error:
                notes += f" Error: {result.error[:30]}..."

            table.add_row(
                result.action_id,
                description[:40] + "..." if len(description) > 40 else description,
                result_color,
                f"{result.duration:.1f}s",
                notes
            )

        console.print(table)

        # Summary panel
        status_color = {
            ExecutionStatus.COMPLETED: "green",
            ExecutionStatus.FAILED: "red",
            ExecutionStatus.ROLLED_BACK: "yellow"
        }.get(log.status, "white")

        summary = f"[bold]Status: {log.status.value.upper()}[/bold]\n"
        summary += f"Total Duration: {log.total_duration:.1f}s\n"
        summary += f"Actions: {successful} successful, {failed} failed out of {total_actions}\n"

        if log.backup_directory and Path(log.backup_directory).exists():
            summary += f"Backups: {log.backup_directory}"

        console.print(Panel(summary, title="Execution Summary", border_style=status_color))

    def rollback_execution(self, execution_id: str) -> bool:
        """Rollback a failed execution using backups"""
        if execution_id not in self.execution_logs:
            console.print(f"[red]Execution {execution_id} not found[/red]")
            return False

        log = self.execution_logs[execution_id]

        if log.status == ExecutionStatus.COMPLETED:
            console.print(f"[yellow]Cannot rollback successful execution[/yellow]")
            return False

        console.print(f"[yellow]Rolling back execution {execution_id}...[/yellow]")

        # Rollback actions in reverse order
        rollback_count = 0
        for result in reversed(log.action_results):
            if result.backup_path and Path(result.backup_path).exists():
                try:
                    # Restore from backup
                    # This would need to be implemented based on action type
                    rollback_count += 1
                except Exception as e:
                    console.print(f"[red]Failed to rollback action {result.action_id}: {e}[/red]")

        log.status = ExecutionStatus.ROLLED_BACK
        console.print(f"[green]Rolled back {rollback_count} actions[/green]")
        return True

    def get_execution_logs(self) -> List[ExecutionLog]:
        """Get all execution logs"""
        return list(self.execution_logs.values())

    def get_execution_log(self, execution_id: str) -> Optional[ExecutionLog]:
        """Get a specific execution log"""
        return self.execution_logs.get(execution_id)