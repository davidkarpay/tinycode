#!/usr/bin/env python3
"""Test script to demonstrate the complete plan execution workflow"""

import sys
from pathlib import Path

# Add the current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tiny_code.cli import TinyCodeCLI
from tiny_code.mode_manager import OperationMode
from tiny_code.plan_generator import PlanStatus
from rich.console import Console

console = Console()

def test_plan_execution_workflow():
    """Test the complete plan execution workflow"""

    console.print("[bold cyan]🧪 Testing Plan Execution Workflow[/bold cyan]")
    console.print()

    # Initialize CLI
    console.print("[yellow]1. Initializing TinyCode CLI...[/yellow]")
    cli = TinyCodeCLI()

    # Switch to propose mode
    console.print("[yellow]2. Switching to Propose mode...[/yellow]")
    cli.mode_manager.set_mode(OperationMode.PROPOSE)

    # Create a simple test plan
    console.print("[yellow]3. Creating a test plan...[/yellow]")
    test_request = "Create a simple Hello World Python script in test_hello.py"

    try:
        plan = cli.plan_generator.generate_plan(test_request, title="Test Hello World Creation")
        console.print(f"[green]✓ Plan created: {plan.id}[/green]")

        # Show plan details
        console.print("[yellow]4. Generated plan details:[/yellow]")
        cli.plan_generator.show_plan_details(plan)

        # Approve the plan
        console.print("[yellow]5. Approving the plan...[/yellow]")
        success = cli.plan_generator.update_plan_status(plan.id, PlanStatus.APPROVED)
        if success:
            console.print(f"[green]✓ Plan {plan.id} approved[/green]")
        else:
            console.print(f"[red]✗ Failed to approve plan {plan.id}[/red]")
            return False

        # Execute the plan (dry run first)
        console.print("[yellow]6. Executing plan (dry run)...[/yellow]")
        execution_log = cli.plan_executor.execute_plan(plan, dry_run=True)

        console.print(f"[cyan]Dry run results:[/cyan]")
        console.print(f"  Status: {execution_log.status}")
        console.print(f"  Actions: {len(execution_log.action_results)}")
        console.print(f"  Duration: {execution_log.total_duration:.2f}s")

        # Real execution
        console.print("[yellow]7. Executing plan (real execution)...[/yellow]")
        execution_log = cli.plan_executor.execute_plan(plan, dry_run=False)

        console.print(f"[cyan]Execution results:[/cyan]")
        console.print(f"  Status: {execution_log.status}")
        from tiny_code.plan_executor import ActionResult
        console.print(f"  Actions completed: {len([a for a in execution_log.action_results if a.result == ActionResult.SUCCESS])}")
        console.print(f"  Actions failed: {len([a for a in execution_log.action_results if a.result == ActionResult.FAILED])}")
        console.print(f"  Duration: {execution_log.total_duration:.2f}s")
        console.print(f"  Backup: {execution_log.backup_directory}")

        # Update plan status
        from tiny_code.plan_executor import ExecutionStatus
        if execution_log.status == ExecutionStatus.COMPLETED:
            cli.plan_generator.update_plan_status(plan.id, PlanStatus.EXECUTED)
            console.print(f"[green]✓ Plan {plan.id} marked as executed[/green]")
        else:
            cli.plan_generator.update_plan_status(plan.id, PlanStatus.FAILED)
            console.print(f"[red]✗ Plan {plan.id} marked as failed[/red]")

        # Show final plans list
        console.print("[yellow]8. Final plans status:[/yellow]")
        plans = cli.plan_generator.list_plans()
        if plans:
            for plan in plans:
                console.print(f"  {plan.id}: {plan.title} - {plan.status.value}")

        console.print()
        console.print("[bold green]🎉 Plan execution workflow test completed![/bold green]")
        return True

    except Exception as e:
        console.print(f"[red]✗ Error during test: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False

if __name__ == "__main__":
    test_plan_execution_workflow()