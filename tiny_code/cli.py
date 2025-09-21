"""CLI interface for Tiny Code"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from .agent import TinyCodeAgent
from .tools import CodeTools
from .mode_manager import ModeManager, OperationMode
from .plan_generator import PlanGenerator, PlanStatus
from .plan_executor import PlanExecutor

console = Console()

class TinyCodeCLI:
    """Command-line interface for Tiny Code"""

    def __init__(self):
        self.agent = TinyCodeAgent()
        self.tools = CodeTools()
        self.mode_manager = ModeManager(initial_mode=OperationMode.CHAT)
        self.plan_generator = PlanGenerator()
        self.plan_executor = PlanExecutor()
        self.history_file = Path.home() / '.tiny_code_history'
        self.last_response = None  # Track last response for save functionality

    def interactive_mode(self):
        """Run interactive chat mode"""
        console.print(Panel.fit(
            "[bold cyan]Welcome to Tiny Code![/bold cyan]\n"
            "Your AI coding assistant powered by TinyLlama\n"
            "Type 'help' for commands, '/mode help' for mode info, 'exit' to quit",
            border_style="cyan"
        ))

        # Show initial mode
        self.mode_manager._show_mode_change(self.mode_manager.current_mode)

        history = FileHistory(str(self.history_file))

        while True:
            try:
                # Create mode-aware prompt
                mode_indicator = f"[{self.mode_manager.current_mode.value}]"
                user_input = prompt(
                    f"Tiny Code {mode_indicator}> ",
                    history=history,
                    auto_suggest=AutoSuggestFromHistory()
                ).strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                if user_input.lower() == 'help':
                    self.show_help()
                    continue

                if user_input.lower() == 'clear':
                    console.clear()
                    continue

                if user_input.startswith('/'):
                    self.handle_command(user_input[1:])
                else:
                    # Chat mode - safe Q&A only
                    if self.mode_manager.current_mode == OperationMode.CHAT:
                        console.print("[dim]Thinking...[/dim]")
                        response = self.agent.chat(user_input, stream=True)
                        self.last_response = response
                        console.print()
                    else:
                        # In propose or execute mode, treat as potential action request
                        self.handle_user_request(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def handle_command(self, command: str):
        """Handle special commands with mode awareness"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Handle mode commands first
        if cmd == 'mode':
            self.handle_mode_command(args)
            return

        # Check if command is allowed in current mode
        if not self.mode_manager.is_command_allowed(cmd):
            console.print(f"[red]Command '{cmd}' not allowed in {self.mode_manager.current_mode.value} mode[/red]")
            console.print(f"[yellow]Use '/mode help' to see available modes[/yellow]")
            return

        commands = {
            # Safe commands (available in all modes)
            'help': self.show_help,
            'analyze': self.analyze_file_cmd,
            'explain': self.explain_code_cmd,
            'review': self.review_code_cmd,
            'workspace': self.set_workspace_cmd,
            'list': self.list_files_cmd,

            # Execution commands (execute mode only)
            'file': self.load_file,
            'complete': self.complete_code_cmd,
            'fix': self.fix_code_cmd,
            'refactor': self.refactor_code_cmd,
            'test': self.generate_tests_cmd,
            'run': self.run_code_cmd,
            'save': self.save_output_cmd,

            # Planning commands (propose mode)
            'plan': self.create_plan_cmd,
            'preview': self.preview_plan_cmd,
            'approve': self.approve_plan_cmd,
            'reject': self.reject_plan_cmd,
            'show_plan': self.show_plan_cmd,
            'list_plans': self.list_plans_cmd,
            'execute_plan': self.execute_plan_cmd
        }

        if cmd in commands:
            commands[cmd](args)
        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")

    def show_help(self):
        """Show help information"""
        help_text = """
        [bold cyan]Tiny Code Commands:[/bold cyan]

        [yellow]Chat:[/yellow]
        Just type your question or request

        [yellow]Commands (prefix with /):[/yellow]
        /file <path>       - Load a file for processing
        /analyze <path>    - Analyze a code file
        /complete <path>   - Complete code in file
        /fix <path>        - Fix bugs in code
        /explain <path>    - Explain code in file
        /refactor <path>   - Refactor code
        /test <path>       - Generate tests for code
        /review <path>     - Review code quality
        /run <path>        - Execute a Python file
        /save <path>       - Save last response to file
        /workspace <path>  - Set working directory
        /list [pattern]    - List files in workspace

        [yellow]Other:[/yellow]
        help    - Show this help
        clear   - Clear screen
        exit    - Quit the program
        """
        console.print(Panel(help_text, title="Help", border_style="blue"))

    def load_file(self, filepath: str):
        """Load a file for processing"""
        if not filepath:
            filepath = Prompt.ask("Enter file path")

        code = self.tools.read_file(filepath)
        if code:
            self.agent.current_file = filepath
            lines = len(code.splitlines())
            console.print(f"[green]Loaded {filepath} ({lines} lines)[/green]")
            self.tools.display_code(code[:500] + ("..." if len(code) > 500 else ""))
        else:
            console.print(f"[red]Could not load {filepath}[/red]")

    def analyze_file_cmd(self, filepath: str):
        """Analyze a file"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        analysis = self.agent.analyze_file(filepath)

        if "error" in analysis:
            console.print(f"[red]{analysis['error']}[/red]")
            return

        table = Table(title=f"Analysis of {filepath}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        for key, value in analysis['metrics'].items():
            table.add_row(key.capitalize(), str(value))

        console.print(table)

        if analysis['functions']:
            console.print("\n[bold cyan]Functions:[/bold cyan]")
            for func in analysis['functions']:
                console.print(f"  • {func['name']}({', '.join(func['args'])})")

        if analysis['classes']:
            console.print("\n[bold cyan]Classes:[/bold cyan]")
            for cls in analysis['classes']:
                console.print(f"  • {cls['name']}")
                for method in cls['methods']:
                    console.print(f"    - {method}")

    def complete_code_cmd(self, filepath: str):
        """Complete code in a file"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        requirements = Prompt.ask("Requirements (optional)", default="")
        result = self.agent.process_file(filepath, 'complete', requirements=requirements)
        console.print(Panel(result, title="Code Completion", border_style="green"))

    def fix_code_cmd(self, filepath: str):
        """Fix bugs in code"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        error = Prompt.ask("Describe the error/issue")
        result = self.agent.process_file(filepath, 'fix', error=error)
        console.print(Panel(result, title="Bug Fix", border_style="green"))

    def explain_code_cmd(self, filepath: str):
        """Explain code"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        result = self.agent.process_file(filepath, 'explain')
        console.print(Panel(Markdown(result), title="Code Explanation", border_style="blue"))

    def refactor_code_cmd(self, filepath: str):
        """Refactor code"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        requirements = Prompt.ask("Refactoring goals (optional)", default="")
        result = self.agent.process_file(filepath, 'refactor', requirements=requirements)
        console.print(Panel(result, title="Refactored Code", border_style="green"))

    def generate_tests_cmd(self, filepath: str):
        """Generate tests for code"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        result = self.agent.process_file(filepath, 'test')
        console.print(Panel(result, title="Generated Tests", border_style="green"))

    def review_code_cmd(self, filepath: str):
        """Review code quality"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        result = self.agent.process_file(filepath, 'review')
        console.print(Panel(Markdown(result), title="Code Review", border_style="yellow"))

    def run_code_cmd(self, filepath: str):
        """Execute a Python file"""
        if not filepath:
            filepath = self.agent.current_file or Prompt.ask("Enter file path")

        code = self.tools.read_file(filepath)
        if code:
            self.agent.execute_code(code)

    def save_output_cmd(self, filepath: str):
        """Save last output to file"""
        if not filepath:
            filepath = Prompt.ask("Enter output file path")

        # This would need to track last response
        console.print("[yellow]Save functionality requires response tracking[/yellow]")

    def set_workspace_cmd(self, path: str):
        """Set workspace directory"""
        if not path:
            path = Prompt.ask("Enter workspace path")

        self.agent.set_workspace(path)

    def list_files_cmd(self, pattern: str):
        """List files in workspace"""
        if not pattern:
            pattern = "*.py"

        files = self.agent.list_files(pattern)
        if files:
            console.print(f"[cyan]Files matching '{pattern}':[/cyan]")
            for f in files:
                console.print(f"  • {f}")
        else:
            console.print(f"[yellow]No files found matching '{pattern}'[/yellow]")

    def handle_mode_command(self, args: str):
        """Handle mode-related commands"""
        if not args:
            # Show current mode status
            status = self.mode_manager.get_mode_status()
            console.print(Panel(
                f"[bold]Current Mode: {status['current_mode'].upper()}[/bold]\n"
                f"{status['description']}\n\n"
                f"[cyan]Available Commands:[/cyan]\n" +
                ", ".join(status['allowed_commands'][:10]) +
                (f" ... and {len(status['allowed_commands']) - 10} more" if len(status['allowed_commands']) > 10 else ""),
                title="Mode Status",
                border_style="blue"
            ))
            return

        parts = args.split()
        cmd = parts[0].lower()

        if cmd in ['chat', 'propose', 'execute']:
            mode_map = {
                'chat': OperationMode.CHAT,
                'propose': OperationMode.PROPOSE,
                'execute': OperationMode.EXECUTE
            }
            self.mode_manager.set_mode(mode_map[cmd])

        elif cmd == 'status':
            status = self.mode_manager.get_mode_status()
            console.print(Panel(
                f"[bold]Current Mode: {status['current_mode'].upper()}[/bold]\n"
                f"{status['description']}\n\n"
                f"[cyan]Available Commands:[/cyan]\n" +
                "\n".join(f"  • {cmd}" for cmd in status['allowed_commands']),
                title="Detailed Mode Status",
                border_style="blue"
            ))

        elif cmd == 'help':
            self.mode_manager.show_mode_help()

        else:
            console.print(f"[red]Unknown mode command: {cmd}[/red]")
            console.print("[yellow]Available: chat, propose, execute, status, help[/yellow]")

    def handle_user_request(self, user_input: str):
        """Handle user requests in propose/execute modes"""
        if self.mode_manager.current_mode == OperationMode.PROPOSE:
            # Generate a plan for the request
            console.print(f"[yellow]Generating execution plan...[/yellow]")
            try:
                plan = self.plan_generator.generate_plan(user_input)
                self.plan_generator.show_plan_details(plan)

                console.print(f"\n[cyan]Plan '{plan.id}' created successfully![/cyan]")
                console.print(f"[dim]Use '/approve {plan.id}' to approve or '/reject {plan.id}' to reject[/dim]")

            except Exception as e:
                console.print(f"[red]Error generating plan: {e}[/red]")

        elif self.mode_manager.current_mode == OperationMode.EXECUTE:
            # Execute immediately with confirmation
            console.print(f"[red]Execute mode - immediate execution[/red]")
            console.print(f"[dim]Request: {user_input}[/dim]")

            if Confirm.ask(f"Execute this request immediately?"):
                console.print(f"[dim]Thinking...[/dim]")
                response = self.agent.chat(user_input, stream=True)
                self.last_response = response
                console.print()
            else:
                console.print(f"[yellow]Execution cancelled[/yellow]")

    # Planning command implementations
    def create_plan_cmd(self, args: str):
        """Create a new execution plan"""
        if not args:
            args = Prompt.ask("Enter request to plan")

        try:
            plan = self.plan_generator.generate_plan(args)
            self.plan_generator.show_plan_details(plan)
            console.print(f"\n[green]Plan '{plan.id}' created successfully![/green]")
        except Exception as e:
            console.print(f"[red]Error creating plan: {e}[/red]")

    def preview_plan_cmd(self, args: str):
        """Preview a plan"""
        if not args:
            args = Prompt.ask("Enter plan ID to preview")

        plan = self.plan_generator.get_plan(args)
        if plan:
            self.plan_generator.show_plan_details(plan)
        else:
            console.print(f"[red]Plan '{args}' not found[/red]")

    def approve_plan_cmd(self, args: str):
        """Approve a plan for execution"""
        if not args:
            args = Prompt.ask("Enter plan ID to approve")

        plan = self.plan_generator.get_plan(args)
        if not plan:
            console.print(f"[red]Plan '{args}' not found[/red]")
            return

        if plan.status != PlanStatus.DRAFT and plan.status != PlanStatus.PENDING:
            console.print(f"[red]Plan '{args}' cannot be approved (status: {plan.status.value})[/red]")
            return

        # Show plan details before approval
        self.plan_generator.show_plan_details(plan)

        if Confirm.ask(f"Approve plan '{plan.title}'?"):
            if self.plan_generator.update_plan_status(args, PlanStatus.APPROVED):
                console.print(f"[green]Plan '{args}' approved for execution[/green]")
                console.print(f"[dim]Use '/execute_plan {args}' to execute[/dim]")
            else:
                console.print(f"[red]Error approving plan '{args}'[/red]")
        else:
            console.print(f"[yellow]Plan approval cancelled[/yellow]")

    def reject_plan_cmd(self, args: str):
        """Reject a plan"""
        if not args:
            args = Prompt.ask("Enter plan ID to reject")

        plan = self.plan_generator.get_plan(args)
        if not plan:
            console.print(f"[red]Plan '{args}' not found[/red]")
            return

        if plan.status not in [PlanStatus.DRAFT, PlanStatus.PENDING]:
            console.print(f"[red]Plan '{args}' cannot be rejected (status: {plan.status.value})[/red]")
            return

        reason = Prompt.ask("Reason for rejection (optional)", default="")

        if self.plan_generator.update_plan_status(args, PlanStatus.REJECTED):
            console.print(f"[yellow]Plan '{args}' rejected[/yellow]")
            if reason:
                console.print(f"[dim]Reason: {reason}[/dim]")
        else:
            console.print(f"[red]Error rejecting plan '{args}'[/red]")

    def show_plan_cmd(self, args: str):
        """Show details of a plan"""
        if not args:
            # List all plans first to help user choose
            self.list_plans_cmd("")
            args = Prompt.ask("Enter plan ID to show details")

        plan = self.plan_generator.get_plan(args)
        if plan:
            self.plan_generator.show_plan_details(plan)
        else:
            console.print(f"[red]Plan '{args}' not found[/red]")

    def list_plans_cmd(self, args: str):
        """List all available plans"""
        # Parse optional status filter
        status_filter = None
        if args:
            try:
                status_filter = PlanStatus(args.lower())
            except ValueError:
                console.print(f"[yellow]Invalid status '{args}'. Available: draft, pending, approved, rejected, executed, failed[/yellow]")

        plans = self.plan_generator.list_plans(status_filter)

        if not plans:
            status_text = f" with status '{status_filter.value}'" if status_filter else ""
            console.print(f"[yellow]No plans found{status_text}[/yellow]")
            return

        # Create plans table
        table = Table(title=f"Plans{' - ' + status_filter.value.title() if status_filter else ''}")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Risk", style="red")
        table.add_column("Actions", style="green")
        table.add_column("Created", style="dim")

        for plan in plans:
            status_color = {
                PlanStatus.DRAFT: "[yellow]",
                PlanStatus.PENDING: "[blue]",
                PlanStatus.APPROVED: "[green]",
                PlanStatus.REJECTED: "[red]",
                PlanStatus.EXECUTED: "[bright_green]",
                PlanStatus.FAILED: "[bright_red]"
            }.get(plan.status, "[white]")

            table.add_row(
                plan.id,
                plan.title[:40] + "..." if len(plan.title) > 40 else plan.title,
                f"{status_color}{plan.status.value}[/]",
                plan.risk_assessment,
                str(len(plan.actions)),
                plan.created_at.strftime("%m/%d %H:%M")
            )

        console.print(table)

        # Show summary
        total_plans = len(plans)
        if total_plans > 0:
            console.print(f"\n[dim]Showing {total_plans} plan{'s' if total_plans != 1 else ''}[/dim]")
            console.print("[dim]Use '/show_plan <id>' to see details[/dim]")

    def execute_plan_cmd(self, args: str):
        """Execute an approved plan"""
        if not args:
            # Show approved plans
            approved_plans = self.plan_generator.list_plans(PlanStatus.APPROVED)
            if not approved_plans:
                console.print("[yellow]No approved plans available for execution[/yellow]")
                return

            console.print("[cyan]Approved plans available for execution:[/cyan]")
            for plan in approved_plans:
                console.print(f"  {plan.id}: {plan.title}")

            args = Prompt.ask("Enter plan ID to execute")

        plan = self.plan_generator.get_plan(args)
        if not plan:
            console.print(f"[red]Plan '{args}' not found[/red]")
            return

        if plan.status != PlanStatus.APPROVED:
            console.print(f"[red]Plan '{args}' is not approved for execution (status: {plan.status.value})[/red]")
            return

        # Show final confirmation
        self.plan_generator.show_plan_details(plan)

        if not Confirm.ask(f"Execute plan '{plan.title}' with {len(plan.actions)} actions?"):
            console.print("[yellow]Plan execution cancelled[/yellow]")
            return

        # Execute the plan using PlanExecutor
        try:
            console.print(f"[yellow]Executing plan '{plan.title}'...[/yellow]")

            # Update plan status to executing
            self.plan_generator.update_plan_status(args, PlanStatus.PENDING)

            # Execute using PlanExecutor
            execution_log = self.plan_executor.execute_plan(plan)

            # Update plan status based on execution result
            from .plan_executor import ExecutionStatus, ActionResult
            if execution_log.status == ExecutionStatus.COMPLETED:
                self.plan_generator.update_plan_status(args, PlanStatus.EXECUTED)
                console.print(f"[green]✓ Plan '{args}' executed successfully![/green]")

                # Show execution summary
                console.print(Panel(
                    f"[bold]Execution Summary[/bold]\n"
                    f"Duration: {execution_log.total_duration:.2f}s\n"
                    f"Actions completed: {len([a for a in execution_log.action_results if a.result == ActionResult.SUCCESS])}\n"
                    f"Actions failed: {len([a for a in execution_log.action_results if a.result == ActionResult.FAILED])}\n"
                    f"Backup created: {execution_log.backup_directory}",
                    title="Execution Complete",
                    border_style="green"
                ))

            else:
                self.plan_generator.update_plan_status(args, PlanStatus.FAILED)
                console.print(f"[red]✗ Plan '{args}' execution failed[/red]")
                console.print(f"[dim]Error: {execution_log.error_message}[/dim]")

                # Offer rollback option
                if execution_log.backup_directory and Confirm.ask("Rollback changes?"):
                    try:
                        self.plan_executor.rollback_execution(execution_log)
                        console.print("[green]Changes rolled back successfully[/green]")
                    except Exception as rollback_error:
                        console.print(f"[red]Rollback failed: {rollback_error}[/red]")

        except Exception as e:
            self.plan_generator.update_plan_status(args, PlanStatus.FAILED)
            console.print(f"[red]Error executing plan: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Tiny Code - AI Coding Assistant"""
    if ctx.invoked_subcommand is None:
        cli_instance = TinyCodeCLI()
        cli_instance.interactive_mode()

@cli.command()
@click.argument('filepath')
@click.option('--operation', '-o', default='explain',
              type=click.Choice(['complete', 'fix', 'explain', 'refactor', 'test', 'review', 'analyze']))
def process(filepath, operation):
    """Process a code file with specified operation"""
    agent = TinyCodeAgent()
    result = agent.process_file(filepath, operation)
    console.print(result)

@cli.command()
@click.argument('filepath')
def run(filepath):
    """Execute a Python file"""
    agent = TinyCodeAgent()
    tools = CodeTools()
    code = tools.read_file(filepath)
    if code:
        agent.execute_code(code)

@cli.command()
@click.argument('message')
def ask(message):
    """Ask Tiny Code a question"""
    agent = TinyCodeAgent()
    response = agent.chat(message)
    console.print(response)