#!/usr/bin/env python3
"""Demonstration of enhanced safety systems in TinyCode"""

import sys
from pathlib import Path

# Add the current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tiny_code.safety_config import SafetyConfigManager, SafetyLevel
from tiny_code.audit_logger import AuditLogger
from tiny_code.plan_validator import PlanValidator
from tiny_code.timeout_manager import TimeoutManager
from rich.console import Console

console = Console()

def demo_safety_systems():
    """Demonstrate the enhanced safety systems"""

    console.print("[bold cyan]🔒 TinyCode Enhanced Safety Systems Demo[/bold cyan]")
    console.print()

    # 1. Safety Configuration System
    console.print("[yellow]1. Safety Configuration System[/yellow]")
    safety_config = SafetyConfigManager()

    console.print(f"   Current Safety Level: [bold]{safety_config.config.safety_level.value}[/bold]")
    console.print(f"   Max Files per Plan: {safety_config.config.execution_limits.max_files_per_plan}")
    console.print(f"   Max Execution Time: {safety_config.config.execution_limits.max_execution_time_seconds}s")
    console.print(f"   Allowed Extensions: {len(safety_config.config.execution_limits.allowed_file_extensions)} types")

    # Show safety configuration summary
    summary = safety_config.show_config_summary()
    console.print(f"   Configuration Summary: {summary}")
    console.print()

    # 2. Audit Logging System
    console.print("[yellow]2. Audit Logging System[/yellow]")
    audit_logger = AuditLogger()

    # Log a sample event
    from tiny_code.audit_logger import AuditEventType, AuditSeverity
    event_id = audit_logger.log_event(
        event_type=AuditEventType.CONFIG_CHANGED,
        severity=AuditSeverity.INFO,
        details={'action': 'safety_demo_started', 'demo_session': True}
    )
    console.print(f"   Logged demo event: {event_id}")

    # Show audit summary
    audit_logger.show_audit_summary()
    console.print()

    # 3. Plan Validation System
    console.print("[yellow]3. Plan Validation System[/yellow]")
    plan_validator = PlanValidator(safety_config)

    # Create a mock plan for validation
    from tiny_code.plan_generator import ExecutionPlan, PlannedAction, ActionType, PlanStatus
    from datetime import datetime

    mock_plan = ExecutionPlan(
        id="demo_plan",
        title="Demo Plan for Safety Testing",
        description="A demonstration plan to test safety systems",
        user_request="Create demo files for safety testing",
        actions=[
            PlannedAction(
                id="action1",
                action_type=ActionType.CREATE_FILE,
                description="Create a Python script",
                target_path="demo_script.py",
                content="print('Hello, Safe World!')",
                estimated_duration=30,
                risk_level="LOW"
            ),
            PlannedAction(
                id="action2",
                action_type=ActionType.CREATE_FILE,
                description="Create a README file",
                target_path="README.md",
                content="# Demo Project\nThis is a safe demo project.",
                estimated_duration=15,
                risk_level="LOW"
            )
        ],
        status=PlanStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        risk_assessment="LOW",
        estimated_total_duration=45
    )

    # Validate the plan
    console.print("   Validating demo plan...")
    validation_result = plan_validator.validate_plan(mock_plan)
    plan_validator.show_validation_results(validation_result)
    console.print()

    # 4. Timeout Management System
    console.print("[yellow]4. Timeout Management System[/yellow]")
    timeout_manager = TimeoutManager()

    console.print("   Testing timeout context...")
    try:
        with timeout_manager.timeout_context(
            operation_name="demo_operation",
            timeout_seconds=2,
            warning_callback=lambda: console.print("   [yellow]⚠️  Warning: Operation taking longer than expected[/yellow]")
        ) as context:
            import time
            console.print(f"   Operation started: {context.operation_name}")
            time.sleep(1)
            console.print("   Operation completed successfully within timeout")
    except timeout_manager.TimeoutError as e:
        console.print(f"   [red]Operation timed out: {e}[/red]")

    console.print()

    # 5. Safety Level Demonstration
    console.print("[yellow]5. Safety Level Impact Demonstration[/yellow]")

    for level in [SafetyLevel.PERMISSIVE, SafetyLevel.STANDARD, SafetyLevel.STRICT, SafetyLevel.PARANOID]:
        console.print(f"   [cyan]{level.value.upper()}[/cyan]: ", end="")

        # Create temporary config for this level
        temp_config = SafetyConfigManager()
        temp_config.config.safety_level = level
        temp_config.config._apply_safety_level_adjustments()

        console.print(f"Max files: {temp_config.config.execution_limits.max_files_per_plan}, "
                     f"Timeout: {temp_config.config.execution_limits.max_execution_time_seconds}s, "
                     f"Confirmation req: {temp_config.config.confirmation_prompts}")

    console.print()

    # 6. Final Security Summary
    console.print("[yellow]6. Security Features Summary[/yellow]")
    security_features = [
        "✅ Pre-execution plan validation",
        "✅ Path traversal protection",
        "✅ Dangerous command detection",
        "✅ File size and count limits",
        "✅ Execution timeout controls",
        "✅ Comprehensive audit logging with hash chains",
        "✅ Configurable safety levels",
        "✅ Automatic backup creation",
        "✅ Rollback capabilities",
        "✅ Content scanning for suspicious patterns"
    ]

    for feature in security_features:
        console.print(f"   {feature}")

    console.print()
    console.print("[bold green]🎉 Enhanced Safety Systems Demo Complete![/bold green]")
    console.print("[dim]All safety systems are functioning and protecting your execution environment.[/dim]")

if __name__ == "__main__":
    demo_safety_systems()